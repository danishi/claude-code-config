#!/usr/bin/env python3
"""
Nano Banana - AI Image Generation using Google Gemini 3 Pro Image

Supports both Gemini Developer API and Vertex AI API platforms.

Usage:
    python generate.py "a cute robot" -o robot.png
    python generate.py "make it blue" -i input.jpg -o output.png
    python generate.py "landscape" --ratio 16:9 --size 4K -o landscape.png

Environment Variables:
    Gemini Developer API:
        GEMINI_API_KEY - API key from https://aistudio.google.com/apikey

    Vertex AI API:
        GOOGLE_CLOUD_PROJECT  - GCP project ID
        GOOGLE_CLOUD_LOCATION - GCP region (default: us-central1)

    Common:
        NANOBANANA_MODEL      - Model name (default: gemini-3-pro-image-preview)
        IMAGE_OUTPUT_DIR      - Default output directory (default: ./nanobanana-images)
"""

import argparse
import json
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
    print("Install with: pip install google-genai Pillow", file=sys.stderr)
    sys.exit(1)

DEFAULT_MODEL = "gemini-3-pro-image-preview"

_ssl_verification_disabled = False


def disable_ssl_verification() -> None:
    """Disable SSL certificate verification globally.

    Useful for environments behind corporate proxies or with self-signed
    certificates.  Called once when --no-ssl-verify is passed or when the
    NANOBANANA_NO_SSL_VERIFY environment variable is set.
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

VALID_ASPECT_RATIOS = [
    "1:1", "2:3", "3:2", "3:4", "4:3",
    "4:5", "5:4", "9:16", "16:9", "21:9",
]

VALID_SIZES = ["1K", "2K", "4K"]


def create_client(no_ssl_verify: bool = False) -> genai.Client:
    """Create a GenAI client based on available environment variables.

    Priority:
        1. Vertex AI (if GOOGLE_CLOUD_PROJECT is set)
        2. Gemini Developer API (if GEMINI_API_KEY is set)

    Args:
        no_ssl_verify: If True, disable SSL certificate verification.
    """
    if no_ssl_verify or os.environ.get("NANOBANANA_NO_SSL_VERIFY", "").lower() in (
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


def get_model_name() -> str:
    """Return the model name from env or default."""
    return os.environ.get("NANOBANANA_MODEL", DEFAULT_MODEL)


def load_image_bytes(path: str) -> tuple[bytes, str]:
    """Load an image file and return raw bytes and MIME type."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Image file not found: {path}")

    mime_map = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
        ".gif": "image/gif",
    }
    mime_type = mime_map.get(p.suffix.lower(), "image/png")

    return p.read_bytes(), mime_type


def generate_output_path(output_dir: str | None = None) -> str:
    """Generate a timestamped output file path."""
    if output_dir is None:
        output_dir = os.environ.get("IMAGE_OUTPUT_DIR", "./nanobanana-images")

    Path(output_dir).mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return str(Path(output_dir) / f"nanobanana_{ts}.png")


