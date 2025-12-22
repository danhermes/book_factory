# Book Quick Draft System

The `book_quick_draft` module is a streamlined book compilation system designed for rapidly generating draft PDFs from Markdown content with minimal configuration.

## Overview

This system converts Markdown chapter files into readable PDF books using pandoc and LaTeX, with a focus on speed and simplicity. It's ideal for creating early drafts, quick previews, and simple documents without the complexity of a full typesetting system.

## Key Components

- **build_book.sh**: Main build script that combines chapter files and compiles the final PDF
- **sanitize_all.py**: Python script for preprocessing Markdown files to fix common issues
- **header-includes.tex**: LaTeX customizations for basic formatting
- **pagebreak.md**: Template for adding page breaks between chapters
- **front_cover.pdf/back_cover.pdf**: Cover pages that can be integrated into the final PDF

## Features

- Simple, straightforward workflow for quick book compilation
- Automatic integration of front and back covers
- Table of contents generation
- Proper chapter separation with page breaks
- Basic LaTeX formatting for readable output
- Support for front matter and back matter
- Single-command build process

## Usage

```bash
cd src/book_quick_draft
./build_book.sh
```

The final PDF will be available at `output/chapters/final_book.pdf`.

## Process

1. The `sanitize_all.py` script preprocesses Markdown files to fix common issues
2. The `build_book.sh` script:
   - Converts cover images to PDF format (if present)
   - Creates necessary LaTeX files for formatting
   - Gathers all chapter files in alphanumeric order
   - Adds page breaks between chapters
   - Generates a table of contents
   - Compiles everything into a LaTeX document
   - Converts the LaTeX document to PDF
   - Merges the PDF with cover pages (if present)

## Comparison with book_layout

While both modules produce PDF books from Markdown content, they serve different purposes:

### book_quick_draft (This Module)

- **Purpose**: Rapid prototyping and draft generation
- **Strengths**:
  - Simpler workflow
  - Faster processing
  - Easy integration of cover pages
  - Less configuration required
  - Minimal setup needed
- **Best for**: Early drafts, quick previews, simple documents, rapid iteration

### book_layout

- **Purpose**: Professional-grade typesetting for final publication
- **Strengths**: 
  - Superior typography and layout control
  - Custom styling with LaTeX
  - Advanced text processing with Lua filters
  - Incremental builds for efficiency
  - Optimized for print publication
- **Best for**: Final book production, professional publishing

## Requirements

The script requires the following tools to be installed:

- `pandoc` - For Markdown to LaTeX conversion
- `xelatex` - For LaTeX to PDF conversion
- `imagemagick` - For processing cover images (if needed)
- `pdfunite` - For merging PDF files (if using covers)

## Input Files

The script expects the following files in the `output/chapters` directory:

- `*.md` - Chapter files (sorted alphanumerically)
- `front_matter.md` (optional) - Content for the front matter
- `back_matter.md` (optional) - Content for the back matter
- `front_cover.png` (optional) - Image for the front cover
- `back_cover.png` (optional) - Image for the back cover

## Customization

You can customize the book's appearance by modifying:

- `header-includes.tex` - For LaTeX customizations
- The pandoc command parameters in the build script for title, author, margins, etc.

## When to Use book_quick_draft vs. book_layout

- **Use book_quick_draft when**:
  - You need a quick preview of your book
  - You're in the early drafting stages
  - You want a simple PDF without complex formatting
  - You need to rapidly iterate on content
  - You don't need advanced typesetting features

- **Use book_layout when**:
  - You're preparing for final publication
  - You need professional typesetting
  - You require advanced formatting features
  - You want precise control over typography and layout
  - The book is ready for print production