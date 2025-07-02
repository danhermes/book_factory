#!/usr/bin/env python
"""
Example of using book_cli.py programmatically from another Python script
This demonstrates how to integrate book generation into your own applications
"""
import os
import sys
import subprocess
import logging
import json
import time
from typing import Dict, List, Optional, Union, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("programmatic_example")

class BookGenerator:
    """Class for programmatically generating book content"""
    
    def __init__(self, book_topic: str = "ChatGPT for Business"):
        """Initialize the book generator"""
        self.book_topic = book_topic
        self.python_exe = sys.executable
        self.book_cli_path = self._get_book_cli_path()
        self.ensure_output_dirs()
    
    def _get_book_cli_path(self) -> str:
        """Get the path to book_cli.py based on current directory"""
        script_dir = os.path.dirname(os.path.abspath(__file__))
        if os.path.basename(script_dir) == "test":
            # We're in the test directory, so book_cli.py is in the parent directory
            book_cli_path = os.path.join(os.path.dirname(script_dir), "book_cli.py")
        else:
            # We're in some other directory, assume book_cli.py is in the current directory
            book_cli_path = "book_cli.py"
        
        # Make sure the path exists
        if not os.path.exists(book_cli_path):
            logger.error(f"book_cli.py not found at {book_cli_path}")
            raise FileNotFoundError(f"book_cli.py not found at {book_cli_path}")
        
        logger.info(f"Using book_cli.py at: {book_cli_path}")
        return book_cli_path
        
    def ensure_output_dirs(self):
        """Ensure output directories exist"""
        os.makedirs("output/outlines", exist_ok=True)
        os.makedirs("output/chapters", exist_ok=True)
        os.makedirs("output/research", exist_ok=True)
    
    def run_command(self, command: List[str]) -> Optional[str]:
        """Run a command and return its output"""
        logger.info(f"Running command: {' '.join(command)}")
        try:
            result = subprocess.run(
                command, 
                capture_output=True, 
                text=True, 
                check=True
            )
            return result.stdout
        except subprocess.CalledProcessError as e:
            logger.error(f"Command failed with exit code {e.returncode}")
            logger.error(f"Error output: {e.stderr}")
            return None
    
    def generate_outline(self) -> bool:
        """Generate a book outline"""
        logger.info("Generating book outline...")
        start_time = time.time()
        
        result = self.run_command([
            self.python_exe,
            self.book_cli_path,
            "outline",
            "--topic",
            self.book_topic
        ])
        
        success = result is not None
        elapsed_time = time.time() - start_time
        logger.info(f"Outline generation completed in {elapsed_time:.2f} seconds")
        
        # Verify the outline files were created
        if os.path.exists("output/outlines/book_outline.json"):
            logger.info("Book outline JSON file generated successfully")
        else:
            logger.error("Book outline JSON file not found")
            success = False
            
        return success
    
    def generate_chapter_outline(self, chapter_num: int) -> bool:
        """Generate an outline for a specific chapter"""
        logger.info(f"Generating outline for chapter {chapter_num}...")
        start_time = time.time()
        
        result = self.run_command([
            self.python_exe,
            self.book_cli_path,
            "outline",
            "--chapter",
            str(chapter_num)
        ])
        
        success = result is not None
        elapsed_time = time.time() - start_time
        logger.info(f"Chapter outline generation completed in {elapsed_time:.2f} seconds")
        
        # Verify the chapter outline file was created
        chapter_outline_path = f"output/outlines/chapter{chapter_num}_outline.json"
        if os.path.exists(chapter_outline_path):
            logger.info(f"Chapter outline file generated successfully: {chapter_outline_path}")
        else:
            logger.error(f"Chapter outline file not found: {chapter_outline_path}")
            success = False
            
        return success
    
    def write_chapter(self, chapter_num: int, force: bool = False) -> bool:
        """Write a specific chapter"""
        logger.info(f"Writing chapter {chapter_num}...")
        start_time = time.time()
        
        cmd = [
            self.python_exe,
            self.book_cli_path,
            "write",
            "--chapter",
            str(chapter_num)
        ]
        
        if force:
            cmd.append("--force")
            
        result = self.run_command(cmd)
        
        success = result is not None
        elapsed_time = time.time() - start_time
        logger.info(f"Chapter writing completed in {elapsed_time:.2f} seconds")
        
        return success
    
    def run_full_flow(self, chapters: Union[str, List[int]] = "all") -> bool:
        """Run the full book generation flow"""
        logger.info("Running full book generation flow...")
        start_time = time.time()
        
        # Convert list of chapters to string if needed
        if isinstance(chapters, list):
            chapters_str = ",".join(str(c) for c in chapters)
        else:
            chapters_str = chapters
            
        result = self.run_command([
            self.python_exe,
            self.book_cli_path,
            "flow",
            "--chapters",
            chapters_str,
            "--topic",
            self.book_topic
        ])
        
        success = result is not None
        elapsed_time = time.time() - start_time
        logger.info(f"Full flow completed in {elapsed_time:.2f} seconds")
        
        return success
    
    def get_outline_data(self) -> Optional[Dict[str, Any]]:
        """Get the outline data from the JSON file"""
        try:
            with open("output/outlines/book_outline.json", "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"Error loading outline data: {e}")
            return None
    
    def get_chapter_titles(self) -> List[str]:
        """Get the list of chapter titles from the outline"""
        outline_data = self.get_outline_data()
        if not outline_data or "chapters" not in outline_data:
            return []
            
        return [chapter.get("title", f"Chapter {i+1}") 
                for i, chapter in enumerate(outline_data["chapters"])]
    
    def get_chapter_content(self, chapter_num: int) -> Optional[str]:
        """Get the content of a specific chapter"""
        # Find the chapter file
        chapter_files = os.listdir("output/chapters")
        chapter_prefix = f"{chapter_num:02d}_"
        
        matching_files = [f for f in chapter_files if f.startswith(chapter_prefix)]
        if not matching_files:
            logger.error(f"No chapter file found with prefix {chapter_prefix}")
            return None
            
        # Read the chapter content
        try:
            with open(f"output/chapters/{matching_files[0]}", "r") as f:
                return f.read()
        except FileNotFoundError as e:
            logger.error(f"Error reading chapter file: {e}")
            return None


def example_usage():
    """Example of how to use the BookGenerator class"""
    # Create a book generator
    generator = BookGenerator(book_topic="ChatGPT for Business")
    
    # Generate the book outline
    if generator.generate_outline():
        logger.info("Book outline generated successfully")
        
        # Get the chapter titles
        chapter_titles = generator.get_chapter_titles()
        logger.info(f"Book has {len(chapter_titles)} chapters:")
        for i, title in enumerate(chapter_titles, 1):
            logger.info(f"  Chapter {i}: {title}")
        
        # Generate a specific chapter
        chapter_to_generate = 1
        if generator.write_chapter(chapter_to_generate):
            logger.info(f"Chapter {chapter_to_generate} generated successfully")
            
            # Get the chapter content
            content = generator.get_chapter_content(chapter_to_generate)
            if content:
                logger.info(f"Chapter {chapter_to_generate} content length: {len(content)} characters")
                logger.info(f"First 200 characters: {content[:200]}...")
    else:
        logger.error("Failed to generate book outline")


if __name__ == "__main__":
    example_usage()