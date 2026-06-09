#!/usr/bin/env python3
"""
Lyria - AI Music Generation using Google Gemini (Lyria 3).

Automatically selects the best model based on the request / purpose:
  - Lyria 3 Pro   (lyria-3-pro-preview)  : full-length songs, lyrics,
                                            song structure, premium quality
  - Lyria 3 Clip  (lyria-3-clip-preview) : 30-second clips, loops, jingles,
                                            quick previews / prompt iteration

Supports both Gemini Developer API and Vertex AI API platforms.

Usage:
    python generate.py "lofi hip hop, mellow piano, rainy night" -o track.mp3
    python generate.py "upbeat synthwave, driving bass, 80s" --clip -o clip.mp3
    python generate.py "[Verse] ... [Chorus] ... full pop ballad" --pro -o song.mp3

Environment Variables:
    Gemini Developer API:
        GEMINI_API_KEY - API key from https://aistudio.google.com/apikey

    Vertex AI API:
        GOOGLE_CLOUD_PROJECT  - GCP project ID
        GOOGLE_CLOUD_LOCATION - GCP region (default: us-central1)

    Common:
        LYRIA_MODEL       - Force a specific model (overrides auto-selection)
        AUDIO_OUTPUT_DIR  - Default output directory (default: ./lyria-music)
"""

import argparse
import json
import mimetypes
import os
import ssl
import sys
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

MODEL_PRO = "lyria-3-pro-preview"
MODEL_CLIP = "lyria-3-clip-preview"

# Thresholds for auto-selecting Lyria 3 Pro (full song vs short clip)
_COMPLEXITY_PROMPT_LENGTH = 100

# Keywords in the prompt that indicate a full-length / premium song -> Pro
_PRO_KEYWORDS = [
    "フル", "フルサイズ", "フル尺", "長尺", "1曲", "一曲", "楽曲", "歌詞",
    "高品質", "高音質", "プロ", "完成",
    "full", "full-length", "full length", "complete song", "verse",
    "chorus", "bridge", "lyrics", "professional", "studio",
]

# Keywords that indicate a short clip / loop / preview -> Clip
_CLIP_KEYWORDS = [
    "クリップ", "短い", "短尺", "ループ", "ジングル", "サウンドロゴ",
    "プレビュー", "試し", "30秒", "30 秒", "効果音", "スニペット",
    "clip", "loop", "jingle", "snippet", "preview", "short", "30 second",
    "30-second", "sound effect", "sfx",
]

_ssl_verification_disabled = False


