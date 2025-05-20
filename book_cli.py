#!/usr/bin/env python
import os
import sys
import json
import time
import argparse
import subprocess
from typing import List, Optional, Dict, Any
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
# Set the root logger level to INFO to capture all module logs
logging.getLogger().setLevel(logging.INFO)
logger = logging.getLogger("book_cli")

def ensure_output_dirs():
    """Ensure output directories exist"""
    os.makedirs("output/outlines", exist_ok=True)
    os.makedirs("output/chapters", exist_ok=True)
    os.makedirs("output/research", exist_ok=True)

def run_command(command):
    """Run a command and return its output"""
    logging.info(f"Running command: {' '.join(command)}")
    # Don't capture output so it's displayed in the terminal
    result = subprocess.run(command)
    if result.returncode != 0:
        logging.info(f"Error running command (exit code {result.returncode})")
        return None
    return "Command executed successfully"

def copy_file(src, dest):
    """Copy a file from src to dest"""
    logging.info(f"Copying {src} to {dest}")
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with open(src, 'r') as src_file:
        content = src_file.read()
    with open(dest, 'w') as dest_file:
        dest_file.write(content)

def extract_chapter_from_outline(outline_path, chapter_index, output_prefix):
    """Extract a single chapter from a book outline"""
    try:
        with open(outline_path, 'r') as f:
            outline = json.load(f)
        
        chapters = outline.get("chapters", [])
        if not chapters or chapter_index >= len(chapters):
            logging.info(f"Chapter {chapter_index+1} not found in outline")
            return None
        
        chapter = chapters[chapter_index]
        
        # Create a single-chapter outline
        chapter_outline = {
            "total_chapters": 1,
            "chapters": [chapter]
        }
        
        # Save to JSON
        json_path = f"output/outlines/{output_prefix}_outline.json"
        with open(json_path, "w") as f:
            json.dump(chapter_outline, f, indent=2)
        
        # Save to Markdown
        md_path = f"output/outlines/{output_prefix}_outline.md"
        with open(md_path, "w") as f:
            f.write(f"# Chapter {chapter_index+1} Outline: {chapter['title']}\n\n")
            
            for section in chapter.get("sections", []):
                f.write(f"- {section['title']}\n")
            
            f.write("\n")
        
        logging.info(f"Chapter outline saved to {json_path} and {md_path}")
        return chapter_outline
    
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logging.info(f"Error loading outline: {e}")
        return None


def generate_full_outline():
    """Generate a full book outline"""
    logger.info("Generating full book outline...")
    start_time = time.time()
    
    # Log the command we're about to run
    logger.info("Running: python src/book_writing_flow/main.py")
    result = run_command(["python", "src/book_writing_flow/main.py"])
    if result:
        logger.info("Command output length: " + str(len(result)))
    
    outline_time = time.time() - start_time
    logger.info(f"Outline generation took {outline_time:.2f} seconds")
    
    # Check if the outline files were generated successfully
    if os.path.exists("output/outlines/book_outline.json"):
        logger.info("Book outline JSON file generated successfully")
    else:
        logger.warning("output/outlines/book_outline.json not found after generation")
        
    if os.path.exists("output/outlines/book_outline.md"):
        logger.info("Book outline markdown file generated successfully")
    else:
        logger.warning("output/outlines/book_outline.md not found after generation")


def generate_full_outline_and_extract_chapter(chapter_num):
    """Generate a full book outline and extract a specific chapter"""
    # First generate the full outline
    generate_full_outline()
    
    # Then extract the specific chapter
    logger.info(f"Extracting chapter {chapter_num}...")
    start_time = time.time()
    
    # Check if the outline file exists
    if not os.path.exists("output/outlines/book_outline.json"):
        logger.error("Cannot extract chapter: book_outline.json not found")
        return False
    
    # Log the outline file size
    outline_size = os.path.getsize("output/outlines/book_outline.json")
    logger.info(f"book_outline.json size: {outline_size} bytes")
    
    # Extract the chapter
    result = extract_chapter_from_outline(
        "output/outlines/book_outline.json",
        chapter_num - 1,
        f"chapter{chapter_num}"
    )
    
    if result:
        logger.info(f"Successfully extracted chapter {chapter_num}")
    else:
        logger.error(f"Failed to extract chapter {chapter_num}")
    
    extract_time = time.time() - start_time
    logger.info(f"Chapter extraction took {extract_time:.2f} seconds")
    return result is not None

