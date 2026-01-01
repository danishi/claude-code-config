#!/usr/bin/env python3
"""
Split a PDF file into multiple files.

Usage:
    python split_pdf.py <input_pdf> <output_dir> <split_spec>

Arguments:
    input_pdf: Path to the input PDF file
    output_dir: Directory to save split PDF files
    split_spec: How to split the PDF:
                - "single": Each page becomes a separate file
                - "1-3,4-6,7-9": Split at specified page ranges
                - "3": Split every 3 pages
"""

import sys
import os
from pypdf import PdfReader, PdfWriter


def split_pdf_single(reader, output_dir, base_name):
    """Split PDF into individual pages."""
    for i, page in enumerate(reader.pages):
        writer = PdfWriter()
        writer.add_page(page)

        output_file = os.path.join(output_dir, f"{base_name}_page_{i+1}.pdf")
        with open(output_file, 'wb') as f:
            writer.write(f)

    print(f"✅ Split into {len(reader.pages)} individual pages")


def split_pdf_ranges(reader, output_dir, base_name, ranges):
    """Split PDF by specified page ranges."""
    parts = ranges.split(',')

    for idx, part in enumerate(parts):
        writer = PdfWriter()

        if '-' in part:
            start, end = part.split('-')
            start, end = int(start) - 1, int(end) - 1
        else:
            start = end = int(part) - 1

        for i in range(start, end + 1):
            if i < len(reader.pages):
                writer.add_page(reader.pages[i])

        output_file = os.path.join(output_dir, f"{base_name}_part_{idx+1}.pdf")
        with open(output_file, 'wb') as f:
            writer.write(f)

    print(f"✅ Split into {len(parts)} parts")


def split_pdf_every_n(reader, output_dir, base_name, n):
    """Split PDF every n pages."""
    n = int(n)
    total_pages = len(reader.pages)
    part_num = 1

    for start in range(0, total_pages, n):
        writer = PdfWriter()

        for i in range(start, min(start + n, total_pages)):
            writer.add_page(reader.pages[i])

        output_file = os.path.join(output_dir, f"{base_name}_part_{part_num}.pdf")
        with open(output_file, 'wb') as f:
            writer.write(f)

        part_num += 1

    print(f"✅ Split into {part_num - 1} parts ({n} pages each)")


def split_pdf(input_pdf, output_dir, split_spec):
    """Split PDF according to specification."""
    reader = PdfReader(input_pdf)

    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Get base name for output files
    base_name = os.path.splitext(os.path.basename(input_pdf))[0]

    if split_spec == 'single':
        split_pdf_single(reader, output_dir, base_name)
    elif ',' in split_spec or '-' in split_spec:
        split_pdf_ranges(reader, output_dir, base_name, split_spec)
    else:
        split_pdf_every_n(reader, output_dir, base_name, split_spec)

    print(f"   Saved to: {output_dir}")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python split_pdf.py <input_pdf> <output_dir> <split_spec>")
        print("Examples:")
        print("  python split_pdf.py input.pdf ./output single")
        print("  python split_pdf.py input.pdf ./output '1-3,4-6,7-9'")
        print("  python split_pdf.py input.pdf ./output 3")
        sys.exit(1)

    split_pdf(sys.argv[1], sys.argv[2], sys.argv[3])
