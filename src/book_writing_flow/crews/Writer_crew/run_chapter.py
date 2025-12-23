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
from logging.handlers import RotatingFileHandler

# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)

# Clear existing log files at the start of each run
log_files = ['../../../logs/run_chapter.log', '../../../logs/writer_crew.log']
for log_file in log_files:
    if os.path.exists(log_file):
        try:
            with open(log_file, 'w') as f:
                f.write('')  # Clear the file
            print(f"Cleared log file: {log_file}")
        except Exception as e:
            print(f"Warning: Could not clear log file {log_file}: {e}")

# Reconfigure stdout to UTF-8 to support emojis (Windows fix)
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')  # Optional but safer

# Set up logging with UTF-8-safe stream
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),  # Force UTF-8-capable stream
        logging.FileHandler('logs/run_chapter.log', encoding='utf-8')  # Also ensure file handles UTF-8
    ]
)

# Set the root logger level to INFO to capture all module logs
logging.getLogger().setLevel(logging.INFO)
logger = logging.getLogger("run_chapter")

from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import SerperDevTool
from pydantic import BaseModel
from src.book_writing_flow.crews.Writer_crew.writer_crew import ChapterWriterCrew
from src.book_writing_flow.crews.Writer_crew.writer_crew import write_chapter_task
from sanitize_markdown import sanitize_markdown
from src.book_writing_flow.book_model import Chapter, Section
from src.book_writing_flow.tools.context7_mcp import Context7_MCP

llm = LLM(model="gpt-4o")

