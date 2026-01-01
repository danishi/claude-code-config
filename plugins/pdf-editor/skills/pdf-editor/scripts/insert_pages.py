#!/usr/bin/env python3
"""
Insert pages from one PDF into another PDF.

Usage:
    python insert_pages.py <base_pdf> <source_pdf> <output_pdf> <position> <pages>

Arguments:
    base_pdf: Path to the base PDF file
    source_pdf: Path to the source PDF file (to extract pages from)
    output_pdf: Path to the output PDF file
    position: Position to insert pages (1-indexed, 0 means prepend)
    pages: Pages to insert from source (comma-separated, 1-indexed)
           Examples: "1", "1,3,5", "2-4", "1,3-5,7", "all"
"""

import sys
from pypdf import PdfReader, PdfWriter


def parse_page_range(page_str, total_pages):
    """Parse page string into a list of page numbers (0-indexed)."""
    if page_str.lower() == 'all':
        return list(range(total_pages))

    pages = []
    parts = page_str.split(',')

    for part in parts:
        part = part.strip()
        if '-' in part:
            start, end = part.split('-')
            pages.extend(range(int(start) - 1, int(end)))
        else:
            pages.append(int(part) - 1)

    return pages


def insert_pages(base_pdf, source_pdf, output_pdf, position, pages_to_insert):
    """Insert pages from source PDF into base PDF at specified position."""
    base_reader = PdfReader(base_pdf)
    source_reader = PdfReader(source_pdf)
    writer = PdfWriter()

    position = int(position)
    pages_list = parse_page_range(pages_to_insert, len(source_reader.pages))

    # Validate page numbers
    for page_num in pages_list:
        if page_num < 0 or page_num >= len(source_reader.pages):
            print(f"❌ Error: Page {page_num + 1} is out of range in source PDF")
            sys.exit(1)

    # Add pages from base PDF up to insertion position
    for i in range(min(position, len(base_reader.pages))):
        writer.add_page(base_reader.pages[i])

    # Insert pages from source PDF
    for page_num in pages_list:
        writer.add_page(source_reader.pages[page_num])

    # Add remaining pages from base PDF
    for i in range(position, len(base_reader.pages)):
        writer.add_page(base_reader.pages[i])

    with open(output_pdf, 'wb') as output_file:
        writer.write(output_file)

    print(f"✅ Inserted pages {pages_to_insert} from {source_pdf}")
    print(f"   Into {base_pdf} at position {position}")
    print(f"   Saved to: {output_pdf}")


if __name__ == "__main__":
    if len(sys.argv) != 6:
        print("Usage: python insert_pages.py <base_pdf> <source_pdf> <output_pdf> <position> <pages>")
        print("Example: python insert_pages.py base.pdf source.pdf output.pdf 2 '1,3-5'")
        print("Example: python insert_pages.py base.pdf source.pdf output.pdf 0 'all'")
        sys.exit(1)

    insert_pages(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])
