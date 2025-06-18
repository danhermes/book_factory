#!/usr/bin/env bash
# This script is used to build the book from the Markdown files.
# Test with single chapter:
# pandoc ./chapters/chapter1_write.md -o test.pdf --listings --lua-filter=./lua/working_fixes.lua
set -e

BOOK_TEX="chatgpt_main.tex"
OUTPUT_DIR="output"
OUTPUT_NAME="chatgpt_in_the_office.pdf"
MKTEX_PATH="/c/Users/Dan Hermes/AppData/Local/Programs/MiKTeX/miktex/bin/x64"

export PATH="$PATH:$MKTEX_PATH"
mkdir -p "$OUTPUT_DIR"

echo "Converting only changed Markdown chapters…"
for md in chapters/*.md; do
  base=$(basename "$md" .md)
  tex="chapters/${base}.tex"
  # If the .tex is missing or older than the .md, convert it
  if [ ! -f "$tex" ] || [ "$md" -nt "$tex" ]; then
    echo "  ↻ $md → $tex"
    pandoc "$md" --from=markdown --to=latex -o "$tex" --listings --lua-filter=./lua/working_fixes.lua
  else
    echo "  ✓ $md (up to date)"
  fi
done

echo "Running LaTeX build…"
pdflatex -output-directory="$OUTPUT_DIR" "$BOOK_TEX"
pdflatex -output-directory="$OUTPUT_DIR" "$BOOK_TEX"

mv "$OUTPUT_DIR/${BOOK_TEX%.tex}.pdf" "$OUTPUT_DIR/$OUTPUT_NAME"
echo "✅ PDF ready at $OUTPUT_DIR/$OUTPUT_NAME"
