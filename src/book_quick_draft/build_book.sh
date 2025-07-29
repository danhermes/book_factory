#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CHAPTER_DIR="$SCRIPT_DIR/../../output/chapters"

OUTPUT="$CHAPTER_DIR/final_book.pdf"
LOGFILE="$SCRIPT_DIR/build_book.log"
TEXFILE="$SCRIPT_DIR/build_temp.tex"
HEADER_TEX="$SCRIPT_DIR/header-includes.tex"

FRONT_COVER_IMAGE="$CHAPTER_DIR/front_cover.png"
BACK_COVER_IMAGE="$CHAPTER_DIR/back_cover.png"
FRONT_MATTER="$CHAPTER_DIR/front_matter.md"
BACK_MATTER="$CHAPTER_DIR/back_matter.md"
PAGEBREAK="$SCRIPT_DIR/pagebreak.md"

FRONT_COVER_PDF="$SCRIPT_DIR/front_cover.pdf"
BACK_COVER_PDF="$SCRIPT_DIR/back_cover.pdf"

BOOK_CONFIG="../../output/outlines/book_outline.json"
BOOK_TITLE=$(python -c "import sys, json; print(json.load(open('$BOOK_CONFIG'))['book_title'])")
#BOOK_AUTHOR=$(python -c "import sys, json; print(json.load(open('$BOOK_CONFIG'))['author'])") #Todo
#BOOK_DATE=$(python -c "import sys, json; print(json.load(open('$BOOK_CONFIG'))['date'])") #Todo

echo "📘 Starting full book build from output/chapters/..."

# Create header-includes.tex if missing
if [ ! -f "$HEADER_TEX" ]; then
  echo "Creating header-includes.tex..."
  cat <<EOF > "$HEADER_TEX"
\tableofcontents
\newpage
EOF
fi

# Create pagebreak.md if missing
if [ ! -f "$PAGEBREAK" ]; then
  echo "\newpage" > "$PAGEBREAK"
  echo "➕ Created pagebreak.md"
fi

# Convert front cover image
if [ -f "$FRONT_COVER_IMAGE" ]; then
  echo "🖼️ Converting front cover image..."
  magick "$FRONT_COVER_IMAGE" -density 300 -resize 2550x3300^ -background white -gravity center -extent 2550x3300 "$FRONT_COVER_PDF"
else
  echo "⚠️ Warning: front_cover.png not found. Skipping."
  FRONT_COVER_PDF=""
fi

# Convert back cover image
if [ -f "$BACK_COVER_IMAGE" ]; then
  echo "🖼️ Converting back cover image..."
  magick "$BACK_COVER_IMAGE" -density 300 -resize 2550x3300^ -gravity north -extent 2550x3300 "$BACK_COVER_PDF"
else
  echo "⚠️ Warning: back_cover.png not found. Skipping."
  BACK_COVER_PDF=""
fi

echo "📦 Gathering chapters"
CHAPTERS=($(ls "$CHAPTER_DIR"/*.md | sort -V))
INPUTS=()

# Add front matter if present
if [ -f "$FRONT_MATTER" ]; then
  echo "📄 Including front matter"
  INPUTS+=("$FRONT_MATTER")
else
  echo "⚠️ Warning: front_matter.md not found. Skipping."
fi

# Append chapters with page breaks
for ((i=0; i<${#CHAPTERS[@]}; i++)); do
  INPUTS+=("${CHAPTERS[i]}")
  if (( i < ${#CHAPTERS[@]} - 1 )); then
    INPUTS+=("$PAGEBREAK")
  fi
done

# Add back matter if present
if [ -f "$BACK_MATTER" ]; then
  echo "📄 Including back matter"
  INPUTS+=("$BACK_MATTER")
else
  echo "⚠️ Warning: back_matter.md not found. Skipping."
fi

echo "🛠️ Generating LaTeX with TOC injection..."
pandoc --standalone --pdf-engine=xelatex \
  --include-before-body="$HEADER_TEX" \
  -V title="$BOOK_TITLE" -V author="Dan Hermes" -V date="\\today" \
  -V geometry=top=0.75in,bottom=0.75in,left=0.65in,right=0.65in \
  "${INPUTS[@]}" -o "$TEXFILE" > "$LOGFILE" 2>&1 || {
  echo "❌ Pandoc failed. See $LOGFILE"
  exit 1
}

echo "📄 Compiling PDF with XeLaTeX..."
(
  cd "$SCRIPT_DIR"
  xelatex -interaction=nonstopmode "$(basename "$TEXFILE")" >> "$LOGFILE" 2>&1
) || {
  echo "❌ XeLaTeX failed. See $LOGFILE"
  exit 1
}

echo "📚 Merging final PDF..."
MERGE_LIST=()
[ -f "$FRONT_COVER_PDF" ] && MERGE_LIST+=("$FRONT_COVER_PDF")
MERGE_LIST+=("$SCRIPT_DIR/build_temp.pdf")
[ -f "$BACK_COVER_PDF" ] && MERGE_LIST+=("$BACK_COVER_PDF")

if [ ${#MERGE_LIST[@]} -eq 1 ]; then
  mv "${MERGE_LIST[0]}" "$OUTPUT"
else
  pdfunite "${MERGE_LIST[@]}" "$OUTPUT"
fi

echo "✅ Success! Output written to: $OUTPUT"
