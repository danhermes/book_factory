#!/usr/bin/env python
import re
import json
from pydantic import BaseModel
from typing import List, Optional

class Section(BaseModel):
    """Section of a chapter"""
    title: str
    content: str = ""

class Chapter(BaseModel):
    """Chapter of the book"""
    title: str
    content: str = ""
    sections: List[Section] = []

class Outline(BaseModel):
    """Outline of the book"""
    total_chapters: int
    chapters: List[Chapter]

def parse_outline_text(content: str):
    """
    Parse the outline text content into a structured outline.
    
    Args:
        content: The text content of the outline file.
        
    Returns:
        A dictionary with total_chapters and chapters list.
    """
    lines = content.strip().split('\n')
    chapters = []
    current_chapter = None
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Skip empty lines and the title
        if not line or line == "Expanded Outline - ChatGPT for Business" or line == "Introduction" or line.isdigit():
            i += 1
            continue
            
        # Check if this is a chapter heading
        if line.startswith("Chapter"):
            # Extract chapter number and title
            parts = line.split(":", 1)
            if len(parts) > 1:
                chapter_title = parts[1].strip()
                
                # Save previous chapter if exists
                if current_chapter:
                    chapters.append(current_chapter)
                
                # Create new chapter
                current_chapter = {
                    "title": chapter_title,
                    "sections": []
                }
            i += 1
            continue
        
        # Check if this is a section
        if line.startswith("-") and current_chapter:
            section_line = line[1:].strip()  # Remove the dash
            
            # Handle different section types
            if section_line.startswith("Theme:"):
                # Add theme as the first section (introduction)
                current_chapter["sections"].append({
                    "title": f"Theme: {section_line.replace('Theme:', '').strip()} (Introduction)"
                })
            elif section_line.startswith("Original Stories:"):
                # Split stories into individual sections
                stories_text = section_line.replace("Original Stories:", "").strip()
                stories = [s.strip() for s in stories_text.split(",")]
                for story in stories:
                    current_chapter["sections"].append({
                        "title": f"Story: {story} (Story)"
                    })
            elif section_line.startswith("Topic Explanations:"):
                # Split topic explanations into individual sections
                topics_text = section_line.replace("Topic Explanations:", "").strip()
                topics = [t.strip() for t in topics_text.split(",")]
                for topic in topics:
                    current_chapter["sections"].append({
                        "title": f"{topic} (Topic Explanation)"
                    })
            elif section_line.startswith("Bonus Topics:"):
                # Split bonus topics into individual sections
                bonuses_text = section_line.replace("Bonus Topics:", "").strip()
                bonuses = [b.strip() for b in bonuses_text.split(",")]
                for bonus in bonuses:
                    current_chapter["sections"].append({
                        "title": f"{bonus} (Bonus Topic)"
                    })
            elif section_line.startswith("Big Box:"):
                # Add big box as a technical section
                current_chapter["sections"].append({
                    "title": f"{section_line.replace('Big Box:', '').strip()} (Big Box)"
                })
            elif section_line.startswith("Outro:"):
                # Add outro as the last section
                current_chapter["sections"].append({
                    "title": f"{section_line.replace('Outro:', '').strip()} (Chapter Summary)"
                })
        i += 1
    
    # Add the last chapter
    if current_chapter:
        chapters.append(current_chapter)
    
    return {
        "total_chapters": len(chapters),
        "chapters": chapters
    }

def main():
    # Read the text file
    txt_path = "ChatGPT_for_Business_Expanded_Outline.txt"
    print(f"Reading outline file: {txt_path}")
    
    try:
        with open(txt_path, 'r') as f:
            txt_content = f.read()
        
        # Parse the text content
        parsed_outline = parse_outline_text(txt_content)
        
        # Convert to Pydantic models
        outline = Outline(
            total_chapters=parsed_outline["total_chapters"],
            chapters=[]
        )
        
        for chapter_data in parsed_outline["chapters"]:
            chapter = Chapter(
                title=chapter_data["title"],
                sections=[]
            )
            
            for section_data in chapter_data["sections"]:
                section = Section(
                    title=section_data["title"]
                )
                chapter.sections.append(section)
            
            outline.chapters.append(chapter)
        
        # Save to markdown file
        with open("book_outline.md", "w") as f:
            f.write(f"# Book Outline: ChatGPT for Business\n\n")
            
            for i, chapter in enumerate(outline.chapters, 1):
                f.write(f"## Chapter {i}: {chapter.title}\n\n")
                
                for section in chapter.sections:
                    f.write(f"- {section.title}\n")
                
                f.write("\n")
            
            f.write(f"\nTotal Chapters: {outline.total_chapters}\n")
        
        # Save to JSON file for reference
        with open("book_outline.json", "w") as f:
            json.dump(outline.model_dump(), f, indent=2)
        
        print("Outline saved to book_outline.md and book_outline.json")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()