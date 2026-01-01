#!/usr/bin/env python3
"""
Rotate specified pages in a PDF file.

Usage:
    python rotate_pages.py <input_pdf> <output_pdf> <pages> <angle>

Arguments:
    input_pdf: Path to the input PDF file
    output_pdf: Path to the output PDF file
    pages: Pages to rotate (comma-separated, 1-indexed)
           Examples: "1", "1,3,5", "2-4", "all"
    angle: Rotation angle (90, 180, 270, or -90)
"""

import sys
from pypdf import PdfReader, PdfWriter


def parse_page_range(page_str, total_pages):
    """Parse page string into a set of page numbers (0-indexed)."""
    if page_str.lower() == 'all':
        return set(range(total_pages))

    pages = set()
    parts = page_str.split(',')

    for part in parts:
        part = part.strip()
        if '-' in part:
            start, end = part.split('-')
            pages.update(range(int(start) - 1, int(end)))
        else:
            pages.add(int(part) - 1)

    return pages


def rotate_pages(input_pdf, output_pdf, pages_to_rotate, angle):
    """Rotate specified pages in PDF."""
    reader = PdfReader(input_pdf)
    writer = PdfWriter()

    angle = int(angle)
    if angle not in [90, 180, 270, -90]:
        print("❌ Error: Angle must be 90, 180, 270, or -90")
        sys.exit(1)

    pages_set = parse_page_range(pages_to_rotate, len(reader.pages))

    for i, page in enumerate(reader.pages):
        if i in pages_set:
            page.rotate(angle)
        writer.add_page(page)

    with open(output_pdf, 'wb') as output_file:
        writer.write(output_file)

    print(f"✅ Rotated pages {pages_to_rotate} by {angle}° in {input_pdf}")
    print(f"   Saved to: {output_pdf}")


if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Usage: python rotate_pages.py <input_pdf> <output_pdf> <pages> <angle>")
        print("Example: python rotate_pages.py input.pdf output.pdf '1,3-5' 90")
        print("Example: python rotate_pages.py input.pdf output.pdf 'all' 180")
        sys.exit(1)

    rotate_pages(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
