#!/usr/bin/env python
"""
Analyze Book Factory CLI test results
This script runs a test and analyzes the output
"""
import argparse
import json
import logging
import os
import subprocess
import sys
import time
from typing import Dict, List, Optional, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("analyze_results")

class TestAnalyzer:
    """Class for running tests and analyzing results"""
    
    def __init__(self):
        """Initialize the analyzer"""
        self.python_exe = sys.executable
        self.ensure_output_dirs()
    
    def ensure_output_dirs(self):
        """Ensure output directories exist"""
        os.makedirs("output/outlines", exist_ok=True)
        os.makedirs("output/chapters", exist_ok=True)
        os.makedirs("output/research", exist_ok=True)
        os.makedirs("output/analysis", exist_ok=True)
    
    def run_test(self, test_name: str, chapter: int = 1, force: bool = False) -> Dict[str, Any]:
        """Run a test and capture the results"""
        logger.info(f"Running test: {test_name} for chapter {chapter}")
        
        # Build the command
        cmd = [self.python_exe, "quick_test.py", test_name]
        if test_name in ["chapter-outline", "write", "flow"]:
            cmd.extend(["--chapter", str(chapter)])
        if force and test_name == "write":
            cmd.append("--force")
        
        # Run the command and capture output
        start_time = time.time()
        try:
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                check=True
            )
            success = True
            output = result.stdout
            error = result.stderr
        except subprocess.CalledProcessError as e:
            success = False
            output = e.stdout
            error = e.stderr
        
        elapsed_time = time.time() - start_time
        
        # Return the results
        return {
            "test_name": test_name,
            "chapter": chapter,
            "force": force,
            "success": success,
            "elapsed_time": elapsed_time,
            "output": output,
            "error": error,
            "timestamp": time.time()
        }
    
    def analyze_outline(self, chapter: Optional[int] = None) -> Dict[str, Any]:
        """Analyze the outline file"""
        logger.info("Analyzing outline file")
        
        # Determine which file to analyze
        if chapter is not None:
            outline_path = f"output/outlines/chapter{chapter}_outline.json"
        else:
            outline_path = "output/outlines/book_outline.json"
        
        # Check if the file exists
        if not os.path.exists(outline_path):
            logger.error(f"Outline file not found: {outline_path}")
            return {"error": "Outline file not found"}
        
        # Load the outline
        try:
            with open(outline_path, "r") as f:
                outline = json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing outline file: {e}")
            return {"error": f"Error parsing outline file: {e}"}
        
        # Analyze the outline
        analysis = {
            "file_path": outline_path,
            "file_size": os.path.getsize(outline_path),
            "total_chapters": outline.get("total_chapters", 0),
            "chapters": []
        }
        
        # Analyze each chapter
        for i, chapter_data in enumerate(outline.get("chapters", [])):
            chapter_analysis = {
                "index": i,
                "title": chapter_data.get("title", ""),
                "total_sections": len(chapter_data.get("sections", [])),
                "sections": []
            }
            
            # Analyze each section
            for j, section in enumerate(chapter_data.get("sections", [])):
                section_analysis = {
                    "index": j,
                    "title": section.get("title", "")
                }
                chapter_analysis["sections"].append(section_analysis)
            
            analysis["chapters"].append(chapter_analysis)
        
        return analysis
    
    def analyze_chapter(self, chapter: int) -> Dict[str, Any]:
        """Analyze a chapter file"""
        logger.info(f"Analyzing chapter {chapter}")
        
        # Find the chapter file
        chapter_files = [f for f in os.listdir("output/chapters") if f.startswith(f"{chapter:02d}_")]
        if not chapter_files:
            logger.error(f"Chapter file not found for chapter {chapter}")
            return {"error": "Chapter file not found"}
        
        chapter_path = f"output/chapters/{chapter_files[0]}"
        
        # Check if the file exists
        if not os.path.exists(chapter_path):
            logger.error(f"Chapter file not found: {chapter_path}")
            return {"error": "Chapter file not found"}
        
        # Load the chapter
        try:
            with open(chapter_path, "r") as f:
                content = f.read()
        except Exception as e:
            logger.error(f"Error reading chapter file: {e}")
            return {"error": f"Error reading chapter file: {e}"}
        
        # Analyze the chapter
        lines = content.split("\n")
        title = lines[0].replace("# ", "") if lines else ""
        
        # Count words
        word_count = sum(len(line.split()) for line in lines)
        
        # Count sections (lines starting with ##)
        sections = [line for line in lines if line.startswith("## ")]
        
        analysis = {
            "file_path": chapter_path,
            "file_size": os.path.getsize(chapter_path),
            "title": title,
            "word_count": word_count,
            "line_count": len(lines),
            "section_count": len(sections),
            "sections": [section.replace("## ", "") for section in sections]
        }
        
        return analysis
    
    def save_analysis(self, analysis: Dict[str, Any], filename: str):
        """Save analysis results to a file"""
        logger.info(f"Saving analysis to {filename}")
        
        # Ensure the directory exists
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        # Save the analysis
        with open(filename, "w") as f:
            json.dump(analysis, f, indent=2)
        
        logger.info(f"Analysis saved to {filename}")
    
    def generate_report(self, test_results: Dict[str, Any], analysis: Dict[str, Any], filename: str):
        """Generate a human-readable report"""
        logger.info(f"Generating report: {filename}")
        
        # Ensure the directory exists
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        # Generate the report
        with open(filename, "w") as f:
            f.write("# Book Factory Test Analysis Report\n\n")
            f.write(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Test results
            f.write("## Test Results\n\n")
            f.write(f"Test: {test_results['test_name']}\n")
            f.write(f"Chapter: {test_results['chapter']}\n")
            f.write(f"Force: {test_results['force']}\n")
            f.write(f"Success: {test_results['success']}\n")
            f.write(f"Elapsed Time: {test_results['elapsed_time']:.2f} seconds\n\n")
            
            # Analysis results
            f.write("## Analysis Results\n\n")
            
            if "error" in analysis:
                f.write(f"Error: {analysis['error']}\n\n")
            else:
                if "total_chapters" in analysis:
                    # Outline analysis
                    f.write("### Outline Analysis\n\n")
                    f.write(f"File: {analysis['file_path']}\n")
                    f.write(f"Size: {analysis['file_size']} bytes\n")
                    f.write(f"Total Chapters: {analysis['total_chapters']}\n\n")
                    
                    f.write("#### Chapters\n\n")
                    for chapter in analysis["chapters"]:
                        f.write(f"- Chapter {chapter['index']+1}: {chapter['title']}\n")
                        f.write(f"  - Sections: {chapter['total_sections']}\n")
                        for section in chapter["sections"]:
                            f.write(f"    - {section['title']}\n")
                        f.write("\n")
                else:
                    # Chapter analysis
                    f.write("### Chapter Analysis\n\n")
                    f.write(f"File: {analysis['file_path']}\n")
                    f.write(f"Size: {analysis['file_size']} bytes\n")
                    f.write(f"Title: {analysis['title']}\n")
                    f.write(f"Word Count: {analysis['word_count']}\n")
                    f.write(f"Line Count: {analysis['line_count']}\n")
                    f.write(f"Section Count: {analysis['section_count']}\n\n")
                    
                    f.write("#### Sections\n\n")
                    for section in analysis["sections"]:
                        f.write(f"- {section}\n")
                    f.write("\n")
        
        logger.info(f"Report generated: {filename}")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Analyze Book Factory CLI test results")
    parser.add_argument("test", choices=["outline", "chapter-outline", "write", "flow"],
                        help="Test to run and analyze")
    parser.add_argument("--chapter", type=int, default=1,
                        help="Chapter number (default: 1)")
    parser.add_argument("--force", action="store_true",
                        help="Force regeneration of chapter")
    
    args = parser.parse_args()
    
    # Create analyzer
    analyzer = TestAnalyzer()
    
    # Run the test
    test_results = analyzer.run_test(args.test, args.chapter, args.force)
    
    # Analyze the results
    if args.test == "outline":
        analysis = analyzer.analyze_outline()
    elif args.test == "chapter-outline":
        analysis = analyzer.analyze_outline(args.chapter)
    elif args.test == "write" or args.test == "flow":
        analysis = analyzer.analyze_chapter(args.chapter)
    else:
        analysis = {"error": "Unknown test type"}
    
    # Save the results
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    test_results_file = f"output/analysis/{args.test}_{args.chapter}_{timestamp}_results.json"
    analysis_file = f"output/analysis/{args.test}_{args.chapter}_{timestamp}_analysis.json"
    report_file = f"output/analysis/{args.test}_{args.chapter}_{timestamp}_report.md"
    
    analyzer.save_analysis(test_results, test_results_file)
    analyzer.save_analysis(analysis, analysis_file)
    analyzer.generate_report(test_results, analysis, report_file)
    
    logger.info("Analysis complete")
    logger.info(f"Test results: {test_results_file}")
    logger.info(f"Analysis: {analysis_file}")
    logger.info(f"Report: {report_file}")

if __name__ == "__main__":
    main()