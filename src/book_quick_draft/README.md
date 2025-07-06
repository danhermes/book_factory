# Book Binding Script

The `build_book.sh` script is a comprehensive tool for compiling a complete book from individual Markdown chapter files into a professional PDF document.

## Overview

This script takes individual chapter Markdown files from the `output/chapters` directory and combines them into a single, professionally formatted PDF book with:

- Front and back covers (if provided)
- Front matter (if provided)
- Table of contents
- Properly formatted chapters with page breaks
- Back matter (if provided)

## Requirements

The script requires the following tools to be installed:

- `pandoc` - For Markdown to LaTeX conversion
- `xelatex` - For LaTeX to PDF conversion
- `imagemagick` - For processing cover images
- `pdfunite` - For merging PDF files

## Usage

```bash
cd src/book_quick_draft
./build_book.sh
```

## Input Files

The script expects the following files in the `output/chapters` directory:

- `*.md` - Chapter files (sorted alphanumerically)
- `front_matter.md` (optional) - Content for the front matter
- `back_matter.md` (optional) - Content for the back matter
- `front_cover.png` (optional) - Image for the front cover
- `back_cover.png` (optional) - Image for the back cover

## Output

The final compiled book is saved as:

```
output/chapters/final_book.pdf
```

## Process

0. Chapters have already been sanitized in the chapter-writing process. (run_chapter.py:sanitize_markdown(text))

1. Converts cover images to PDF format (if present)
2. Creates necessary LaTeX files for formatting
3. Gathers all chapter files in alphanumeric order
4. Adds page breaks between chapters
5. Generates a table of contents
6. Compiles everything into a LaTeX document
7. Converts the LaTeX document to PDF
8. Merges the PDF with cover pages (if present)

## Log File

The script generates a log file at `src/book_binding/build_book.log` that can be useful for troubleshooting if any issues occur during the build process.

## Customization

You can customize the book's appearance by modifying:

- `header-includes.tex` - For LaTeX customizations
- The pandoc command parameters in the script (lines 85-92) for title, author, margins, etc.