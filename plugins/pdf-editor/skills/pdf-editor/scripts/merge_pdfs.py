#!/usr/bin/env python3
"""
Merge multiple PDF files into a single PDF.

Usage:
    python merge_pdfs.py <output_pdf> <input_pdf1> <input_pdf2> [<input_pdf3> ...]

Arguments:
    output_pdf: Path to the output PDF file
    input_pdfN: Paths to input PDF files to merge (in order)
"""

import sys
from pypdf import PdfWriter


def merge_pdfs(output_pdf, input_pdfs):
    """Merge multiple PDF files into one."""
    writer = PdfWriter()

    for pdf_file in input_pdfs:
        writer.append(pdf_file)

    with open(output_pdf, 'wb') as output_file:
        writer.write(output_file)

    print(f"✅ Merged {len(input_pdfs)} PDF files")
    print(f"   Files: {', '.join(input_pdfs)}")
    print(f"   Saved to: {output_pdf}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python merge_pdfs.py <output_pdf> <input_pdf1> <input_pdf2> [<input_pdf3> ...]")
        print("Example: python merge_pdfs.py output.pdf file1.pdf file2.pdf file3.pdf")
        sys.exit(1)

    output_pdf = sys.argv[1]
    input_pdfs = sys.argv[2:]

    merge_pdfs(output_pdf, input_pdfs)
