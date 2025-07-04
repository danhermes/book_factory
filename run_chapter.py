#!/usr/bin/env python
import os
import re
import sys
import json
import asyncio
import argparse
import logging
import datetime
import yaml
from datetime import datetime
from zoneinfo import ZoneInfo
from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import SerperDevTool
from pydantic import BaseModel
from src.book_writing_flow.crews.Writer_crew.writer_crew import ChapterWriterCrew
from src.book_writing_flow.crews.Writer_crew.writer_crew import write_chapter_task
from sanitize_markdown import sanitize_markdown
from src.book_writing_flow.book_model import Chapter, Section

# Configure basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

llm = LLM(model="gpt-4o")

# Set the root logger level to INFO to capture all module logs
logging.getLogger().setLevel(logging.INFO)
logger = logging.getLogger("run_chapter")

# class Section(BaseModel):
#     """Section of a chapter"""
#     chapter_title : str
#     title: str
#     type: str  # Introduction, Story, Topic Explanation, etc.
#     content: str

# class Chapter(BaseModel):
#     """Chapter of the book"""
#     title: str
#     content: str
#     sections: list[Section] = []

def run_single_chapter(chapter_index=0, force_regenerate=False):
    """Run just a single chapter generation with enhanced RAG content and section guidance"""
    # Create chapters directory if it doesn't exist
    if not os.path.exists("output/chapters"):
        os.makedirs("output/chapters")
    logging.info("✅ run_chapter.py STARTED")  # Before anything else

    # Load the outline from output/outlines directory
    try:
        # First try to load from output/outlines directory
        if os.path.exists("output/outlines/book_outline.json"):
            with open("output/outlines/book_outline.json", "r") as f:
                outline = json.load(f)
                logging.info(f"Loaded outline from output/outlines/book_outline.json with {len(outline.get('chapters', []))} chapters")
        # Fall back to root directory if not found in output/outlines
        elif os.path.exists("book_outline.json"):
            with open("book_outline.json", "r") as f:
                outline = json.load(f)
                logging.info(f"Loaded outline from book_outline.json with {len(outline.get('chapters', []))} chapters")
        else:
            raise FileNotFoundError("book_outline.json not found in output/outlines or root directory")
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logging.info(f"Error loading outline: {e}")
        logging.info("Please make sure book_outline.json exists and is valid in either output/outlines or root directory")
        return
    
    # Get the chapter title
    chapters = outline.get("chapters", [])
    if not chapters or chapter_index >= len(chapters):
        logging.info(f"Chapter {chapter_index+1} not found in outline")
        return
    
    chapter_title = chapters[chapter_index]["title"]
    logging.info(f"Found chapter title: {chapter_title}")
    
    # Create a safe filename
    safe_title = chapter_title.replace(' ', '_').replace(':', '_').replace('/', '_').replace('\\', '_')
    chapter_file = f"output/chapters/{chapter_index+1:02d}_{safe_title}.md"
    
    # Check if chapter already exists
    if os.path.exists(chapter_file) and not force_regenerate:
        logging.info(f"Chapter {chapter_index+1} already exists at {chapter_file}")
        return
    
    if force_regenerate and os.path.exists(chapter_file):
        logging.info(f"Forcing regeneration of chapter {chapter_index+1}")
    
    logging.info(f"RUN_SINGLE_CHAPTER: Generating chapter {chapter_index+1}: {chapter_title}")
    
    # Generate the chapter
    try:
        # Research the chapter topics
        # crew for chapter research only - not used for chapter writing
        crew = ChapterWriterCrew(chapter_number=chapter_index+1, chapter_title=chapter_title).crew()       

        logging.info(f"RUN_SINGLE_CHAPTER: Crew created")
        chapter_data = chapters[chapter_index]

        result = crew.kickoff(inputs={
            "title": chapter_title,
            "topic": "ChatGPT for Business: How to Create Powerful AI Workflows",
            "chapters": [chapter["title"] for chapter in chapters],
            "outline_sections": [section.get("section_title", "") for section in chapter_data.get("sections", [])]
        })
        
    
        logging.info(f"Checking result.pydantic: {hasattr(result, 'pydantic')}")
        if hasattr(result, 'pydantic'):
            logging.info(f"Result.pydantic type: {type(result.pydantic)}")
            logging.info(f"Result.pydantic value: {result.pydantic}")
        else:
            logging.info("Result has no pydantic attribute, checking raw")
        if hasattr(result, 'raw'):
            logging.info(f"Result.raw type: {type(result.raw)}")
            logging.info(f"Result.raw value: {result.raw}")
        else:
            logging.info("Result has no raw attribute either")

        # Extract the research content
        if result.pydantic:
            research_content = result.pydantic
        elif hasattr(result, 'raw') and result.raw:
            research_content = result.raw
        else:
            research_content = ""


        # Ensure research directory exists
        os.makedirs("output/research", exist_ok=True)
        chapter_number = 1  # Default to chapter 1
        
        # Try to extract chapter number from title
        match = re.search(r"Chapter (\d+)", chapter_title)
        if match:
            chapter_number = int(match.group(1))
                
        # Create a research log file for this chapter
        safe_title = chapter_title.replace(' ', '_').replace(':', '_').replace('/', '_').replace('\\', '_')
        research_log_file = f"output/research/{chapter_number:02d}_{safe_title}_research.md"
        
        logging.info(f"Research content type: {type(research_content)}")
        logging.info(f"Research content length: {len(str(research_content))}")
        logging.info(f"First 100 chars of research content: {str(research_content)[:100]}")


        # Check if research file already exists and has content
        # if os.path.exists(research_log_file) and os.path.getsize(research_log_file) > 0:
        #     logger.info(f"Research file already exists: {research_log_file}")

        # Save research results to file
        with open(research_log_file, "w", encoding="utf-8") as f:
                f.write(f"# Research for Chapter {chapter_index+1}: {chapter_title}\n\n")
                local_time = datetime.now(ZoneInfo("America/New_York"))
                f.write(f"Generated on: {local_time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                f.write("## Research Findings\n\n")
                f.write(research_content)
            
        logger.info(f"Research completed and saved to {research_log_file}")
        
        # Print the outline sections for debugging
        logging.info(f"Generating chapter with these sections:")
        for section in chapter_data.get("sections", []):
            logging.info(f"- {section.get('title', '')}")
        
        logging.info("🚀 Launching chapter crew with:")
        logging.info("  Chapter title: %s", chapter_title)
        logging.info("  Chapters: %s", [chapter["title"] for chapter in chapters])
        logging.info("  Outline sections: %s", [section.get("title", "") for section in chapter_data.get("sections", [])])
        
        with open("src/book_writing_flow/crews/Writer_crew/config/agents.yaml", "r") as f:
            agents_config = yaml.safe_load(f)

        with open("src/book_writing_flow/crews/Writer_crew/config/tasks.yaml", "r") as f:
            tasks_config = yaml.safe_load(f)

        # agents = {}
        # agents = {
        # "section_writer": Agent(
        #     config=agents_config["section_writer"],
        #     llm=llm,
        #     verbose=True
        # ),
        # "writer": Agent(
        #     config=agents_config["writer"],
        #     llm=llm,
        #     verbose=True
        # ),
        # "topic_researcher": Agent(
        #     config=agents_config["topic_researcher"],
        #     llm=llm,
        #     verbose=True
        # )}

        # # Create context items from inputs
        # context_items = []
        # for key, value in {
        #     "chapter_title": chapter_title,
        #     "title": chapter_title,
        #     "tasks_config": tasks_config,
        #     "agents": agents,
        #     "chapters": [chapter["title"] for chapter in chapters],
        #     "outline_sections": [section.get("title", "") for section in chapter_data.get("sections", [])]
        # }.items():
        #     context_items.append({
        #         "key": key,
        #         "value": value,
        #         "description": f"Input for {key}"
        #     })
        logging.info(f"Define write_chapter_task")

        task = write_chapter_task(
            description=tasks_config["write_section"]["description"],
            expected_output=tasks_config["write_section"]["expected_output"],
            config=agents_config,
            research_content=research_content,
            chapter_title=chapter_title,
            chapter_number=chapter_index+1
        )

        # task = write_chapter_task(
        #     #description=tasks_config["write_chapter"]["description"], #f"Write chapter {chapter_title} using the outline",
        #     #expected_output=tasks_config["write_chapter"]["expected_output"], #"A completed chapter object with full sections",
        #     tasks=tasks_config,              # output_pydantic=Chapter,
        #     agents=agents_config,            # inputs={ #???????????????????????????????????????????????? necessary?
        #     research_content=research_content
        #     # "chapter_title": chapter_title,
        #     # "title": chapter_title,
        #     # "topic": "ChatGPT for Business",
        #     # inputs={
        #     #   "agents": agents_config["chapter_writer"]            
        #     # }
        #     #"chapters": [chapter["title"] for chapter in chapters],
        #     #"outline_sections": [section.get("title", "") for section in chapter_data.get("sections", [])]
        #     #}
        #     # "chapters": [chapter["title"] for chapter in chapters],
        #     # "outline_sections": [section.get("title", "") for section in chapter_data.get("sections", [])]
        #     # }
        #     )
        
        logging.info("🚀 Crew finished successfully!")

        # Extract the chapter content
        import asyncio
        chapter_result = asyncio.run(task.execute())
        chapter = chapter_result #result.pydantic
        logging.info(f"Chapter ---------------------------------")
        logging.info(f"Chapter content: {chapter.content}")
        logging.info(f"Chapter sections: {len(chapter.sections)}")
        logging.info(f"Chapter +++++++++++++++++++++++++++++++++")
        logging.info(f"Sanitize chapter")
        # Sanitize the chapter content
        chapter.content = sanitize_markdown(chapter.content)
        # Copy to output directory
        os.makedirs("output/chapters", exist_ok=True)
        output_file = f"output/chapters/{chapter_index+1:02d}_{safe_title}.md"
        logging.info(f"Save chapter to {output_file}")
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(chapter.content + "\n\n")
        
        logging.info(f"Successfully generated and saved chapter {chapter_index+1} to {chapter_file}")
    except Exception as e:
        logging.info(f"Error generating chapter: {e}")
        try:
            k = 1
    
        except Exception as e2:
            print(f"Error in retry attempt: {e2}")
            return None

if __name__ == "__main__":
    # Parse command line arguments
    logging.info("✅ Run_chapter.py STARTED")
    parser = argparse.ArgumentParser(description="Generate a book chapter with enhanced RAG content and section guidance")
    parser.add_argument("chapter", type=int, nargs="?", default=1,
                        help="Chapter number to generate (1-based)")
    parser.add_argument("--force", "-f", action="store_true",
                        help="Force regeneration even if chapter already exists")
    
    args = parser.parse_args()
    
    # Check for --force flag in sys.argv for backward compatibility with book_cli.py
    force_regenerate = args.force or "--force" in sys.argv
    
    # Run the specified chapter
    run_single_chapter(args.chapter - 1, force_regenerate)