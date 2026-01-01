#!/usr/bin/env python3
"""
Reorder pages in a PDF file.

Usage:
    python reorder_pages.py <input_pdf> <output_pdf> <page_order>

Arguments:
    input_pdf: Path to the input PDF file
    output_pdf: Path to the output PDF file
    page_order: New page order (comma-separated, 1-indexed)
                Example: "2,1,3" - swap first two pages
                Example: "3,2,1" - reverse first three pages
"""

import sys
from pypdf import PdfReader, PdfWriter


def reorder_pages(input_pdf, output_pdf, page_order):
    """Reorder pages in PDF according to specified order."""
    reader = PdfReader(input_pdf)
    writer = PdfWriter()

    # Parse page order (convert from 1-indexed to 0-indexed)
    order = [int(p.strip()) - 1 for p in page_order.split(',')]

    # Validate page numbers
    total_pages = len(reader.pages)
    for page_num in order:
        if page_num < 0 or page_num >= total_pages:
            print(f"❌ Error: Page {page_num + 1} is out of range (PDF has {total_pages} pages)")
            sys.exit(1)

    # Add pages in the specified order
    for page_num in order:
        writer.add_page(reader.pages[page_num])

    with open(output_pdf, 'wb') as output_file:
        writer.write(output_file)

    print(f"✅ Reordered pages in {input_pdf}")
    print(f"   New order: {page_order}")
    print(f"   Saved to: {output_pdf}")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python reorder_pages.py <input_pdf> <output_pdf> <page_order>")
        print("Example: python reorder_pages.py input.pdf output.pdf '2,1,3,4'")
        sys.exit(1)

    reorder_pages(sys.argv[1], sys.argv[2], sys.argv[3])
