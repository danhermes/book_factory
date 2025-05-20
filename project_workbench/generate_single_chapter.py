#!/usr/bin/env python
import os
import asyncio
import json
from pydantic import BaseModel

from book_writing_flow.crews.Writer_crew.writer_crew import ChapterWriterCrew
from book_writing_flow.crews.Outline_crew.outline_crew import OutlineCrew
from dotenv import load_dotenv
import logging

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class Section(BaseModel):
    title: str = ""
    content: str = ""

class Chapter(BaseModel):
    title: str = ""
    content: str = ""
    sections: list[Section] = []

async def generate_single_chapter(chapter_index=0):
    """Generate a single chapter based on the outline"""
    print(f"Generating chapter {chapter_index+1}")
    
    # Create chapters directory if it doesn't exist
    if not os.path.exists("output/chapters"):
        os.makedirs("output/chapters")
    
    # Load the outline from output/outlines directory
    print("Loading outline...")
    try:
        # First try to load from output/outlines directory
        if os.path.exists("output/outlines/book_outline.json"):
            with open("output/outlines/book_outline.json", "r") as f:
                outline = json.load(f)
                print(f"Loaded outline from output/outlines/book_outline.json with {len(outline.get('chapters', []))} chapters")
        # Fall back to root directory if not found in output/outlines
        elif os.path.exists("book_outline.json"):
            with open("book_outline.json", "r") as f:
                outline = json.load(f)
                print(f"Loaded outline from book_outline.json with {len(outline.get('chapters', []))} chapters")
        else:
            raise FileNotFoundError("book_outline.json not found in output/outlines or root directory")
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading outline: {e}")
        print("Please make sure book_outline.json exists and is valid in either output/outlines or root directory")
        return
    
    # Get the chapter title
    chapters = outline.get("chapters", [])
    if not chapters or chapter_index >= len(chapters):
        print(f"Chapter {chapter_index+1} not found in outline")
        return
    
    chapter_title = chapters[chapter_index]["title"]
    print(f"Found chapter title: {chapter_title}")
    
    # Create a safe filename
    safe_title = chapter_title.replace(' ', '_').replace(':', '_').replace('/', '_').replace('\\', '_')
    chapter_file = f"chapters/{chapter_index+1:02d}_{safe_title}.md"
    
    # Check if chapter already exists
    if os.path.exists(chapter_file):
        logging.info(f"Chapter {chapter_index+1} already exists at {chapter_file}")
        return
    
    # Generate the chapter
    logging.info(f"GENERATE_SINGLE_CHAPTER: Generating single chapter {chapter_index+1}: {chapter_title}")
    try:
        result = (
            ChapterWriterCrew()
            .crew()
            .kickoff(inputs={
                "title": chapter_title,
                "topic": "ChatGPT for Business",
                "chapters": [chapter["title"] for chapter in chapters]
            })
        )
    except Exception as e:
        print(f"Error generating chapter: {e}")
        return
    
    # Save the chapter
    chapter = result.pydantic
    with open(chapter_file, "w") as f:
        f.write("# " + chapter.title + "\n")
        f.write(chapter.content + "\n")
    
    print(f"Successfully generated and saved chapter {chapter_index+1} to {chapter_file}")
    return chapter

if __name__ == "__main__":
    # Run the first chapter (index 0)
    asyncio.run(generate_single_chapter(0))