async def run_single_chapter(chapter_index=0, force_regenerate=False):
    """Run just a single chapter generation with enhanced RAG content and section guidance"""
    # Create chapters directory if it doesn't exist
    if not os.path.exists("output/chapters"):
        os.makedirs("output/chapters")
    logging.info("✅ run_chapter.py STARTED")  # Before anything else

    # Initialize Context7 MCP
    context7 = Context7_MCP(binary="node", package="./src/book_writing_flow/tools/context7.js")

    # Load the outline from output/rag directory (contains tools, descriptions, stories)
    try:
        with open("output/rag/book_outline.json", "r") as f:
            outline = json.load(f)
            logging.info(f"Loaded outline from output/rag/book_outline.json with {len(outline.get('chapters', []))} chapters")
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logging.error(f"Error loading outline: {e}")
        raise RuntimeError("output/rag/book_outline.json is required (contains tools, descriptions, stories)")
    
    # Extract tools from chapter sections in the outline
    chapter_tools = []
    chapters = outline.get("chapters", [])
    if chapters and chapter_index < len(chapters):
        chapter_data = chapters[chapter_index]
        for section in chapter_data.get("sections", []):
            section_tools = section.get("tools", [])
            for tool in section_tools:
                if tool and tool not in chapter_tools:
                    chapter_tools.append(tool)
        logging.info(f"Extracted {len(chapter_tools)} unique tools from chapter {chapter_index + 1} sections: {chapter_tools}")

    # Get the chapter title
    if not chapters or chapter_index >= len(chapters):
        logging.info(f"Chapter {chapter_index+1} not found in outline")
        return
    
    chapter_data = chapters[chapter_index]
    chapter_title = chapter_data.get("chapter_title") or chapter_data.get("title")
    book_topic = outline.get("topic")

    logging.info(f"Found chapter title: {chapter_title}")
    
    # Create a safe filename
    safe_title = chapter_title.replace(' ', '_').replace(':', '_').replace('/', '_').replace('\\', '_')
    chapter_file = f"output/chapters/{chapter_index+1}_-_{safe_title}.md"
    
    # Check if chapter already exists
    if os.path.exists(chapter_file) and not force_regenerate:
        logging.info(f"Chapter {chapter_index+1} already exists at {chapter_file}")
        return
    
    if force_regenerate and os.path.exists(chapter_file):
        logging.info(f"Forcing regeneration of chapter {chapter_index+1}")
    
    logging.info(f"RUN_SINGLE_CHAPTER: Generating chapter: {chapter_title}")
    
    # Generate the chapter
    try:
        # Research the chapter topics
        # crew for chapter research only - not used for chapter writing
        crew = ChapterWriterCrew(chapter_number=chapter_index+1, chapter_title=chapter_title).crew()       

        logging.info(f"RUN_SINGLE_CHAPTER: Crew created")
        chapter_data = chapters[chapter_index]

        logging.info(f"Load context7 documentation for AI Tools")
        context7_docs = ""
        
        if chapter_tools:
            logging.info(f"Found {len(chapter_tools)} tools for chapter {chapter_index + 1}: {chapter_tools}")
            try:
                logging.info(f"Context7 MCP initialized successfully")
                
                # Use the filtered chapter_tools instead of extracting from content
                for tool in chapter_tools:
                    tool_name = ""
                    try:
                        logging.info(f"Getting Context7 documentation for tool: {tool}")
                        tool_name = tool if isinstance(tool, str) else tool.get('name', '')
                        logging.info(f"Resolved tool name: {tool_name}")
                        
                        tool_docs = context7.get_documentation(tool_name, token_limit=1000)
                        if tool_docs and not tool_docs.startswith("[Context7 ERROR") and not tool_docs.startswith("[Context7] Could not resolve"):
                            context7_docs += f"\n\n## {tool_name} Documentation\n{tool_docs}"
                            logging.info(f"Successfully loaded documentation for {tool_name}: {len(tool_docs)} chars")
                        else:
                            logging.warning(f"Failed to get valid documentation for {tool_name}: {tool_docs}")
                    except Exception as e:
                        logging.error(f"Error getting documentation for {tool_name}: {e}")
                        
            except Exception as e:
                logging.error(f"Error initializing Context7 MCP: {e}")
                context7_docs = ""
        else:
            logging.info("No tools found for this chapter, skipping Context7 documentation")
        
        # Add fallback if no Context7 documentation was loaded
        if not context7_docs:
            context7_docs = f"## AI Tools for Chapter {chapter_index + 1}\n\nNo specific tool documentation available for this chapter."
            logging.info("Using fallback Context7 documentation message")

        logging.info(f"Context7 documentation: {context7_docs[:1000]}")  # Trimmed for preview

        sections_text = "\n\n".join([
            f"Section {section.get('section_number', '')}: {section.get('section_title', '')}\n"
            f"Type: {section.get('type', '')}\n"
            f"Description: {section.get('description', '')}\n"
            f"Story: {section.get('story', '')}\n"
            f"Tools: {', '.join(section.get('tools', []))}"
            for section in chapter_data.get("sections", [])
        ])

        rag_content = ""
        logger.info(f"Research: Load rag_content for chapter: {chapter_title}")
        rag_content = ChapterWriterCrew(chapter_index+1, chapter_title).load_rag_content(chapter_title, chapter_data.get("sections", []))
        logger.info("Research: Successfully loaded RAG content")

        result = crew.kickoff(inputs={
            "title": chapter_title,
            "topic": book_topic,
            "chapters": [chapter.get("chapter_title") or chapter.get("title") for chapter in chapters],
            "sections": sections_text,
            "rag_content": rag_content,
            "context7_docs": context7_docs,
            "required_tools": ", ".join(chapter_tools) if chapter_tools else "No specific tools required"
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

        # Save research results to file
        with open(research_log_file, "w", encoding="utf-8") as f:
                f.write(f"# Research for Chapter {chapter_index+1}: {chapter_title}\n\n")
                try:
                    local_time = datetime.now(ZoneInfo("America/New_York"))
                except:
                    local_time = datetime.now()
                f.write(f"Generated on: {local_time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                f.write("## Research Findings\n\n")
                f.write(research_content)
            
        logger.info(f"Research completed and saved to {research_log_file}")
        
        # Print the outline sections for debugging
        logging.info(f"Generating chapter with these sections:")
        for section in chapter_data.get("sections", []):
            logging.info(f"- {section.get('section_title', '')}")
        
        logging.info("🚀 Launching chapter crew with:")
        logging.info("  Chapter title: %s", chapter_title)
        logging.info("  Chapters: %s", [chapter.get("chapter_title") or chapter.get("title") for chapter in chapters])
        logging.info("  Outline sections: %s", [section.get("section_title", "") for section in chapter_data.get("sections", [])])
        
        with open("src/book_writing_flow/crews/Writer_crew/config/agents.yaml", "r") as f:
            agents_config = yaml.safe_load(f)

        with open("src/book_writing_flow/crews/Writer_crew/config/tasks.yaml", "r") as f:
            tasks_config = yaml.safe_load(f)
        logging.info(f"Define write_chapter_task")

        task = write_chapter_task(
            description=tasks_config["write_section"]["description"],
            expected_output=tasks_config["write_section"]["expected_output"],
            config=agents_config,
            research_content=research_content,
            chapter_title=chapter_title,
            chapter_number=chapter_index+1
        )
        
        logging.info("🚀 Crew finished successfully!")

        # Extract the chapter content
        import asyncio
        chapter_result = await task.execute()
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
        output_file = f"output/chapters/{chapter_index+1}_-_{safe_title}.md"
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
    asyncio.run(run_single_chapter(args.chapter - 1, force_regenerate))