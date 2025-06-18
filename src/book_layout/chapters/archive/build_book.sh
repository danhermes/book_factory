#!/bin/bash

echo "Starting book build..."
set -e

BOOK_TEX="chatgpt_main.tex"
OUTPUT_DIR="output"
OUTPUT_NAME="chatgpt_in_the_office.pdf"

echo "Setting up environment..."
export PATH="$PATH:/c/Users/Dan Hermes/AppData/Local/Programs/MiKTeX/miktex/bin/x64"
#export TEXINPUTS="/c/Users/Dan Hermes/AppData/Local/Programs/MiKTeX/tex/latex/memoir"

mkdir -p "$OUTPUT_DIR"

echo "Running LaTeX build..."
pdflatex -output-directory="$OUTPUT_DIR" "$BOOK_TEX"
pdflatex -output-directory="$OUTPUT_DIR" "$BOOK_TEX"  # Run twice for TOC
echo "Build complete."

echo "✅ PDF built: $OUTPUT_DIR/$OUTPUT_NAME"
mv "$OUTPUT_DIR/chatgpt_main.pdf" "$OUTPUT_DIR/$OUTPUT_NAME"
