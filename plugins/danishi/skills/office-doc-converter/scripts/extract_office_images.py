#!/usr/bin/env python3
"""Extract embedded images from Office Open XML files (docx/pptx/xlsx).

The script copies images from common media folders (word/media, ppt/media, xl/media)
and groups them under an output directory named after the input file.
"""

from __future__ import annotations

import argparse
import shutil
import sys
import zipfile
from pathlib import Path
from typing import Iterable

MEDIA_FOLDERS: tuple[str, ...] = ("word/media/", "ppt/media/", "xl/media/")


def iter_media_members(zf: zipfile.ZipFile) -> Iterable[zipfile.ZipInfo]:
    """Yield media members from known Office media directories."""
    for info in zf.infolist():
        if info.is_dir():
            continue
        if any(info.filename.startswith(prefix) for prefix in MEDIA_FOLDERS):
            yield info


def extract_images(input_path: Path, output_dir: Path) -> list[Path]:
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    destination_root = output_dir / input_path.stem
    destination_root.mkdir(parents=True, exist_ok=True)

    extracted: list[Path] = []
    with zipfile.ZipFile(input_path) as zf:
        for info in iter_media_members(zf):
            target_path = destination_root / Path(info.filename).name
            target_path.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(info) as src, target_path.open("wb") as dst:
                shutil.copyfileobj(src, dst)
            extracted.append(target_path)
    return extracted


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract embedded images from Office files")
    parser.add_argument("input_file", type=Path, help="Office file path (.docx, .pptx, .xlsx, etc.)")
    parser.add_argument("output_dir", type=Path, help="Directory to store extracted images")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    extracted = extract_images(args.input_file, args.output_dir)

    if not extracted:
        print(f"No embedded images found in {args.input_file}")
    else:
        print(f"Extracted {len(extracted)} image(s) from {args.input_file} to {args.output_dir / args.input_file.stem}")
        for path in extracted:
            print(f"- {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