def disable_ssl_verification() -> None:
    """Disable SSL certificate verification globally.

    Useful for environments behind corporate proxies or with self-signed
    certificates.  Called once when --no-ssl-verify is passed or when the
    LYRIA_NO_SSL_VERIFY environment variable is set.
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
    """Create a GenAI client based on available environment variables.

    Priority:
        1. Vertex AI (if GOOGLE_CLOUD_PROJECT is set)
        2. Gemini Developer API (if GEMINI_API_KEY is set)

    Args:
        no_ssl_verify: If True, disable SSL certificate verification.
    """
    if no_ssl_verify or os.environ.get("LYRIA_NO_SSL_VERIFY", "").lower() in (
        "1",
        "true",
        "yes",
    ):
        disable_ssl_verification()

    project = os.environ.get("GOOGLE_CLOUD_PROJECT")
    location = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
    api_key = os.environ.get("GEMINI_API_KEY")

    if project:
        return genai.Client(
            vertexai=True,
            project=project,
            location=location,
        )

    if api_key:
        return genai.Client(api_key=api_key)

    print(
        "Error: No API credentials found.\n"
        "Set one of:\n"
        "  GEMINI_API_KEY           - for Gemini Developer API\n"
        "  GOOGLE_CLOUD_PROJECT     - for Vertex AI API\n",
        file=sys.stderr,
    )
    sys.exit(1)


def select_model(
    prompt: str,
    force_pro: bool = False,
    force_clip: bool = False,
) -> str:
    """Select the best Lyria model based on the request / purpose.

    Returns Lyria 3 Pro for full-length / structured / premium songs and
    Lyria 3 Clip for short clips, loops, jingles, and quick previews.
    The LYRIA_MODEL env var overrides auto-selection.

    Selection criteria:
      - ``force_pro`` (--pro)  -> always Pro
      - ``force_clip`` (--clip) -> always Clip
      - Prompt contains clip keywords (e.g. "ループ", "jingle", "30 second")
      - Prompt contains pro keywords (e.g. "歌詞", "full-length", "[Verse]")
      - Prompt longer than 100 characters -> Pro
      - Default -> Clip (fast, cheap, good for iteration)
    """
    override = os.environ.get("LYRIA_MODEL")
    if override:
        return override

    if force_pro:
        return MODEL_PRO
    if force_clip:
        return MODEL_CLIP

    prompt_lower = prompt.lower()

    # Explicit clip intent wins over length-based heuristics.
    if any(kw in prompt_lower for kw in _CLIP_KEYWORDS):
        return MODEL_CLIP

    is_full_song = (
        len(prompt) >= _COMPLEXITY_PROMPT_LENGTH
        or any(kw in prompt_lower for kw in _PRO_KEYWORDS)
    )

    return MODEL_PRO if is_full_song else MODEL_CLIP


def generate_output_path(output_dir: str | None = None, ext: str = ".mp3") -> str:
    """Generate a timestamped output file path."""
    if output_dir is None:
        output_dir = os.environ.get("AUDIO_OUTPUT_DIR", "./lyria-music")

    Path(output_dir).mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return str(Path(output_dir) / f"lyria_{ts}{ext}")


def generate_music(
    prompt: str,
    output_path: str | None = None,
    force_pro: bool = False,
    force_clip: bool = False,
    wav: bool = False,
    verbose: bool = False,
    no_ssl_verify: bool = False,
) -> dict:
    """Generate music using the Lyria 3 API.

    Args:
        prompt:         Text description of the music (genre, mood, instruments,
                        structure tags, lyrics, etc.).
        output_path:    Where to save the generated audio.
        force_pro:      Force Lyria 3 Pro model.
        force_clip:     Force Lyria 3 Clip model.
        wav:            Request WAV output (Pro only; Clip is MP3).
        verbose:        Print progress information.
        no_ssl_verify:  Disable SSL certificate verification.

    Returns:
        dict with keys: success (bool), path (str|None),
        text (str|None), error (str|None), metadata (dict|None).
    """
    client = create_client(no_ssl_verify=no_ssl_verify)
    model = select_model(prompt=prompt, force_pro=force_pro, force_clip=force_clip)

    contents = [
        types.Content(
            role="user",
            parts=[types.Part.from_text(text=prompt)],
        ),
    ]

    config_kwargs: dict = {"response_modalities": ["AUDIO"]}
    # WAV output is only supported by the Pro model; ignored otherwise.
    if wav and model == MODEL_PRO:
        try:
            config_kwargs["response_format"] = {"audio": {"mime_type": "audio/wav"}}
        except Exception:
            pass

    generate_config = types.GenerateContentConfig(**config_kwargs)

    if verbose:
        print(f"Model: {model}")
        print(f"Prompt: {prompt}")
        if wav and model == MODEL_PRO:
            print("Output format: WAV")
        print("Generating music...")

    try:
        audio_chunks: list[bytes] = []
        mime_type: str | None = None
        text_response: str | None = None

        for chunk in client.models.generate_content_stream(
            model=model,
            contents=contents,
            config=generate_config,
        ):
            if chunk.parts is None:
                continue
            for part in chunk.parts:
                if part.inline_data and part.inline_data.data:
                    audio_chunks.append(part.inline_data.data)
                    if mime_type is None:
                        mime_type = part.inline_data.mime_type
                elif getattr(part, "text", None):
                    text_response = (text_response or "") + part.text

        if not audio_chunks:
            return {
                "success": False,
                "error": text_response
                or "No audio returned. The prompt may have been blocked by safety filters.",
                "path": None,
                "text": text_response,
                "metadata": None,
            }

        ext = mimetypes.guess_extension(mime_type) if mime_type else None
        if not ext:
            ext = ".mp3"

        if output_path is None:
            output_path = generate_output_path(ext=ext)
        else:
            # Honor caller-supplied path; ensure parent dir exists.
            output_path = str(output_path)
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "wb") as f:
            for buf in audio_chunks:
                f.write(buf)

        if verbose:
            print(f"Saved: {output_path}")
            if text_response:
                print(f"Model note / lyrics: {text_response}")

        return {
            "success": True,
            "path": output_path,
            "text": text_response,
            "error": None,
            "metadata": {
                "model": model,
                "prompt": prompt,
                "mime_type": mime_type,
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
            "path": None,
            "text": None,
            "metadata": None,
        }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate music using Lyria 3 (auto-selects Pro or Clip based on the request)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Examples:
  %(prog)s "lofi hip hop, mellow piano, rainy night" -o track.mp3
  %(prog)s "upbeat synthwave jingle, 80s, short loop" --clip -o jingle.mp3
  %(prog)s "[Verse] city lights fade [Chorus] ... full pop ballad" --pro -o song.mp3
  %(prog)s "epic orchestral cinematic, full-length" --pro --wav -o cinematic.wav
""",
    )

    parser.add_argument("prompt", help="Text prompt describing the music")
    parser.add_argument("-o", "--output", help="Output file path")
    parser.add_argument(
        "--pro", action="store_true",
        help="Force Lyria 3 Pro (full-length songs)",
    )
    parser.add_argument(
        "--clip", action="store_true",
        help="Force Lyria 3 Clip (30s clips, loops, jingles)",
    )
    parser.add_argument(
        "--wav", action="store_true",
        help="Request WAV output (Pro only; Clip outputs MP3)",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true",
        help="Show detailed output",
    )
    parser.add_argument(
        "--json", action="store_true", dest="json_output",
        help="Output result as JSON",
    )
    parser.add_argument(
        "--no-ssl-verify", action="store_true",
        help="Disable SSL certificate verification (for proxies or self-signed certs)",
    )

    args = parser.parse_args()

    if args.pro and args.clip:
        print("Error: --pro and --clip are mutually exclusive.", file=sys.stderr)
        sys.exit(2)

    result = generate_music(
        prompt=args.prompt,
        output_path=args.output,
        force_pro=args.pro,
        force_clip=args.clip,
        wav=args.wav,
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
