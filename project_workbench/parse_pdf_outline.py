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

def parse_pdf_content(content: str):
    """
    Parse the PDF content into a structured outline.
    
    Args:
        content: The text content of the PDF file.
        
    Returns:
        A dictionary with total_chapters and chapters list.
    """
    lines = content.strip().split('\n')
    chapters = []
    current_chapter = None
    
    # Regular expressions for identifying different parts of the outline
    chapter_pattern = re.compile(r'^Chapter (\d+): (.+)$')
    section_pattern = re.compile(r'^- (.+?)(?:: (.+))?$')
    
    for line in lines:
        line = line.strip()
        
        # Skip empty lines and the title
        if not line or line == "Expanded Outline - ChatGPT for Business" or line == "Introduction":
            continue
            
        # Check if this is a chapter heading
        chapter_match = chapter_pattern.match(line)
        if chapter_match:
            if current_chapter:
                chapters.append(current_chapter)
            
            current_chapter = {
                "title": chapter_match.group(2),
                "sections": []
            }
            continue
        
        # Check if this is a section
        section_match = section_pattern.match(line)
        if section_match and current_chapter:
            section_type = section_match.group(1).strip()
            
            # Handle different section types
            if section_type.startswith("Theme:"):
                # Add theme as the first section (introduction)
                current_chapter["sections"].append({
                    "title": f"Theme: {section_type.replace('Theme:', '').strip()} (Introduction)"
                })
            elif section_type.startswith("Original Stories:"):
                # Split stories into individual sections
                stories = section_type.replace("Original Stories:", "").strip().split(", ")
                for story in stories:
                    current_chapter["sections"].append({
                        "title": f"Story: {story} (Story)"
                    })
            elif section_type.startswith("Topic Explanations:"):
                # Split topic explanations into individual sections
                topics = section_type.replace("Topic Explanations:", "").strip().split(", ")
                for topic in topics:
                    current_chapter["sections"].append({
                        "title": f"{topic} (Topic Explanation)"
                    })
            elif section_type.startswith("Bonus Topics:"):
                # Split bonus topics into individual sections
                bonuses = section_type.replace("Bonus Topics:", "").strip().split(", ")
                for bonus in bonuses:
                    current_chapter["sections"].append({
                        "title": f"{bonus} (Bonus Topic)"
                    })
            elif section_type.startswith("Big Box:"):
                # Add big box as a technical section
                current_chapter["sections"].append({
                    "title": f"{section_type.replace('Big Box:', '').strip()} (Big Box)"
                })
            elif section_type.startswith("Outro:"):
                # Add outro as the last section
                current_chapter["sections"].append({
                    "title": f"{section_type.replace('Outro:', '').strip()} (Chapter Summary)"
                })
    
    # Add the last chapter
    if current_chapter:
        chapters.append(current_chapter)
    
    return {
        "total_chapters": len(chapters),
        "chapters": chapters
    }

def main():
    # Read the text file instead of PDF
    txt_path = "ChatGPT_for_Business_Expanded_Outline.txt"
    print(f"Reading text file: {txt_path}")
    
    try:
        with open(txt_path, 'r') as f:
            txt_content = f.read()
        
        # Parse the text content
        parsed_outline = parse_pdf_content(txt_content)
        
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