# Book Layout System

The `book_layout` module is a professional-grade book typesetting system designed for producing high-quality, print-ready PDF books from Markdown content with advanced LaTeX formatting.

## Overview

This system converts Markdown chapter files into beautifully formatted PDF books using a custom LaTeX template based on the `memoir` document class. It provides precise control over typography, layout, and special formatting elements like code blocks and prompt boxes.

## Key Components

- **build.sh**: Main build script that converts Markdown to LaTeX and compiles the final PDF
- **chatgpt_main.tex**: Primary LaTeX template that defines the document structure
- **chatgpt_layout.sty**: Custom LaTeX style package with typography and layout settings
- **lua/**: Directory containing Lua filters for advanced text processing
  - **working_fixes.lua**: Handles duplicate headers, code blocks, and other formatting issues
- **chapters/**: Directory for chapter content in Markdown and converted LaTeX
  - **layout_clean.py**: Python script for preprocessing Markdown files (sanitizing, fixing headers)
- **output/**: Directory where the final PDF and intermediate files are stored

## Features

- Professional typesetting with the `memoir` document class
- Custom page dimensions (6" × 9") optimized for print
- Elegant typography with Palatino font and proper spacing
- Special formatting for code blocks with syntax highlighting and line wrapping
- Custom prompt boxes for ChatGPT examples
- Automatic table of contents generation
- Proper handling of front matter and main content
- Incremental builds that only process changed files

## Usage

### Local Usage

```bash
cd src/book_layout
./build.sh
```

The final PDF will be available at `output/chatgpt_in_the_office.pdf`.

### Docker Deployment

A deployment script is provided to easily build and run the Docker container:

```bash
# On Linux/macOS:
cd src/book_layout
./deploy.sh

# On Windows:
cd src/book_layout
bash deploy.sh
```

The deployment script supports the following commands:

- `deploy.sh` - Build and run the container (default)
- `deploy.sh build` - Only build the Docker image
- `deploy.sh run` - Only run the container
- `deploy.sh stop` - Stop the running container
- `deploy.sh logs` - View the container logs
- `deploy.sh status` - Check the status of the container
- `deploy.sh help` - Display help information

## Process

1. The `layout_clean.py` script preprocesses Markdown files to fix common issues
2. The `build.sh` script converts Markdown to LaTeX using pandoc with custom Lua filters
3. LaTeX files are compiled using pdflatex to generate the final PDF
4. Only changed files are reprocessed to speed up builds

## Comparison with book_quick_draft

While both modules produce PDF books from Markdown content, they serve different purposes:

### book_layout (This Module)

- **Purpose**: Professional-grade typesetting for final publication
- **Strengths**: 
  - Superior typography and layout control
  - Custom styling with LaTeX
  - Advanced text processing with Lua filters
  - Incremental builds for efficiency
  - Optimized for print publication
- **Best for**: Final book production, professional publishing

### book_quick_draft

- **Purpose**: Rapid prototyping and draft generation
- **Strengths**:
  - Simpler workflow
  - Faster processing
  - Easy integration of cover pages
  - Less configuration required
- **Best for**: Early drafts, quick previews, simple documents

## Requirements

- `pandoc` - For Markdown to LaTeX conversion
- `pdflatex` (part of TeX Live or MiKTeX) - For LaTeX to PDF conversion
- Python 3.x - For preprocessing scripts

## Customization

You can customize the book's appearance by modifying:

- `chatgpt_layout.sty` - For typography, page dimensions, and visual styling
- `chatgpt_main.tex` - For document structure and content inclusion
- Lua filters in the `lua/` directory - For custom text processing

## Advanced Usage

For more complex books, you can:

1. Add more chapters by including them in the `chatgpt_main.tex` file
2. Create custom environments in the style file for special content types
3. Develop additional Lua filters for specialized text processing
4. Modify the build script to include additional processing steps