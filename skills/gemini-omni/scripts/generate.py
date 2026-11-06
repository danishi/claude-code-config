#!/usr/bin/env python3
"""
Gemini Omni - multimodal video generation & conversational editing
using Google Gemini Omni Flash (gemini-omni-1.1-flash) via the Interactions API.

One model covers every mode; the mode is inferred from the inputs:

  - text only                       -> text-to-video
  - 1 image + text                  -> image-to-video
  - 2 images + "first/last" prompt  -> first/last frame interpolation
  - images as subjects              -> subject reference
  - --video FILE + text             -> edit / extend an uploaded video
  - --previous ID + text            -> multi-turn edit / extend of a generated video

Every run writes a sidecar JSON (<output>.json) holding the interaction ID, so
the next turn can pass `--previous <output>.mp4` to keep editing.

Usage:
    python generate.py "A marble rolling on a chain reaction track" -o marble.mp4
    python generate.py "Bring this drawing to life" -i drawing.png -o anim.mp4
    python generate.py "Make the violin invisible" --previous marble.mp4 -o edit.mp4
    python generate.py "Continue the scene" --video clip.mp4 -o extended.mp4

Environment Variables:
    Gemini Developer API:
        GEMINI_API_KEY - API key from https://aistudio.google.com/apikey
    Vertex AI API:
        GOOGLE_CLOUD_PROJECT  - GCP project ID
        GOOGLE_CLOUD_LOCATION - GCP region (default: global)
    Common:
        OMNI_MODEL          - Force a specific model ID
        OMNI_OUTPUT_DIR     - Default output directory (default: ./gemini-omni)
        OMNI_NO_SSL_VERIFY  - 1/true/yes to disable SSL verification
"""

import argparse
import base64
import json
import mimetypes
import os
import ssl
import sys
import time
import warnings
from datetime import datetime
from pathlib import Path

try:
    from google import genai
except ImportError:
    print("Error: google-genai package not installed.", file=sys.stderr)
    print("Install with: pip install -U google-genai", file=sys.stderr)
    sys.exit(1)

MODEL_GEMINI_API = "gemini-omni-1.1-flash"
MODEL_VERTEX = "gemini-omni-1.1-flash-preview"

VALID_RATIOS = ["16:9", "9:16"]
VALID_RESOLUTIONS = ["360p", "720p", "1080p", "4k"]
VALID_TASKS = ["text_to_video", "image_to_video", "reference_to_video", "edit", "extend"]
# Inline payloads above ~4MB fail; these resolutions switch to URI delivery.
URI_RESOLUTIONS = {"1080p", "4k"}

IMAGE_MIME = {
    ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png",
    ".webp": "image/webp", ".heic": "image/heic", ".heif": "image/heif",
}

_ssl_verification_disabled = False


def disable_ssl_verification() -> None:
    """Disable SSL certificate verification globally (corporate proxies etc.)."""
    global _ssl_verification_disabled
    if _ssl_verification_disabled:
        return
    ssl._create_default_https_context = ssl._create_unverified_context
    warnings.filterwarnings("ignore", message=".*certificate verify failed.*")
    warnings.filterwarnings("ignore", message=".*Unverified HTTPS.*")
    try:
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    except ImportError:
        pass
    try:
        import httpx

        _orig = httpx.Client.__init__

        def _patched(self, *a, **kw):  # type: ignore[no-untyped-def]
            kw.setdefault("verify", False)
            _orig(self, *a, **kw)

        httpx.Client.__init__ = _patched  # type: ignore[method-assign]

        _orig_async = httpx.AsyncClient.__init__

        def _patched_async(self, *a, **kw):  # type: ignore[no-untyped-def]
            kw.setdefault("verify", False)
            _orig_async(self, *a, **kw)

        httpx.AsyncClient.__init__ = _patched_async  # type: ignore[method-assign]
    except ImportError:
        pass
    _ssl_verification_disabled = True


def _is_vertex() -> bool:
    return bool(os.environ.get("GOOGLE_CLOUD_PROJECT"))


def create_client(no_ssl_verify: bool = False) -> "genai.Client":
    """Vertex AI if GOOGLE_CLOUD_PROJECT is set, else Gemini Developer API."""
    if no_ssl_verify or os.environ.get("OMNI_NO_SSL_VERIFY", "").lower() in ("1", "true", "yes"):
        disable_ssl_verification()

    if _is_vertex():
        return genai.Client(
            vertexai=True,
            project=os.environ["GOOGLE_CLOUD_PROJECT"],
            location=os.environ.get("GOOGLE_CLOUD_LOCATION", "global"),
        )
    api_key = os.environ.get("GEMINI_API_KEY")
    if api_key:
        return genai.Client(api_key=api_key)

    print(
        "Error: No API credentials found.\n"
        "Set one of:\n"
        "  GEMINI_API_KEY        - for Gemini Developer API\n"
        "  GOOGLE_CLOUD_PROJECT  - for Vertex AI API\n",
        file=sys.stderr,
    )
    sys.exit(1)


