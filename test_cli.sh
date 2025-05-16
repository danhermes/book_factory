#!/bin/bash
# Test script for the Book Writing Flow CLI

# Make sure the script is executable
chmod +x book_cli.py

# Create output directories if they don't exist
mkdir -p output/outlines
mkdir -p output/chapters

# Test 1: Generate an outline for chapter 1
echo "Test 1: Generating an outline for chapter 1..."
python book_cli.py outline --chapter 1

# Check if the output file exists
if [ -f "output/outlines/chapter1_outline.json" ] && [ -f "output/outlines/chapter1_outline.md" ]; then
    echo "✅ Test 1 passed: Chapter 1 outline files were created"
else
    echo "❌ Test 1 failed: Chapter 1 outline files were not created"
fi

# Test 2: Generate content for chapter 1 (only if outline exists)
if [ -f "output/outlines/chapter1_outline.json" ]; then
    echo "Test 2: Generating content for chapter 1..."
    python book_cli.py write --chapter 1 --outline "output/outlines/chapter1_outline.json"
    
    # Check if the output file exists
    chapter_file=$(find output/chapters -name "01_*.md" | head -n 1)
    if [ -n "$chapter_file" ]; then
        echo "✅ Test 2 passed: Chapter 1 content file was created: $chapter_file"
    else
        echo "❌ Test 2 failed: Chapter 1 content file was not created"
    fi
else
    echo "⚠️ Test 2 skipped: Chapter 1 outline does not exist"
fi

echo "Tests completed."