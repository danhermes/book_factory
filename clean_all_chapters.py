#!/usr/bin/env python3
"""
Clean up all chapter markdown files to fix YAML parsing issues
"""

import re
import os
import glob

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
    # Find all markdown files in current directory
    md_files = glob.glob("*.md")
    
    if not md_files:
        print("No markdown files found in current directory")
        return
    
    print(f"Found {len(md_files)} markdown files to clean:")
    for file in md_files:
        print(f"  - {file}")
    
    # Clean each file
    for file_path in md_files:
        clean_chapter_file(file_path)
    
    print("All chapter files cleaned successfully!")

if __name__ == "__main__":
    main() 