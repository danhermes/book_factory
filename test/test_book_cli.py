#!/usr/bin/env python
"""
Test script for book_factory CLI
This script demonstrates how to use the book_cli.py to generate book content
"""
import os
import subprocess
import argparse
import time
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("test_book_cli")

# Determine the path to book_cli.py based on current directory
def get_book_cli_path():
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
        return None
    
    logger.info(f"Using book_cli.py at: {book_cli_path}")
    return book_cli_path

def run_command(command, description):
    """Run a command and log the result"""
    logger.info(f"RUNNING: {description}")
    logger.info(f"Command: {' '.join(command)}")
    
    start_time = time.time()
    result = subprocess.run(command, capture_output=True, text=True)
    elapsed_time = time.time() - start_time
    
    logger.info(f"Completed in {elapsed_time:.2f} seconds")
    logger.info(f"Exit code: {result.returncode}")
    
    if result.stdout:
        logger.info(f"Output: {result.stdout[:200]}..." if len(result.stdout) > 200 else f"Output: {result.stdout}")
    
    if result.returncode != 0:
        logger.error(f"Error: {result.stderr}")
        return False
    
    return True

def test_generate_outline():
    """Test generating a book outline"""
    logger.info("=== TESTING OUTLINE GENERATION ===")
    book_cli_path = get_book_cli_path()
    if not book_cli_path:
        return False
    
    return run_command(
        ["python", book_cli_path, "outline"],
        "Generating full book outline"
    )

def test_generate_chapter_outline(chapter_num):
    """Test generating an outline for a specific chapter"""
    logger.info(f"=== TESTING CHAPTER {chapter_num} OUTLINE GENERATION ===")
    book_cli_path = get_book_cli_path()
    if not book_cli_path:
        return False
    
    return run_command(
        ["python", book_cli_path, "outline", "--chapter", str(chapter_num)],
        f"Generating outline for chapter {chapter_num}"
    )

def test_write_chapter(chapter_num, force=False):
    """Test writing a specific chapter"""
    logger.info(f"=== TESTING CHAPTER {chapter_num} WRITING ===")
    book_cli_path = get_book_cli_path()
    if not book_cli_path:
        return False
    
    cmd = ["python", book_cli_path, "write", "--chapter", str(chapter_num)]
    if force:
        cmd.append("--force")
    
    return run_command(
        cmd,
        f"Writing chapter {chapter_num}" + (" (force)" if force else "")
    )

def test_full_flow(chapters="1"):
    """Test the full book writing flow"""
    logger.info("=== TESTING FULL BOOK FLOW ===")
    book_cli_path = get_book_cli_path()
    if not book_cli_path:
        return False
    
    return run_command(
        ["python", book_cli_path, "flow", "--chapters", chapters],
        f"Running full flow for chapters: {chapters}"
    )

def check_output_files():
    """Check if output files were created"""
    logger.info("=== CHECKING OUTPUT FILES ===")
    
    files_to_check = [
        "output/outlines/book_outline.json",
        "output/outlines/book_outline.md"
    ]
    
    for file_path in files_to_check:
        if os.path.exists(file_path):
            size = os.path.getsize(file_path)
            logger.info(f"✅ {file_path} exists ({size} bytes)")
        else:
            logger.error(f"❌ {file_path} does not exist")
    
    # Check for chapter files
    chapter_files = [f for f in os.listdir("output/chapters") if f.endswith(".md")]
    logger.info(f"Found {len(chapter_files)} chapter files in output/chapters/")
    for file in chapter_files[:5]:  # Show first 5 only
        logger.info(f"  - {file}")
    
    if len(chapter_files) > 5:
        logger.info(f"  ... and {len(chapter_files) - 5} more")

def main():
    """Main function to run tests"""
    parser = argparse.ArgumentParser(description="Test the book_cli.py functionality")
    parser.add_argument("--test", choices=["outline", "chapter-outline", "write", "flow", "all"], 
                        default="all", help="Test to run")
    parser.add_argument("--chapter", type=int, default=1, help="Chapter number for chapter-specific tests")
    parser.add_argument("--force", action="store_true", help="Force regeneration of chapters")
    
    args = parser.parse_args()
    
    # Ensure output directories exist
    os.makedirs("output/outlines", exist_ok=True)
    os.makedirs("output/chapters", exist_ok=True)
    os.makedirs("output/research", exist_ok=True)
    
    if args.test == "outline" or args.test == "all":
        test_generate_outline()
        
    if args.test == "chapter-outline" or args.test == "all":
        test_generate_chapter_outline(args.chapter)
        
    if args.test == "write" or args.test == "all":
        test_write_chapter(args.chapter, args.force)
        
    if args.test == "flow" or args.test == "all":
        test_full_flow(str(args.chapter))
    
    # Check output files
    check_output_files()
    
    logger.info("=== TEST COMPLETED ===")

if __name__ == "__main__":
    main()