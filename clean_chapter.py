#!/usr/bin/env python3
"""
Clean up chapter markdown files to fix YAML parsing issues
"""

import re
import os

def clean_chapter_file(file_path):
    """Clean up a chapter markdown file to fix formatting issues"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Remove duplicate chapter headers
    # Fix "## Chapter 1: Chapter 1: The AI-Enhanced Human" to "## Chapter 1: The AI-Enhanced Human"
    content = re.sub(r'## Chapter (\d+): Chapter \1: (.+)', r'## Chapter \1: \2', content)
    
    # Remove duplicate section headers (keep only the first occurrence)
    lines = content.split('\n')
    cleaned_lines = []
    seen_headers = set()
    
    for line in lines:
        # Check if this is a header (starts with #)
        if line.strip().startswith('#'):
            # Normalize the header for comparison (remove extra spaces, etc.)
            normalized = re.sub(r'\s+', ' ', line.strip())
            if normalized in seen_headers:
                # Skip duplicate headers
                continue
            seen_headers.add(normalized)
        
        cleaned_lines.append(line)
    
    # Join lines back together
    cleaned_content = '\n'.join(cleaned_lines)
    
    # Remove any empty lines at the beginning
    cleaned_content = cleaned_content.lstrip('\n')
    
    # Write the cleaned content back
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(cleaned_content)
    
    print(f"Cleaned {file_path}")

def main():
    """Main function"""
    chapter_file = "output/chapters/01_Chapter_1__The_AI-Enhanced_Human.md"
    
    if os.path.exists(chapter_file):
        clean_chapter_file(chapter_file)
        print("Chapter file cleaned successfully!")
    else:
        print(f"Chapter file not found: {chapter_file}")

if __name__ == "__main__":
    main()