#!/usr/bin/env python3
"""
Veo - AI Video Generation using Google Veo 3.1 on Vertex AI.

By default this uses the **GA Veo 3.1 Fast** model
(`veo-3.1-fast-generate-001`).  Other models are used **only when explicitly
requested**:

  - default -> veo-3.1-fast-generate-001  (GA, fast / balanced cost)
  - --pro   -> veo-3.1-generate-001       (GA, premium / cinematic, 4k)
  - --lite  -> veo-3.1-lite-generate-001  (Preview, cheapest)

Supports text-to-video and image-to-video (first frame + optional last frame).

Vertex AI only: the Veo 3.1 preview models on the Gemini Developer API
(`veo-3.1-*-generate-preview`) were shut down on 2026-10-22, and the Gemini
Developer API no longer serves any Veo model.

Usage:
    python generate.py "a cat surfing a wave, cinematic" -o cat.mp4
    python generate.py "slow zoom over a city at dawn" --ratio 9:16 --duration 6
    python generate.py "animate this photo" -i start.jpg -o anim.mp4
    python generate.py "epic drone shot, 1080p" --pro --resolution 1080p

Environment Variables:
    Vertex AI API (required):
        GOOGLE_CLOUD_PROJECT  - GCP project ID
        GOOGLE_CLOUD_LOCATION - GCP region (default: us-central1; Veo 3.1 is
                                served only in us-central1)

    Optional:
        VEO_MODEL         - Force a specific model (overrides flags)
        VIDEO_OUTPUT_DIR  - Default output directory (default: ./veo-videos)
"""

import argparse
import json
import os
import ssl
import sys
import time
import warnings
from datetime import datetime
from pathlib import Path

try:
    from google import genai
    from google.genai import types
except ImportError:
    print("Error: google-genai package not installed.", file=sys.stderr)
    print("Install with: pip install google-genai", file=sys.stderr)
    sys.exit(1)

# Default is the GA Fast model. Pro / Lite are opt-in only.
MODEL_FAST = "veo-3.1-fast-generate-001"
MODEL_PRO = "veo-3.1-generate-001"
MODEL_LITE = "veo-3.1-lite-generate-001"

VALID_ASPECT_RATIOS = ["16:9", "9:16"]
VALID_RESOLUTIONS = ["720p", "1080p", "4k"]
# "auto" resolves to "allow_adult" (see resolve_person_generation).
VALID_PERSON_GENERATION = ["auto", "dont_allow", "allow_adult", "allow_all"]

_ssl_verification_disabled = False


def disable_ssl_verification() -> None:
    """Disable SSL certificate verification globally.

    Useful for environments behind corporate proxies or with self-signed
    certificates.  Called once when --no-ssl-verify is passed or when the
    VEO_NO_SSL_VERIFY environment variable is set.
    """
    global _ssl_verification_disabled
    if _ssl_verification_disabled:
        return

    # Override the default HTTPS context so that stdlib and libraries that
    # rely on ssl.create_default_context() skip certificate verification.
    ssl._create_default_https_context = ssl._create_unverified_context

    # Suppress noisy warnings about unverified requests.
    warnings.filterwarnings("ignore", message=".*certificate verify failed.*")
    warnings.filterwarnings("ignore", message=".*Unverified HTTPS.*")

    try:
        import urllib3

        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    except ImportError:
        pass

    # Monkey-patch httpx (used internally by google-genai) so that any
    # Client / AsyncClient instances created later default to verify=False.
    try:
        import httpx

        _original_client_init = httpx.Client.__init__

        def _patched_client_init(self, *args, **kwargs):  # type: ignore[no-untyped-def]
            kwargs.setdefault("verify", False)
            _original_client_init(self, *args, **kwargs)

        httpx.Client.__init__ = _patched_client_init  # type: ignore[method-assign]

        _original_async_init = httpx.AsyncClient.__init__

        def _patched_async_init(self, *args, **kwargs):  # type: ignore[no-untyped-def]
            kwargs.setdefault("verify", False)
            _original_async_init(self, *args, **kwargs)

        httpx.AsyncClient.__init__ = _patched_async_init  # type: ignore[method-assign]
    except ImportError:
        pass

    _ssl_verification_disabled = True


