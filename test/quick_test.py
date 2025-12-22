#!/usr/bin/env python
"""
Quick test script for Book Factory CLI
Run this script to quickly test a specific aspect of the book generation system
"""
import argparse
import logging
import os
import subprocess
import sys
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("quick_test")

def run_test(test_name, chapter=1, force=False):
    """Run a specific test"""
    logger.info(f"Running quick test: {test_name}")
    
    # Ensure output directories exist
    os.makedirs("output/outlines", exist_ok=True)
    os.makedirs("output/chapters", exist_ok=True)
    os.makedirs("output/research", exist_ok=True)
    
    start_time = time.time()
    
    # Determine the path to book_cli.py based on current directory
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
        return False
    
    logger.info(f"Using book_cli.py at: {book_cli_path}")
    
    # Determine the command to run
    if test_name == "outline":
        cmd = ["python", book_cli_path, "outline"]
    elif test_name == "chapter-outline":
        cmd = ["python", book_cli_path, "outline", "--chapter", str(chapter)]
    elif test_name == "write":
        cmd = ["python", book_cli_path, "write", "--chapter", str(chapter)]
        if force:
            cmd.append("--force")
    elif test_name == "flow":
        cmd = ["python", book_cli_path, "flow", "--chapters", str(chapter)]
    else:
        logger.error(f"Unknown test: {test_name}")
        return False
    
    # Run the command
    logger.info(f"Running command: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, check=True)
        logger.info(f"Command completed with exit code: {result.returncode}")
        success = True
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed with exit code: {e.returncode}")
        success = False
    
    elapsed_time = time.time() - start_time
    logger.info(f"Test completed in {elapsed_time:.2f} seconds")
    
    # Check for output files
    if test_name == "outline":
        if os.path.exists("output/outlines/book_outline.json"):
            logger.info("✅ Book outline JSON file generated successfully")
        else:
            logger.error("❌ Book outline JSON file not found")
            success = False
    elif test_name == "chapter-outline":
        if os.path.exists(f"output/outlines/chapter{chapter}_outline.json"):
            logger.info(f"✅ Chapter {chapter} outline JSON file generated successfully")
        else:
            logger.error(f"❌ Chapter {chapter} outline JSON file not found")
            success = False
    elif test_name == "write":
        # Check for chapter files
        chapter_files = [f for f in os.listdir("output/chapters") if f.startswith(f"{chapter:02d}_")]
        if chapter_files:
            logger.info(f"✅ Chapter {chapter} file generated successfully: {chapter_files[0]}")
        else:
            logger.error(f"❌ Chapter {chapter} file not found")
            success = False
    
    return success

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Quick test for Book Factory CLI")
    parser.add_argument("test", choices=["outline", "chapter-outline", "write", "flow"],
                        help="Test to run")
    parser.add_argument("--chapter", type=int, default=1,
                        help="Chapter number (default: 1)")
    parser.add_argument("--force", action="store_true",
                        help="Force regeneration of chapter")
    
    args = parser.parse_args()
    
    success = run_test(args.test, args.chapter, args.force)
    
    if success:
        logger.info("✅ Test completed successfully")
        sys.exit(0)
    else:
        logger.error("❌ Test failed")
        sys.exit(1)

if __name__ == "__main__":
    main()