def main():
    """Main entry point for the CLI"""
    parser = argparse.ArgumentParser(description="Book Writing Flow CLI")
    logging.info("✅ CLI CALLED")
    
    # Get the Python executable path once
    python_exe = sys.executable
    
    # Command subparsers
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Outline command
    outline_parser = subparsers.add_parser("outline", help="Generate book outline")
    outline_parser.add_argument("--topic", type=str, default="ChatGPT for Business",
                               help="Book topic")
    outline_parser.add_argument("--chapter", type=int,
                               help="Generate outline for specific chapter (1-based)")
    outline_parser.add_argument("--use-existing", action="store_true",
                               help="Use existing book_outline.json if available instead of regenerating")
    
    # Write command
    write_parser = subparsers.add_parser("write", help="Generate chapter content")
    write_parser.add_argument("--chapter", type=int, required=True, 
                             help="Chapter number to generate (1-based)")
    write_parser.add_argument("--force", action="store_true",
                             help="Force regeneration even if chapter already exists")
    
    # Full flow command
    flow_parser = subparsers.add_parser("flow", help="Run full book writing flow")
    flow_parser.add_argument("--chapters", type=str, default="all",
                            help="Chapters to generate (comma-separated numbers or 'all')")
    flow_parser.add_argument("--topic", type=str, default="ChatGPT for Business", 
                            help="Book topic")
    
    # Parse arguments
    args = parser.parse_args()
    
    # Ensure output directories exist
    ensure_output_dirs()
    
    if args.command == "outline":
        # If a specific chapter was requested, generate just that chapter
        if args.chapter:
            logger.info(f"Generating outline for chapter {args.chapter} only...")
            start_time = time.time()
            
            # Import the function directly from main.py
            try:
                # Add the src directory to the Python path
                sys.path.insert(0, os.path.abspath("."))
                
                # Import the function
                from src.book_writing_flow.main import generate_single_chapter_outline
                
                # Call the function directly
                logger.info(f"Calling generate_single_chapter_outline({args.chapter})")
                result = generate_single_chapter_outline(args.chapter)
                
                if result:
                    logger.info(f"Successfully generated outline for chapter {args.chapter}")
                    
                    # Files are now saved directly to the output directory
                    logger.info(f"Chapter outline files saved directly to output/outlines/chapter{args.chapter}_outline.json and output/outlines/chapter{args.chapter}_outline.md")
                else:
                    logger.error(f"Failed to generate outline for chapter {args.chapter}")
                
            except ImportError as e:
                logger.error(f"Error importing from main.py: {e}")
                logger.error("Falling back to full outline generation and extraction")
                
                # Fall back to the old method
                generate_full_outline_and_extract_chapter(args.chapter)
            
            outline_time = time.time() - start_time
            logger.info(f"Chapter outline generation took {outline_time:.2f} seconds")
        else:
            # Generate full book outline
            generate_full_outline()
    
    elif args.command == "write":
        # Use the run_chapter.py script to generate the chapter with the enhanced writer crew
        logging.info("✅ run_chapter.py CALLED")
        
        cmd = [python_exe, "run_chapter.py", str(args.chapter)]
        if args.force:
            cmd.append("--force")
        
        run_command(cmd)
        # The run_chapter.py script now handles copying to the output directory
    
    elif args.command == "flow":
        # First generate the outline
        logging.info("Generating book outline...")
        run_command([python_exe, "src/book_writing_flow/main.py"])
        
        # Check if the outline files were generated successfully
        if os.path.exists("output/outlines/book_outline.json"):
            logging.info("Book outline JSON file generated successfully")
        else:
            logging.info("output/outlines/book_outline.json not found after generation")
            
        if os.path.exists("output/outlines/book_outline.md"):
            logging.info("Book outline markdown file generated successfully")
        else:
            logging.info("output/outlines/book_outline.md not found after generation")
        
        # Load the outline to determine which chapters to generate
        try:
            with open("output/outlines/book_outline.json", "r") as f:
                outline = json.load(f)
            
            total_chapters = outline.get("total_chapters", 0)
            
            # Determine which chapters to generate
            chapters_to_generate = []
            if args.chapters == "all":
                chapters_to_generate = list(range(1, total_chapters + 1))
            else:
                try:
                    # Parse comma-separated chapter numbers (1-based)
                    chapters_to_generate = [int(c.strip()) for c in args.chapters.split(",")]
                except ValueError:
                    logging.info(f"Invalid chapter numbers: {args.chapters}")
                    return
            
            # Generate each chapter
            for chapter_num in chapters_to_generate:
                logging.info(f"Generating chapter {chapter_num}...")
                run_command([python_exe, "run_chapter.py", str(chapter_num)])
                
                # The run_chapter.py script now handles copying to the output directory
        
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logging.info(f"Error loading outline: {e}")
            return
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()