def create_client(no_ssl_verify: bool = False) -> genai.Client:
    """Create a Vertex AI GenAI client from environment variables.

    Veo is no longer served by the Gemini Developer API, so GEMINI_API_KEY
    alone is rejected with migration guidance.

    Args:
        no_ssl_verify: If True, disable SSL certificate verification.
    """
    if no_ssl_verify or os.environ.get("VEO_NO_SSL_VERIFY", "").lower() in (
        "1",
        "true",
        "yes",
    ):
        disable_ssl_verification()

    project = os.environ.get("GOOGLE_CLOUD_PROJECT")
    location = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")

    if project:
        return genai.Client(
            vertexai=True,
            project=project,
            location=location,
        )

    if os.environ.get("GEMINI_API_KEY"):
        print(
            "Error: Veo is no longer available on the Gemini Developer API.\n"
            "The veo-3.1-*-generate-preview models were shut down on 2026-10-22.\n"
            "Use Vertex AI instead:\n"
            "  export GOOGLE_CLOUD_PROJECT=\"your-project-id\"\n"
            "  gcloud auth application-default login\n"
            "Or, to keep using GEMINI_API_KEY, use the gemini-omni skill\n"
            "(Gemini Omni Flash), which covers text/image-to-video and more.\n",
            file=sys.stderr,
        )
        sys.exit(1)

    print(
        "Error: No API credentials found.\n"
        "Set GOOGLE_CLOUD_PROJECT (Vertex AI) and configure Application Default\n"
        "Credentials (gcloud auth application-default login).\n",
        file=sys.stderr,
    )
    sys.exit(1)


def select_model(force_pro: bool = False, force_lite: bool = False) -> str:
    """Select the Veo model.

    Defaults to the GA Fast model.  The premium (Pro) and cheapest (Lite)
    models are used only when explicitly requested via flags, or via the
    VEO_MODEL environment variable.
    """
    override = os.environ.get("VEO_MODEL")
    if override:
        return override
    if force_pro:
        return MODEL_PRO
    if force_lite:
        return MODEL_LITE
    return MODEL_FAST


def resolve_person_generation(value: str | None) -> str:
    """Resolve the person_generation policy ("auto" -> "allow_adult")."""
    if value and value != "auto":
        return value
    return "allow_adult"


