#!/usr/bin/env python3
"""Generate images using Codex CLI's built-in image_gen tool.

Wraps `codex exec` to leverage the built-in image generation capability
without requiring an OPENAI_API_KEY.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

DEFAULT_OUTPUT_DIR = "./codex-images"
DEFAULT_OUTPUT_NAME = "image.png"
CODEX_GENERATED_DIR = os.path.join(
    os.environ.get("CODEX_HOME", os.path.expanduser("~/.codex")),
    "generated_images",
)


def find_codex() -> str:
    """Find the codex CLI binary."""
    result = shutil.which("codex")
    if result:
        return result
    die("codex CLI not found. Install it first: https://github.com/openai/codex")
    return ""


def die(msg: str, code: int = 1) -> None:
    print(f"Error: {msg}", file=sys.stderr)
    raise SystemExit(code)


def build_prompt(
    prompt: str,
    *,
    aspect: str | None = None,
    style: str | None = None,
    negative: str | None = None,
) -> str:
    """Build an augmented prompt for the built-in image_gen tool."""
    parts = []

    if style:
        parts.append(f"Style: {style}.")

    parts.append(prompt.rstrip(".") + ".")

    if aspect:
        aspect_descriptions = {
            "1:1": "square composition (1:1 aspect ratio)",
            "16:9": "wide landscape composition (16:9 aspect ratio)",
            "9:16": "tall portrait composition (9:16 aspect ratio)",
            "4:3": "standard landscape composition (4:3 aspect ratio)",
            "3:4": "standard portrait composition (3:4 aspect ratio)",
            "3:2": "classic landscape composition (3:2 aspect ratio)",
            "2:3": "classic portrait composition (2:3 aspect ratio)",
        }
        desc = aspect_descriptions.get(aspect, f"{aspect} aspect ratio")
        parts.append(f"Use a {desc}.")

    if negative:
        parts.append(f"Avoid: {negative}.")

    return " ".join(parts)


def build_codex_instruction(prompt: str, output_path: str) -> str:
    """Build the instruction for codex exec."""
    return (
        f"You MUST generate a brand-new image using the built-in image_gen "
        f"tool. Do NOT reuse any existing file. Do NOT use the CLI fallback "
        f"or scripts/image_gen.py. After generating the new image, copy the "
        f"generated file to {output_path}.\n\n"
        f"Image prompt: {prompt}"
    )


def get_recent_images(before_ts: float) -> list[Path]:
    """Find images generated after the given timestamp."""
    generated_dir = Path(CODEX_GENERATED_DIR)
    if not generated_dir.exists():
        return []
    results = []
    for p in generated_dir.rglob("*.png"):
        if p.stat().st_mtime > before_ts:
            results.append(p)
    for p in generated_dir.rglob("*.webp"):
        if p.stat().st_mtime > before_ts:
            results.append(p)
    for p in generated_dir.rglob("*.jpg"):
        if p.stat().st_mtime > before_ts:
            results.append(p)
    results.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return results


def run_codex(instruction: str, workdir: str, timeout: int, verbose: bool) -> bool:
    """Run codex exec and return True on success."""
    codex = find_codex()
    cmd = [
        codex, "exec",
        "-s", "danger-full-access",
        "-C", workdir,
        instruction,
    ]

    if verbose:
        print(f"Running: {' '.join(cmd[:6])} ...", file=sys.stderr)

    try:
        result = subprocess.run(
            cmd,
            capture_output=not verbose,
            text=True,
            timeout=timeout,
        )
        if result.returncode != 0:
            if not verbose and result.stderr:
                print(result.stderr, file=sys.stderr)
            return False
        return True
    except subprocess.TimeoutExpired:
        die(f"Codex timed out after {timeout}s. Try increasing --timeout.")
    except FileNotFoundError:
        die("codex CLI not found.")
    return False


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate images using Codex CLI's built-in image_gen tool."
    )
    parser.add_argument("prompt", help="Text prompt describing the image to generate")
    parser.add_argument(
        "-o", "--output", default=None,
        help="Output file path (default: ./codex-images/image.png)",
    )
    parser.add_argument(
        "-a", "--aspect", default=None,
        choices=["1:1", "16:9", "9:16", "4:3", "3:4", "3:2", "2:3"],
        help="Aspect ratio (default: model decides)",
    )
    parser.add_argument(
        "-s", "--style", default=None,
        help='Style description (e.g. "watercolor", "photorealistic", "anime")',
    )
    parser.add_argument(
        "--negative", default=None,
        help="Things to avoid in the image",
    )
    parser.add_argument(
        "-n", "--count", type=int, default=1,
        help="Number of images to generate (default: 1)",
    )
    parser.add_argument(
        "--timeout", type=int, default=300,
        help="Timeout in seconds per image (default: 300)",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true",
        help="Show codex output",
    )
    parser.add_argument(
        "--json", action="store_true",
        help="Output result as JSON",
    )

    args = parser.parse_args()

    output_dir = DEFAULT_OUTPUT_DIR
    output_name = DEFAULT_OUTPUT_NAME
    if args.output:
        output_path = Path(args.output)
        output_dir = str(output_path.parent)
        output_name = output_path.name
    else:
        output_path = Path(output_dir) / output_name

    Path(output_dir).mkdir(parents=True, exist_ok=True)

    augmented_prompt = build_prompt(
        args.prompt,
        aspect=args.aspect,
        style=args.style,
        negative=args.negative,
    )

    generated_files: list[str] = []
    workdir = os.getcwd()

    for i in range(args.count):
        if args.count > 1:
            stem = Path(output_name).stem
            suffix = Path(output_name).suffix or ".png"
            current_output = str(Path(output_dir) / f"{stem}_{i}{suffix}")
        else:
            current_output = str(output_path)

        abs_output = str(Path(current_output).resolve())

        if not args.json:
            label = f"[{i + 1}/{args.count}] " if args.count > 1 else ""
            print(f"{label}Generating: {augmented_prompt}", file=sys.stderr)

        before_ts = time.time()
        instruction = build_codex_instruction(augmented_prompt, abs_output)
        success = run_codex(instruction, workdir, args.timeout, args.verbose)

        if success and Path(abs_output).exists():
            generated_files.append(abs_output)
            if not args.json:
                print(f"Saved: {abs_output}", file=sys.stderr)
        elif success:
            new_images = get_recent_images(before_ts)
            if new_images:
                src = new_images[0]
                shutil.copy2(str(src), abs_output)
                generated_files.append(abs_output)
                if not args.json:
                    print(f"Saved: {abs_output} (copied from {src})", file=sys.stderr)
            else:
                print(
                    f"Warning: Codex reported success but no image found at {abs_output}",
                    file=sys.stderr,
                )
        else:
            print(f"Warning: Failed to generate image", file=sys.stderr)

    if args.json:
        print(json.dumps({
            "prompt": args.prompt,
            "augmented_prompt": augmented_prompt,
            "files": generated_files,
            "count": len(generated_files),
        }, ensure_ascii=False, indent=2))
    elif not generated_files:
        die("No images were generated.")
    else:
        print(f"\nDone. Generated {len(generated_files)} image(s).", file=sys.stderr)


if __name__ == "__main__":
    main()
