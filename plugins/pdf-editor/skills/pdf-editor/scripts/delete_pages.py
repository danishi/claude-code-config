#!/usr/bin/env python3
"""
Delete specified pages from a PDF file.

Usage:
    python delete_pages.py <input_pdf> <output_pdf> <pages>

Arguments:
    input_pdf: Path to the input PDF file
    output_pdf: Path to the output PDF file
    pages: Pages to delete (comma-separated, 1-indexed)
           Examples: "1", "1,3,5", "2-4", "1,3-5,7"
"""

import sys
from pypdf import PdfReader, PdfWriter


def parse_page_range(page_str):
    """Parse page string into a set of page numbers (0-indexed)."""
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


def delete_pages(input_pdf, output_pdf, pages_to_delete):
    """Delete specified pages from PDF."""
    reader = PdfReader(input_pdf)
    writer = PdfWriter()

    pages_to_delete_set = parse_page_range(pages_to_delete)

    for i, page in enumerate(reader.pages):
        if i not in pages_to_delete_set:
            writer.add_page(page)

    with open(output_pdf, 'wb') as output_file:
        writer.write(output_file)

    print(f"✅ Deleted pages {pages_to_delete} from {input_pdf}")
    print(f"   Saved to: {output_pdf}")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python delete_pages.py <input_pdf> <output_pdf> <pages>")
        print("Example: python delete_pages.py input.pdf output.pdf '1,3-5'")
        sys.exit(1)

    delete_pages(sys.argv[1], sys.argv[2], sys.argv[3])