def select_model() -> str:
    return os.environ.get("OMNI_MODEL") or (MODEL_VERTEX if _is_vertex() else MODEL_GEMINI_API)


def image_part(path: str) -> dict:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Image file not found: {path}")
    mime = IMAGE_MIME.get(p.suffix.lower(), "image/png")
    return {"type": "image", "data": base64.b64encode(p.read_bytes()).decode(), "mime_type": mime}


def upload_video(client, path: str, verbose: bool) -> dict:
    """Upload a video via the Files API and wait until it is ACTIVE."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Video file not found: {path}")
    if verbose:
        print(f"Uploading video: {path}")
    f = client.files.upload(file=str(p))
    while _state(f) == "PROCESSING":
        if verbose:
            print("  ...video processing")
        time.sleep(5)
        f = client.files.get(name=f.name)
    if _state(f) == "FAILED":
        raise RuntimeError(f"Video upload processing failed: {path}")
    mime = f.mime_type or mimetypes.guess_type(str(p))[0] or "video/mp4"
    return {"type": "video", "uri": f.uri, "mime_type": mime}


def _state(f) -> str:
    s = getattr(f, "state", None)
    return getattr(s, "name", None) or str(s or "")


def resolve_previous_id(value: str | None) -> str | None:
    """Accept an interaction ID, a sidecar .json, or a generated .mp4 (its sidecar is read)."""
    if not value:
        return None
    p = Path(value)
    candidates = []
    if p.suffix.lower() == ".json":
        candidates.append(p)
    elif p.suffix:
        candidates.append(p.with_suffix(p.suffix + ".json"))
        candidates.append(p.with_suffix(".json"))
    for c in candidates:
        if c.exists():
            data = json.loads(c.read_text())
            iid = data.get("interaction_id") or (data.get("metadata") or {}).get("interaction_id")
            if iid:
                return iid
            raise ValueError(f"No interaction_id in sidecar: {c}")
    if p.suffix:
        raise FileNotFoundError(
            f"No sidecar JSON found for {value} (expected {value}.json). "
            "Pass the interaction ID directly instead."
        )
    return value


def default_output_path() -> str:
    out_dir = Path(os.environ.get("OMNI_OUTPUT_DIR", "./gemini-omni"))
    out_dir.mkdir(parents=True, exist_ok=True)
    return str(out_dir / f"omni_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4")


def save_video(client, video, target: str, verbose: bool) -> None:
    data = getattr(video, "data", None)
    uri = getattr(video, "uri", None)
    if data:
        raw = data if isinstance(data, (bytes, bytearray)) else base64.b64decode(data)
        Path(target).write_bytes(raw)
        return
    if not uri:
        raise RuntimeError("Video output had neither inline data nor a URI.")
    if uri.startswith("gs://"):
        raise RuntimeError(f"Video was written to Cloud Storage: {uri} (download it with gcloud storage cp)")
    file_id = uri.rstrip("/").split("/")[-1].split(":")[0]
    if verbose:
        print("Waiting for the video file to become ACTIVE...")
    for _ in range(360):
        info = client.files.get(name=f"files/{file_id}")
        st = _state(info)
        if st == "ACTIVE":
            break
        if st == "FAILED":
            raise RuntimeError("Video file processing failed.")
        time.sleep(5)
    client.files.download(file=uri, destination=target)


def _get_with_retry(client, interaction, verbose: bool, attempts: int = 5):
    """Poll once, tolerating transient network errors / timeouts.

    The GET response carries the finished video inline (base64, several MB),
    so a single slow read must not abort a generation that already succeeded.
    """
    for n in range(1, attempts + 1):
        try:
            return client.interactions.get(id=interaction.id, timeout=300)
        except Exception as e:  # noqa: BLE001
            if n == attempts:
                raise
            if verbose:
                print(f"  poll failed ({type(e).__name__}); retry {n}/{attempts - 1}")
            time.sleep(min(5 * n, 30))
    return interaction


def generate(
    prompt: str,
    output_path: str | None = None,
    images: list[str] | None = None,
    video: str | None = None,
    previous: str | None = None,
    aspect_ratio: str | None = None,
    resolution: str | None = None,
    duration: str | None = None,
    task: str | None = None,
    delivery: str | None = None,
    gcs_uri: str | None = None,
    no_store: bool = False,
    poll_interval: float = 10.0,
    timeout: float | None = None,
    sync_timeout: float = 1800.0,
    verbose: bool = False,
    no_ssl_verify: bool = False,
) -> dict:
    client = create_client(no_ssl_verify=no_ssl_verify)
    model = select_model()
    images = images or []

    try:
        previous_id = resolve_previous_id(previous)

        parts: list[dict] = []
        if video:
            parts.append(upload_video(client, video, verbose))
        parts.extend(image_part(i) for i in images)
        request_input: object = prompt if not parts else parts + [{"type": "text", "text": prompt}]

        fmt: dict = {"type": "video"}
        if aspect_ratio:
            fmt["aspect_ratio"] = aspect_ratio
        if resolution:
            fmt["resolution"] = resolution
        if duration:
            fmt["duration"] = duration
        if delivery is None:
            if gcs_uri:
                delivery = "uri"
            elif resolution in URI_RESOLUTIONS and not _is_vertex():
                delivery = "uri"
        if delivery:
            fmt["delivery"] = delivery
        if gcs_uri:
            fmt["gcs_uri"] = gcs_uri

        kwargs: dict = {"model": model, "input": request_input, "response_format": fmt}
        if previous_id:
            kwargs["previous_interaction_id"] = previous_id
        if task:
            kwargs["generation_config"] = {"video_config": {"task": task}}
        if no_store:
            kwargs["store"] = False

        if verbose:
            print(f"Model: {model}")
            print(f"Prompt: {prompt}")
            if images:
                print(f"Images: {', '.join(images)}")
            if video:
                print(f"Video: {video}")
            if previous_id:
                print(f"Previous interaction: {previous_id}")
            print(f"Response format: {fmt}")
            if task:
                print(f"Task: {task}")
            print("Generating (this can take a few minutes)...")

        started = time.time()
        if no_store:
            # Background mode needs a stored interaction; fall back to a long sync call.
            interaction = client.interactions.create(**kwargs, timeout=sync_timeout)
        else:
            # Generation takes minutes, longer than the default HTTP timeout:
            # submit in the background and poll until it finishes.
            interaction = client.interactions.create(**kwargs, background=True)
            if verbose:
                print(f"Interaction ID: {interaction.id}")
            while getattr(interaction, "status", None) in ("in_progress", "queued"):
                waited = time.time() - started
                if timeout is not None and waited >= timeout:
                    return {
                        "success": False,
                        "error": f"Timed out after {int(waited)}s. Resume later with: "
                        f"client.interactions.get(id='{interaction.id}')",
                        "path": None,
                        "interaction_id": interaction.id,
                        "metadata": None,
                    }
                if verbose:
                    print(f"  ...{interaction.status} ({int(waited)}s)")
                time.sleep(poll_interval)
                interaction = _get_with_retry(client, interaction, verbose)
        elapsed = round(time.time() - started, 1)

        status = getattr(interaction, "status", None)
        if status not in (None, "completed"):
            return {
                "success": False,
                "error": f"Interaction ended with status '{status}'."
                + (f" Model said: {interaction.output_text}" if getattr(interaction, "output_text", None) else ""),
                "path": None,
                "interaction_id": interaction.id,
                "metadata": None,
            }

        out_video = getattr(interaction, "output_video", None)
        text = getattr(interaction, "output_text", None) or ""
        if out_video is None:
            return {
                "success": False,
                "error": "No video returned (possibly blocked by safety filters)."
                + (f" Model said: {text}" if text else ""),
                "path": None,
                "interaction_id": getattr(interaction, "id", None),
                "metadata": None,
            }

        target = output_path or default_output_path()
        Path(target).parent.mkdir(parents=True, exist_ok=True)
        save_video(client, out_video, target, verbose)

        metadata = {
            "model": model,
            "prompt": prompt,
            "images": images,
            "video": video,
            "previous_interaction_id": previous_id,
            "response_format": fmt,
            "task": task,
            "stored": not no_store,
            "model_text": text,
            "elapsed_seconds": elapsed,
            "timestamp": datetime.now().isoformat(),
        }
        sidecar = target + ".json"
        Path(sidecar).write_text(
            json.dumps({"interaction_id": interaction.id, "metadata": metadata}, ensure_ascii=False, indent=2)
        )
        if verbose:
            print(f"Saved: {target}  ({elapsed}s)")
            print(f"Interaction ID: {interaction.id}  (sidecar: {sidecar})")
            if text:
                print(f"Model text: {text}")

        return {
            "success": True,
            "path": target,
            "interaction_id": interaction.id,
            "error": None,
            "metadata": metadata,
        }

    except KeyboardInterrupt:
        raise
    except BaseException as e:  # noqa: BLE001
        if verbose:
            import traceback
            traceback.print_exc()
        msg = f"{type(e).__name__}: {e}"
        low = msg.lower()
        if "safety" in low or "blocked" in low:
            msg = f"Content blocked by safety filters. Try rephrasing. ({msg})"
        elif "quota" in low or "429" in low or "rate limit" in low:
            msg = f"API rate limit / quota reached. Wait and retry. ({msg})"
        return {"success": False, "error": msg, "path": None, "interaction_id": None, "metadata": None}


def main() -> None:
    # Line-buffer output so progress (incl. the interaction ID for recovery)
    # is not lost if the process dies while piped.
    try:
        sys.stdout.reconfigure(line_buffering=True)  # type: ignore[attr-defined]
    except AttributeError:
        pass
    parser = argparse.ArgumentParser(
        description="Generate / edit / extend videos with Gemini Omni Flash (Interactions API)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Examples:
  %(prog)s "A marble rolling on a chain reaction track, continuous shot" -o marble.mp4
  %(prog)s "Turn this drawing into realistic footage" -i fish.png -o fish.mp4
  %(prog)s "Smooth transition from the first image to the second" -i a.jpg -i b.jpg -o morph.mp4
  %(prog)s "Make this video anime. Keep everything else the same." --previous marble.mp4 -o anime.mp4
  %(prog)s "Extend this video: the camera pans up to the sky" --previous marble.mp4 -o ext.mp4
  %(prog)s "Make the mirror ripple like liquid" --video my_clip.mp4 -o edit.mp4
""",
    )
    parser.add_argument("prompt", nargs="?", help="Text prompt (or use -f)")
    parser.add_argument("-f", "--file", help="Read the prompt from a text file")
    parser.add_argument("-o", "--output", help="Output .mp4 path (sidecar <output>.json is written too)")
    parser.add_argument("-i", "--image", action="append", default=[],
                        help="Input image (repeatable, up to 10): start frame, first/last frame, or subject reference")
    parser.add_argument("--video", help="Input video to edit or extend (uploaded via Files API, <=10s)")
    parser.add_argument("-p", "--previous",
                        help="Continue from a previous turn: interaction ID, a generated .mp4 (reads its sidecar), or the sidecar .json")
    parser.add_argument("-r", "--ratio", choices=VALID_RATIOS, help="Aspect ratio (default: 16:9)")
    parser.add_argument("--resolution", choices=VALID_RESOLUTIONS, help="Output resolution (default: 720p; 1080p/4k are upscaled)")
    parser.add_argument("-d", "--duration", help="Requested duration, e.g. '8s' (not covered by the official guide; may be ignored)")
    parser.add_argument("--task", choices=VALID_TASKS, help="Force the generation mode (fallback only; prompt first)")
    parser.add_argument("--delivery", choices=["inline", "uri"], help="Output delivery (auto: uri for 1080p/4k)")
    parser.add_argument("--gcs-uri", help="Vertex AI: gs:// destination for URI delivery")
    parser.add_argument("--no-store", action="store_true",
                        help="store=false: slightly faster, but the result cannot be edited in later turns")
    parser.add_argument("--poll-interval", type=float, default=10.0, help="Seconds between status checks (default: 10)")
    parser.add_argument("--timeout", type=float, help="Max seconds to wait (default: no limit)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Show detailed output")
    parser.add_argument("--json", action="store_true", dest="json_output", help="Output result as JSON")
    parser.add_argument("--no-ssl-verify", action="store_true", help="Disable SSL certificate verification")
    args = parser.parse_args()

    if args.file:
        prompt = Path(args.file).read_text().strip()
    elif args.prompt:
        prompt = args.prompt
    else:
        parser.error("a prompt (positional) or -f FILE is required")
    if len(args.image) > 10:
        parser.error("at most 10 images per prompt")

    result = generate(
        prompt=prompt,
        output_path=args.output,
        images=args.image,
        video=args.video,
        previous=args.previous,
        aspect_ratio=args.ratio,
        resolution=args.resolution,
        duration=args.duration,
        task=args.task,
        delivery=args.delivery,
        gcs_uri=args.gcs_uri,
        no_store=args.no_store,
        poll_interval=args.poll_interval,
        timeout=args.timeout,
        verbose=args.verbose or (args.output is None and not args.json_output),
        no_ssl_verify=args.no_ssl_verify,
    )

    if args.json_output:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif result["success"]:
        print(result["path"])
    else:
        print(f"Error: {result['error']}", file=sys.stderr)
    sys.exit(0 if result["success"] else 1)


if __name__ == "__main__":
    main()
