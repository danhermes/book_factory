#!/bin/bash
set -e

echo "=== DEBUG BUILD SCRIPT START ===" > debug.log
echo "Current directory: $(pwd)" >> debug.log
echo "Script directory: $(cd "$(dirname "$0")" && pwd)" >> debug.log

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CHAPTER_DIR="$SCRIPT_DIR/../../output/chapters"

echo "Chapter directory: $CHAPTER_DIR" >> debug.log
echo "Chapter directory exists: $(test -d "$CHAPTER_DIR" && echo "YES" || echo "NO")" >> debug.log

echo "=== LISTING CHAPTER FILES ===" >> debug.log
ls -la "$CHAPTER_DIR"/*.md 2>/dev/null || echo "No .md files found" >> debug.log

echo "=== LISTING _clean.md FILES ===" >> debug.log
ls -la "$CHAPTER_DIR"/*_clean.md 2>/dev/null || echo "No _clean.md files found" >> debug.log

echo "=== TESTING PANDOC ===" >> debug.log
pandoc --version >> debug.log 2>&1 || echo "Pandoc not found" >> debug.log

echo "=== TESTING XELATEX ===" >> debug.log
xelatex --version >> debug.log 2>&1 || echo "XeLaTeX not found" >> debug.log

echo "=== BUILD SCRIPT END ===" >> debug.log 