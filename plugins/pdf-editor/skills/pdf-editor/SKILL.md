---
name: pdf-editor
description: PDF page manipulation toolkit for editing PDF structure. Use when Claude needs to work with PDF files for (1) Deleting pages, (2) Reordering or rearranging pages, (3) Inserting pages from other PDFs, (4) Rotating pages, (5) Splitting PDFs into multiple files, (6) Merging multiple PDFs into one, or any other PDF page manipulation tasks.
---

# PDF Editor

## Overview

Provides Python scripts for common PDF page manipulation operations. All scripts use the `pypdf` library for reliable, deterministic PDF editing.

## Quick Start

Install the required dependency:
```bash
pip install pypdf
```

Each script can be run directly from the command line. All scripts follow the pattern:
```bash
python scripts/<script_name>.py <input_args> <output_file>
```

## Delete Pages

Remove specific pages from a PDF.

**Script:** `scripts/delete_pages.py`

**Usage:**
```bash
python scripts/delete_pages.py <input_pdf> <output_pdf> <pages>
```

**Examples:**
```bash
# Delete page 1
python scripts/delete_pages.py input.pdf output.pdf "1"

# Delete pages 1, 3, and 5
python scripts/delete_pages.py input.pdf output.pdf "1,3,5"

# Delete pages 2-4
python scripts/delete_pages.py input.pdf output.pdf "2-4"

# Delete pages 1, 3-5, and 7
python scripts/delete_pages.py input.pdf output.pdf "1,3-5,7"
```

**Page specification:** Comma-separated, 1-indexed. Supports ranges with hyphen (e.g., "2-4").

## Reorder Pages

Change the order of pages in a PDF.

**Script:** `scripts/reorder_pages.py`

**Usage:**
```bash
python scripts/reorder_pages.py <input_pdf> <output_pdf> <page_order>
```

**Examples:**
```bash
# Swap first two pages
python scripts/reorder_pages.py input.pdf output.pdf "2,1,3,4,5"

# Reverse first three pages
python scripts/reorder_pages.py input.pdf output.pdf "3,2,1,4,5"
```

**Page specification:** Comma-separated list in desired order, 1-indexed. Must specify all pages to include in output.

## Insert Pages

Insert pages from one PDF into another.

**Script:** `scripts/insert_pages.py`

**Usage:**
```bash
python scripts/insert_pages.py <base_pdf> <source_pdf> <output_pdf> <position> <pages>
```

**Arguments:**
- `position`: Where to insert (1-indexed, 0 = prepend)
- `pages`: Pages from source PDF to insert (supports "all" keyword)

**Examples:**
```bash
# Insert page 5 from source.pdf after page 2 of base.pdf
python scripts/insert_pages.py base.pdf source.pdf output.pdf 2 "5"

# Insert pages 1, 3-5 from source.pdf at the beginning
python scripts/insert_pages.py base.pdf source.pdf output.pdf 0 "1,3-5"

# Insert all pages from source.pdf after page 3
python scripts/insert_pages.py base.pdf source.pdf output.pdf 3 "all"
```

## Rotate Pages

Rotate specific pages by 90, 180, or 270 degrees.

**Script:** `scripts/rotate_pages.py`

**Usage:**
```bash
python scripts/rotate_pages.py <input_pdf> <output_pdf> <pages> <angle>
```

**Arguments:**
- `angle`: 90, 180, 270, or -90

**Examples:**
```bash
# Rotate page 1 by 90 degrees clockwise
python scripts/rotate_pages.py input.pdf output.pdf "1" 90

# Rotate pages 1, 3-5 by 180 degrees
python scripts/rotate_pages.py input.pdf output.pdf "1,3-5" 180

# Rotate all pages by 90 degrees
python scripts/rotate_pages.py input.pdf output.pdf "all" 90
```

**Page specification:** Supports "all" keyword to rotate all pages.

## Split PDF

Split one PDF into multiple files.

**Script:** `scripts/split_pdf.py`

**Usage:**
```bash
python scripts/split_pdf.py <input_pdf> <output_dir> <split_spec>
```

**Split specifications:**
- `"single"`: Each page becomes a separate file
- `"1-3,4-6,7-9"`: Split at specified page ranges
- `"3"`: Split every N pages

**Examples:**
```bash
# Split into individual pages
python scripts/split_pdf.py input.pdf ./output single

# Split into specific ranges
python scripts/split_pdf.py input.pdf ./output "1-3,4-6,7-9"

# Split every 3 pages
python scripts/split_pdf.py input.pdf ./output 3
```

**Output:** Files named `{original_name}_page_{N}.pdf` or `{original_name}_part_{N}.pdf`

## Merge PDFs

Combine multiple PDF files into one.

**Script:** `scripts/merge_pdfs.py`

**Usage:**
```bash
python scripts/merge_pdfs.py <output_pdf> <input_pdf1> <input_pdf2> [<input_pdf3> ...]
```

**Example:**
```bash
# Merge three PDFs in order
python scripts/merge_pdfs.py output.pdf file1.pdf file2.pdf file3.pdf
```

**Note:** PDFs are merged in the order they are specified on the command line.

## Dependencies

All scripts require the `pypdf` library:

```bash
pip install pypdf
```

If using an externally-managed Python environment, create a virtual environment first:

```bash
python3 -m venv venv
source venv/bin/activate
pip install pypdf
```
