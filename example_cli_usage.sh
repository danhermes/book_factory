#!/bin/bash
# Example script demonstrating how to use the Book Writing Flow CLI

# Make sure the script is executable
chmod +x book_cli.py

echo "===== Book Writing Flow CLI Examples ====="

# 1. Generate a complete book outline
echo -e "\n1. Generating a complete book outline..."
python book_cli.py outline --topic "ChatGPT for Business"

# 2. Generate an outline for a specific chapter
echo -e "\n2. Generating an outline for chapter 3..."
python book_cli.py outline --chapter 3

# 3. Generate content for a specific chapter
echo -e "\n3. Generating content for chapter 2..."
python book_cli.py write --chapter 2

# 4. Generate specific chapters
echo -e "\n4. Generating chapters 1 and 3..."
python book_cli.py flow --chapters "1,3" --topic "ChatGPT for Business"

# 5. Generate the entire book
echo -e "\n5. Generating the entire book..."
# Uncomment the line below to run the full book generation
# python book_cli.py flow --chapters "all"

echo -e "\nAll examples completed. Check the output directories:"
echo "- Outlines: output/outlines/"
echo "- Chapters: output/chapters/"