def generate_image(
    prompt: str,
    output_path: str | None = None,
    input_paths: list[str] | None = None,
    aspect_ratio: str | None = None,
    image_size: str | None = None,
    use_search: bool = False,
    verbose: bool = False,
    no_ssl_verify: bool = False,
) -> dict:
    """Generate or edit an image using Gemini API.

    Args:
        prompt:         Text description or editing instruction.
        output_path:    Where to save the generated image.
        input_paths:    Input image path(s) for editing (up to 14 images).
        aspect_ratio:   Aspect ratio (e.g. "1:1", "16:9").
        image_size:     Resolution: "1K", "2K", or "4K".
        use_search:     Enable Google Search grounding.
        verbose:        Print progress information.
        no_ssl_verify:  Disable SSL certificate verification.

    Returns:
        dict with keys: success (bool), path (str|None),
        text (str|None), error (str|None), metadata (dict|None).
    """
    client = create_client(no_ssl_verify=no_ssl_verify)
    model = get_model_name()

    if output_path is None:
        output_path = generate_output_path()

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    # Build contents
    contents: list = []

    if input_paths:
        for img_path in input_paths:
            img_bytes, mime_type = load_image_bytes(img_path)
            contents.append(
                types.Part.from_bytes(data=img_bytes, mime_type=mime_type)
            )
            if verbose:
                print(f"Input image: {img_path}")

    contents.append(prompt)

    # Build image config
    image_config_kwargs = {}
    if aspect_ratio:
        if aspect_ratio not in VALID_ASPECT_RATIOS:
            print(
                f"Warning: '{aspect_ratio}' is not a standard ratio. "
                f"Valid: {VALID_ASPECT_RATIOS}",
                file=sys.stderr,
            )
        image_config_kwargs["aspect_ratio"] = aspect_ratio
    if image_size:
        size_upper = image_size.upper()
        if size_upper not in VALID_SIZES:
            print(
                f"Warning: '{image_size}' is not a valid size. "
                f"Valid: {VALID_SIZES}",
                file=sys.stderr,
            )
        image_config_kwargs["image_size"] = size_upper

    # Build generation config
    config_kwargs: dict = {
        "response_modalities": ["IMAGE", "TEXT"],
    }
    if image_config_kwargs:
        config_kwargs["image_config"] = types.ImageConfig(**image_config_kwargs)
    if use_search:
        config_kwargs["tools"] = [{"google_search": {}}]

    generate_config = types.GenerateContentConfig(**config_kwargs)

    if verbose:
        print(f"Model: {model}")
        print(f"Prompt: {prompt}")
        if aspect_ratio:
            print(f"Aspect ratio: {aspect_ratio}")
        if image_size:
            print(f"Size: {image_size}")
        if use_search:
            print("Google Search grounding: enabled")
        print("Generating...")

    try:
        response = client.models.generate_content(
            model=model,
            contents=contents,
            config=generate_config,
        )

        image_saved = False
        text_response = None

        if not response.candidates or not response.candidates[0].content.parts:
            return {
                "success": False,
                "error": "No candidates returned. The prompt may have been blocked by safety filters.",
                "path": None,
                "text": None,
                "metadata": None,
            }

        for part in response.candidates[0].content.parts:
            if (
                part.inline_data
                and part.inline_data.mime_type
                and part.inline_data.mime_type.startswith("image/")
            ):
                with open(output_path, "wb") as f:
                    f.write(part.inline_data.data)
                image_saved = True
            elif part.text:
                text_response = part.text

        if not image_saved:
            return {
                "success": False,
                "error": text_response or "No image generated by the model.",
                "path": None,
                "text": text_response,
                "metadata": None,
            }

        if verbose:
            print(f"Saved: {output_path}")
            if text_response:
                print(f"Model note: {text_response}")

        return {
            "success": True,
            "path": output_path,
            "text": text_response,
            "error": None,
            "metadata": {
                "model": model,
                "prompt": prompt,
                "aspect_ratio": aspect_ratio,
                "image_size": image_size,
                "input_images": input_paths,
                "search_grounding": use_search,
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
        description="Generate images using Nano Banana Pro (Gemini 3 Pro Image)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Examples:
  %(prog)s "a cute robot mascot" -o robot.png
  %(prog)s "make the sky purple" -i photo.jpg -o edited.png
  %(prog)s "cinematic landscape" --ratio 21:9 --size 4K -o landscape.png
  %(prog)s "photo of Tokyo Tower" --search -o tokyo.png
  %(prog)s "group photo" -i person1.png -i person2.png -o group.png
""",
    )

    parser.add_argument("prompt", help="Text prompt for image generation")
    parser.add_argument("-o", "--output", help="Output file path")
    parser.add_argument(
        "-i", "--input", action="append", dest="inputs",
        help="Input image for editing (can be specified multiple times, up to 14)",
    )
    parser.add_argument(
        "-r", "--ratio", choices=VALID_ASPECT_RATIOS,
        help="Aspect ratio (default: model decides)",
    )
    parser.add_argument(
        "-s", "--size", choices=["1K", "2K", "4K", "1k", "2k", "4k"],
        help="Output resolution",
    )
    parser.add_argument(
        "--search", action="store_true",
        help="Enable Google Search grounding for real-world accuracy",
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

    result = generate_image(
        prompt=args.prompt,
        output_path=args.output,
        input_paths=args.inputs,
        aspect_ratio=args.ratio,
        image_size=args.size.upper() if args.size else None,
        use_search=args.search,
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