def load_image(path: str) -> "types.Image":
    """Load an image file into a types.Image."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Image file not found: {path}")

    mime_map = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
    }
    mime_type = mime_map.get(p.suffix.lower(), "image/png")
    return types.Image(image_bytes=p.read_bytes(), mime_type=mime_type)


def generate_output_path(output_dir: str | None = None) -> str:
    """Generate a timestamped output file path."""
    if output_dir is None:
        output_dir = os.environ.get("VIDEO_OUTPUT_DIR", "./veo-videos")

    Path(output_dir).mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return str(Path(output_dir) / f"veo_{ts}.mp4")


def _indexed_path(base: str, index: int, total: int) -> str:
    """Insert an index suffix into a path when generating multiple videos."""
    if total <= 1:
        return base
    p = Path(base)
    return str(p.with_name(f"{p.stem}_{index}{p.suffix or '.mp4'}"))


def generate_video(
    prompt: str,
    output_path: str | None = None,
    image_path: str | None = None,
    last_frame_path: str | None = None,
    aspect_ratio: str = "16:9",
    resolution: str = "720p",
    duration_seconds: int = 8,
    number_of_videos: int = 1,
    person_generation: str = "auto",
    negative_prompt: str | None = None,
    seed: int | None = None,
    force_pro: bool = False,
    force_lite: bool = False,
    poll_interval: float = 10.0,
    timeout: float | None = None,
    verbose: bool = False,
    no_ssl_verify: bool = False,
) -> dict:
    """Generate video(s) using the Veo API.

    Args:
        prompt:            Text description of the video.
        output_path:       Output .mp4 path (index suffix added if >1 video).
        image_path:        Starting frame image for image-to-video.
        last_frame_path:   Ending frame image (constrains the final frame).
        aspect_ratio:      "16:9" or "9:16".
        resolution:        "720p", "1080p", or "4k" (4k: Pro only).
        duration_seconds:  Clip length in seconds.
        number_of_videos:  Number of videos (1-4).
        person_generation: "auto" / "dont_allow" / "allow_adult" / "allow_all".
                           "auto" resolves to allow_adult.
        negative_prompt:   Optional things to avoid.
        seed:              Optional seed for consistency.
        force_pro:         Use the premium Veo 3.1 model (explicit).
        force_lite:        Use the Veo 3.1 Lite model (explicit).
        poll_interval:     Seconds between polling the operation.
        timeout:           Max seconds to wait (None = no limit).
        verbose:           Print progress information.
        no_ssl_verify:     Disable SSL certificate verification.

    Returns:
        dict with keys: success (bool), paths (list[str]), error (str|None),
        metadata (dict|None).
    """
    client = create_client(no_ssl_verify=no_ssl_verify)
    model = select_model(force_pro=force_pro, force_lite=force_lite)

    if aspect_ratio not in VALID_ASPECT_RATIOS:
        print(
            f"Warning: '{aspect_ratio}' is not a standard ratio. "
            f"Valid: {VALID_ASPECT_RATIOS}",
            file=sys.stderr,
        )
    if resolution not in VALID_RESOLUTIONS:
        print(
            f"Warning: '{resolution}' is not a standard resolution. "
            f"Valid: {VALID_RESOLUTIONS}",
            file=sys.stderr,
        )
    if resolution == "4k" and model in (MODEL_FAST, MODEL_LITE):
        print(
            "Warning: only the premium Veo 3.1 model supports 4k output. "
            "Use --pro for 4k, or choose 720p/1080p.",
            file=sys.stderr,
        )

    person_generation = resolve_person_generation(person_generation)

    base_config_kwargs: dict = {
        "aspect_ratio": aspect_ratio,
        "resolution": resolution,
        "duration_seconds": duration_seconds,
        "number_of_videos": number_of_videos,
    }
    if negative_prompt:
        base_config_kwargs["negative_prompt"] = negative_prompt
    if seed is not None:
        base_config_kwargs["seed"] = seed

    start_image = None
    if image_path:
        start_image = load_image(image_path)
    if last_frame_path:
        base_config_kwargs["last_frame"] = load_image(last_frame_path)

    if verbose:
        print(f"Model: {model}")
        print(f"Prompt: {prompt}")
        print(f"Aspect ratio: {aspect_ratio}, Resolution: {resolution}, "
              f"Duration: {duration_seconds}s, Count: {number_of_videos}")
        print(f"Person generation: {person_generation}")
        if image_path:
            print(f"Start frame: {image_path}")
        if last_frame_path:
            print(f"Last frame: {last_frame_path}")
        print("Submitting generation request...")

    gen_kwargs: dict = {
        "model": model,
        "prompt": prompt,
        "config": types.GenerateVideosConfig(
            person_generation=person_generation, **base_config_kwargs
        ),
    }
    if start_image is not None:
        gen_kwargs["image"] = start_image

    try:
        operation = client.models.generate_videos(**gen_kwargs)

        # Poll the long-running operation until completion.
        waited = 0.0
        while not operation.done:
            if timeout is not None and waited >= timeout:
                return {
                    "success": False,
                    "error": f"Timed out after {timeout}s waiting for video generation.",
                    "paths": [],
                    "metadata": None,
                }
            if verbose:
                print(f"  ...still generating (waited {int(waited)}s)")
            time.sleep(poll_interval)
            waited += poll_interval
            operation = client.operations.get(operation)

        result = getattr(operation, "result", None) or getattr(
            operation, "response", None
        )
        if not result:
            err = getattr(operation, "error", None)
            return {
                "success": False,
                "error": f"Generation failed: {err}" if err else "No result returned.",
                "paths": [],
                "metadata": None,
            }

        generated_videos = getattr(result, "generated_videos", None)
        if not generated_videos:
            return {
                "success": False,
                "error": "No videos were generated (possibly blocked by safety filters).",
                "paths": [],
                "metadata": None,
            }

        base = output_path or generate_output_path()
        Path(base).parent.mkdir(parents=True, exist_ok=True)

        saved_paths: list[str] = []
        total = len(generated_videos)
        for n, gv in enumerate(generated_videos):
            target = _indexed_path(base, n, total)
            client.files.download(file=gv.video)
            gv.video.save(target)
            saved_paths.append(target)
            if verbose:
                print(f"Saved: {target}")

        return {
            "success": True,
            "paths": saved_paths,
            "error": None,
            "metadata": {
                "model": model,
                "prompt": prompt,
                "aspect_ratio": aspect_ratio,
                "resolution": resolution,
                "duration_seconds": duration_seconds,
                "number_of_videos": total,
                "person_generation": person_generation,
                "image": image_path,
                "last_frame": last_frame_path,
                "timestamp": datetime.now().isoformat(),
            },
        }

    except Exception as e:
        msg = str(e)
        if "safety" in msg.lower():
            msg = "Content blocked by safety filters. Try rephrasing your prompt."
        elif "quota" in msg.lower() or "rate" in msg.lower():
            msg = "API rate limit reached. Wait a moment and retry."
        return {
            "success": False,
            "error": msg,
            "paths": [],
            "metadata": None,
        }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate videos using Veo 3.1 on Vertex AI (defaults to the GA Fast model)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Examples:
  %(prog)s "a cat surfing a wave, cinematic" -o cat.mp4
  %(prog)s "slow zoom over a city at dawn" --ratio 9:16 --duration 6
  %(prog)s "animate this photo into a gentle breeze" -i start.jpg -o anim.mp4
  %(prog)s "epic drone shot over mountains" --pro --resolution 1080p

Models (default is GA Fast; Pro/Lite are opt-in only):
  default  veo-3.1-fast-generate-001   (GA, fast / balanced cost)
  --pro    veo-3.1-generate-001        (GA, premium / cinematic, 4k)
  --lite   veo-3.1-lite-generate-001   (Preview, cheapest)
""",
    )

    parser.add_argument("prompt", help="Text prompt for video generation")
    parser.add_argument("-o", "--output", help="Output .mp4 file path")
    parser.add_argument(
        "-i", "--image", help="Starting frame image (image-to-video)",
    )
    parser.add_argument(
        "--last-frame", dest="last_frame", help="Ending frame image (constraint)",
    )
    parser.add_argument(
        "-r", "--ratio", default="16:9", choices=VALID_ASPECT_RATIOS,
        help="Aspect ratio (default: 16:9)",
    )
    parser.add_argument(
        "--resolution", default="720p", choices=VALID_RESOLUTIONS,
        help="Resolution (default: 720p; 4k requires --pro)",
    )
    parser.add_argument(
        "-d", "--duration", type=int, default=8,
        help="Clip duration in seconds (default: 8)",
    )
    parser.add_argument(
        "-n", "--count", type=int, default=1,
        help="Number of videos to generate, 1-4 (default: 1)",
    )
    parser.add_argument(
        "--person-generation", dest="person_generation",
        default="auto", choices=VALID_PERSON_GENERATION,
        help="Person generation policy (default: auto = allow_adult)",
    )
    parser.add_argument("--negative-prompt", dest="negative_prompt", help="Things to avoid")
    parser.add_argument("--seed", type=int, help="Seed for consistency")
    model_group = parser.add_mutually_exclusive_group()
    model_group.add_argument(
        "--pro", action="store_true",
        help=f"Use the premium Veo 3.1 model ({MODEL_PRO})",
    )
    model_group.add_argument(
        "--fast", action="store_true",
        help=f"Use the Veo 3.1 Fast model ({MODEL_FAST}; this is the default)",
    )
    model_group.add_argument(
        "--lite", action="store_true",
        help=f"Use the Veo 3.1 Lite model ({MODEL_LITE}; Preview)",
    )
    parser.add_argument(
        "--poll-interval", type=float, default=10.0,
        help="Seconds between status checks (default: 10)",
    )
    parser.add_argument(
        "--timeout", type=float,
        help="Max seconds to wait for generation (default: no limit)",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Show detailed output")
    parser.add_argument(
        "--json", action="store_true", dest="json_output", help="Output result as JSON",
    )
    parser.add_argument(
        "--no-ssl-verify", action="store_true",
        help="Disable SSL certificate verification (for proxies or self-signed certs)",
    )

    args = parser.parse_args()

    if not (1 <= args.count <= 4):
        print("Error: --count must be between 1 and 4.", file=sys.stderr)
        sys.exit(2)

    result = generate_video(
        prompt=args.prompt,
        output_path=args.output,
        image_path=args.image,
        last_frame_path=args.last_frame,
        aspect_ratio=args.ratio,
        resolution=args.resolution,
        duration_seconds=args.duration,
        number_of_videos=args.count,
        person_generation=args.person_generation,
        negative_prompt=args.negative_prompt,
        seed=args.seed,
        force_pro=args.pro,
        force_lite=args.lite,
        poll_interval=args.poll_interval,
        timeout=args.timeout,
        verbose=args.verbose or (args.output is None and not args.json_output),
        no_ssl_verify=args.no_ssl_verify,
    )

    if args.json_output:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif result["success"]:
        for p in result["paths"]:
            print(p)
    else:
        print(f"Error: {result['error']}", file=sys.stderr)

    sys.exit(0 if result["success"] else 1)


if __name__ == "__main__":
    main()
