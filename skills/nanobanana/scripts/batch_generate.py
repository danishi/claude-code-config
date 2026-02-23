#!/usr/bin/env python3
"""
Batch image generation using Nano Banana Pro (Gemini 3 Pro Image).

Usage:
    python batch_generate.py "pixel art logo" -n 20 -d ./logos -p logo
    python batch_generate.py "product photo" -n 10 --ratio 1:1 --size 4K
    python batch_generate.py "landscape" -n 20 --parallel 5

Environment Variables:
    Same as generate.py (GEMINI_API_KEY or GOOGLE_CLOUD_PROJECT).
"""

import argparse
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from threading import Lock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from generate import generate_image, VALID_ASPECT_RATIOS, VALID_SIZES, disable_ssl_verification

_print_lock = Lock()


def _worker(args_tuple: tuple) -> dict:
    """Generate a single image (thread worker)."""
    idx, total, filepath, prompt, aspect_ratio, image_size, use_search, verbose, no_ssl_verify = args_tuple

    result = generate_image(
        prompt=prompt,
        output_path=str(filepath),
        aspect_ratio=aspect_ratio,
        image_size=image_size,
        use_search=use_search,
        verbose=False,
        no_ssl_verify=no_ssl_verify,
    )
    result["index"] = idx
    result["filename"] = filepath.name

    if verbose:
        with _print_lock:
            status = "OK" if result["success"] else f"FAILED: {result['error']}"
            print(f"[{idx}/{total}] {filepath.name}: {status}")

    return result


def batch_generate(
    prompt: str,
    count: int = 10,
    output_dir: str = "./nanobanana-images",
    prefix: str = "image",
    aspect_ratio: str | None = None,
    image_size: str | None = None,
    use_search: bool = False,
    delay: float = 3.0,
    parallel: int = 1,
    verbose: bool = True,
    no_ssl_verify: bool = False,
) -> list[dict]:
    """Generate multiple images with sequential naming.

    Args:
        prompt:         Text description for image generation.
        count:          Number of images to generate.
        output_dir:     Directory to save images.
        prefix:         Filename prefix.
        aspect_ratio:   Aspect ratio (e.g. "1:1", "16:9").
        image_size:     Resolution: "1K", "2K", or "4K".
        use_search:     Enable Google Search grounding.
        delay:          Seconds between sequential generations.
        parallel:       Number of concurrent requests (1 = sequential).
        verbose:        Print progress.
        no_ssl_verify:  Disable SSL certificate verification.

    Returns:
        List of result dicts.
    """
    if no_ssl_verify:
        disable_ssl_verification()
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    if verbose:
        print(f"Generating {count} images...")
        print(f"Prompt: {prompt}")
        print(f"Output: {output_dir}/{prefix}-XX.png")
        if aspect_ratio:
            print(f"Aspect ratio: {aspect_ratio}")
        if image_size:
            print(f"Size: {image_size}")
        if parallel > 1:
            print(f"Parallel workers: {parallel}")
        print()

    tasks = []
    for i in range(1, count + 1):
        fname = f"{prefix}-{str(i).zfill(len(str(count)))}.png"
        tasks.append(
            (i, count, out / fname, prompt, aspect_ratio, image_size, use_search, verbose, no_ssl_verify)
        )

    results: list[dict] = []

    if parallel > 1:
        with ThreadPoolExecutor(max_workers=parallel) as pool:
            futures = [pool.submit(_worker, t) for t in tasks]
            for fut in as_completed(futures):
                try:
                    results.append(fut.result())
                except Exception as exc:
                    results.append({
                        "success": False,
                        "error": str(exc),
                        "path": None,
                        "text": None,
                        "metadata": None,
                        "index": 0,
                        "filename": "unknown",
                    })
    else:
        for t in tasks:
            results.append(_worker(t))
            if t[0] < count and delay > 0:
                time.sleep(delay)

    results.sort(key=lambda r: r["index"])

    ok = sum(1 for r in results if r["success"])
    if verbose:
        print()
        print(f"Complete: {ok}/{count} images generated")
        print(f"Saved to: {output_dir}/")

    return results


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Batch generate images using Nano Banana Pro",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Examples:
  %(prog)s "pixel art logo" -n 20 -d ./logos -p logo
  %(prog)s "product photo" -n 10 --ratio 1:1 --size 4K
  %(prog)s "landscape painting" -n 5 --ratio 16:9 --delay 5
  %(prog)s "icon set" -n 20 --parallel 5
""",
    )

    parser.add_argument("prompt", help="Text prompt for image generation")
    parser.add_argument(
        "-n", "--count", type=int, default=10,
        help="Number of images (default: 10)",
    )
    parser.add_argument("-d", "--dir", default="./nanobanana-images", help="Output directory")
    parser.add_argument("-p", "--prefix", default="image", help="Filename prefix")
    parser.add_argument("-r", "--ratio", choices=VALID_ASPECT_RATIOS, help="Aspect ratio")
    parser.add_argument(
        "-s", "--size", choices=["1K", "2K", "4K", "1k", "2k", "4k"],
        help="Output resolution",
    )
    parser.add_argument("--search", action="store_true", help="Enable Google Search grounding")
    parser.add_argument(
        "--delay", type=float, default=3.0,
        help="Delay between sequential generations (default: 3s)",
    )
    parser.add_argument(
        "--parallel", type=int, default=1,
        help="Concurrent requests (default: 1, max recommended: 5)",
    )
    parser.add_argument("-q", "--quiet", action="store_true", help="Suppress progress")
    parser.add_argument("--json", action="store_true", dest="json_output", help="Output as JSON")
    parser.add_argument(
        "--no-ssl-verify", action="store_true",
        help="Disable SSL certificate verification (for proxies or self-signed certs)",
    )

    args = parser.parse_args()

    results = batch_generate(
        prompt=args.prompt,
        count=args.count,
        output_dir=args.dir,
        prefix=args.prefix,
        aspect_ratio=args.ratio,
        image_size=args.size.upper() if args.size else None,
        use_search=args.search,
        delay=args.delay,
        parallel=args.parallel,
        verbose=not args.quiet,
        no_ssl_verify=args.no_ssl_verify,
    )

    if args.json_output:
        print(json.dumps(results, ensure_ascii=False, indent=2))

    ok = sum(1 for r in results if r["success"])
    sys.exit(0 if ok > 0 else 1)


if __name__ == "__main__":
    main()
