#!/usr/bin/env python
import os
import sys
import json
import re
import argparse
import logging
from typing import List, Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("simple_research_verify")

def check_research_log_exists(chapter_num: int) -> bool:
    """Check if a research log file exists for the given chapter."""
    research_dir = "output/research"
    if not os.path.exists(research_dir):
        logger.error(f"Research directory {research_dir} does not exist")
        return False
    
    # Look for research log files for this chapter
    research_files = [f for f in os.listdir(research_dir) if f.startswith(f"chapter_{chapter_num}_") and f.endswith("_research.md")]
    
    if not research_files:
        logger.warning(f"No research log file found for chapter {chapter_num}")
        return False
    
    logger.info(f"Found research log file(s) for chapter {chapter_num}: {research_files}")
    return True

def check_research_in_writer_prompt(chapter_num: int) -> bool:
    """Check if research is being passed to the writer agent in the prompt."""
    # Look for the writer crew log file
    log_dir = "logs"
    if not os.path.exists(log_dir):
        logger.error(f"Log directory {log_dir} does not exist")
        return False
    
    # Find the most recent log file for this chapter
    log_files = [f for f in os.listdir(log_dir) if f.endswith(".log")]
    if not log_files:
        logger.error("No log files found")
        return False
    
    # Sort by modification time (newest first)
    log_files.sort(key=lambda x: os.path.getmtime(os.path.join(log_dir, x)), reverse=True)
    
    # Look for research in the most recent log file
    for log_file in log_files:
        with open(os.path.join(log_dir, log_file), 'r') as f:
            content = f.read()
            
            # Look for research being passed to the writer agent
            if f"chapter_{chapter_num}" in content and "research" in content.lower():
                logger.info(f"Found research being passed to writer agent in log file {log_file}")
                return True
    
    logger.warning(f"No evidence of research being passed to writer agent for chapter {chapter_num}")
    return False

def check_research_in_chapter(chapter_num: int) -> bool:
    """Check if research findings are used in the chapter content."""
    # Look for the chapter file
    chapter_dir = "output/chapters"
    if not os.path.exists(chapter_dir):
        logger.error(f"Chapter directory {chapter_dir} does not exist")
        return False
    
    chapter_file = os.path.join(chapter_dir, f"chapter_{chapter_num}.md")
    if not os.path.exists(chapter_file):
        logger.error(f"Chapter file {chapter_file} does not exist")
        return False
    
    # Look for the research log file
    research_dir = "output/research"
    research_files = [f for f in os.listdir(research_dir) if f.startswith(f"chapter_{chapter_num}_") and f.endswith("_research.md")]
    
    if not research_files:
        logger.warning(f"No research log file found for chapter {chapter_num}")
        return False
    
    research_file = os.path.join(research_dir, research_files[0])
    
    # Extract research findings
    with open(research_file, 'r') as f:
        research_content = f.read()
    
    # Extract key phrases from research findings
    key_phrases = []
    findings_pattern = r"- Finding: (.*?)(?=\n  - Usage:|$)"
    findings = re.findall(findings_pattern, research_content, re.DOTALL)
    
    for finding in findings:
        # Extract key phrases (3-5 word sequences)
        words = finding.split()
        for i in range(len(words) - 2):
            for j in range(3, min(6, len(words) - i + 1)):
                phrase = " ".join(words[i:i+j])
                if len(phrase) > 10:  # Only include phrases with more than 10 characters
                    key_phrases.append(phrase)
    
    # Read chapter content
    with open(chapter_file, 'r') as f:
        chapter_content = f.read()
    
    # Check if any key phrases are used in the chapter
    used_phrases = []
    for phrase in key_phrases:
        if phrase.lower() in chapter_content.lower():
            used_phrases.append(phrase)
    
    if used_phrases:
        logger.info(f"Found {len(used_phrases)} research phrases used in chapter {chapter_num}")
        logger.info(f"Example phrases: {used_phrases[:3]}")
        return True
    
    logger.warning(f"No evidence of research findings being used in chapter {chapter_num}")
    return False

def verify_chapter_research(chapter_num: int) -> Dict[str, Any]:
    """Verify that research is being used for a specific chapter."""
    results = {
        "chapter": chapter_num,
        "research_log_exists": False,
        "research_in_writer_prompt": False,
        "research_in_chapter": False,
        "overall_verification": False
    }
    
    # Check if research log exists
    results["research_log_exists"] = check_research_log_exists(chapter_num)
    
    # Check if research is being passed to the writer agent
    results["research_in_writer_prompt"] = check_research_in_writer_prompt(chapter_num)
    
    # Check if research findings are used in the chapter
    results["research_in_chapter"] = check_research_in_chapter(chapter_num)
    
    # Overall verification
    results["overall_verification"] = results["research_log_exists"] and (results["research_in_writer_prompt"] or results["research_in_chapter"])
    
    return results

def verify_all_chapters() -> Dict[str, Any]:
    """Verify research usage for all chapters."""
    # Find all chapter files
    chapter_dir = "output/chapters"
    if not os.path.exists(chapter_dir):
        logger.error(f"Chapter directory {chapter_dir} does not exist")
        return {"error": "Chapter directory does not exist"}
    
    chapter_files = [f for f in os.listdir(chapter_dir) if f.startswith("chapter_") and f.endswith(".md")]
    
    if not chapter_files:
        logger.error("No chapter files found")
        return {"error": "No chapter files found"}
    
    # Extract chapter numbers
    chapter_nums = []
    for chapter_file in chapter_files:
        match = re.search(r"chapter_(\d+)", chapter_file)
        if match:
            chapter_nums.append(int(match.group(1)))
    
    # Verify each chapter
    results = {}
    for chapter_num in sorted(chapter_nums):
        logger.info(f"Verifying research for chapter {chapter_num}")
        results[chapter_num] = verify_chapter_research(chapter_num)
    
    return results

def print_results(results: Dict[str, Any]) -> None:
    """Print verification results."""
    if "error" in results:
        logger.error(f"Error: {results['error']}")
        return
    
    print("\nResearch Verification Results:")
    print("=" * 50)
    
    for chapter_num, chapter_results in sorted(results.items()):
        print(f"\nChapter {chapter_num}:")
        print(f"  Research Log Exists: {'✅' if chapter_results['research_log_exists'] else '❌'}")
        print(f"  Research in Writer Prompt: {'✅' if chapter_results['research_in_writer_prompt'] else '❌'}")
        print(f"  Research in Chapter: {'✅' if chapter_results['research_in_chapter'] else '❌'}")
        print(f"  Overall Verification: {'✅' if chapter_results['overall_verification'] else '❌'}")
    
    # Calculate overall statistics
    total_chapters = len(results)
    verified_chapters = sum(1 for r in results.values() if r["overall_verification"])
    
    print("\nOverall Statistics:")
    print(f"  Total Chapters: {total_chapters}")
    print(f"  Verified Chapters: {verified_chapters}")
    print(f"  Verification Rate: {verified_chapters/total_chapters:.2%}")

def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="Verify that research is being used in the book chapters")
    parser.add_argument("--chapter", type=int, help="Chapter number to verify")
    
    args = parser.parse_args()
    
    if args.chapter:
        # Verify a specific chapter
        results = verify_chapter_research(args.chapter)
        print_results({args.chapter: results})
    else:
        # Verify all chapters
        results = verify_all_chapters()
        print_results(results)

if __name__ == "__main__":
    main() 