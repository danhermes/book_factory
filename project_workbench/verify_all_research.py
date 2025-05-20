#!/usr/bin/env python
import os
import sys
import glob
import argparse
import logging
from typing import List, Dict, Any
from verify_research_usage import verify_research_usage, generate_report

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("verify_all_research")

def find_research_files() -> List[str]:
    """Find all research log files in the output/research directory."""
    research_dir = "output/research"
    if not os.path.exists(research_dir):
        logger.error(f"Research directory {research_dir} does not exist")
        return []
    
    research_files = glob.glob(os.path.join(research_dir, "chapter_*_research.md"))
    return research_files

def find_chapter_files() -> Dict[str, str]:
    """Find all chapter files in the output/chapters directory."""
    chapters_dir = "output/chapters"
    if not os.path.exists(chapters_dir):
        logger.error(f"Chapters directory {chapters_dir} does not exist")
        return {}
    
    chapter_files = {}
    for chapter_file in glob.glob(os.path.join(chapters_dir, "chapter_*.md")):
        # Extract chapter number from filename
        chapter_num = os.path.basename(chapter_file).split("_")[1]
        chapter_files[chapter_num] = chapter_file
    
    return chapter_files

def verify_all_research(output_dir: str = "output/research_verification") -> Dict[str, Any]:
    """Verify research usage for all chapters."""
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Find research and chapter files
    research_files = find_research_files()
    chapter_files = find_chapter_files()
    
    if not research_files:
        logger.error("No research files found")
        return {"error": "No research files found"}
    
    if not chapter_files:
        logger.error("No chapter files found")
        return {"error": "No chapter files found"}
    
    # Verify research usage for each chapter
    results = {}
    for research_file in research_files:
        # Extract chapter number from filename
        chapter_num = os.path.basename(research_file).split("_")[1]
        
        if chapter_num not in chapter_files:
            logger.warning(f"No chapter file found for research file {research_file}")
            continue
        
        chapter_file = chapter_files[chapter_num]
        logger.info(f"Verifying research usage for chapter {chapter_num}")
        
        # Verify research usage
        chapter_results = verify_research_usage(research_file, chapter_file)
        
        # Generate report
        report_file = os.path.join(output_dir, f"chapter_{chapter_num}_verification.md")
        generate_report(chapter_results, report_file)
        
        results[chapter_num] = chapter_results
    
    # Generate summary report
    summary = generate_summary_report(results, output_dir)
    
    return results

def generate_summary_report(results: Dict[str, Any], output_dir: str) -> str:
    """Generate a summary report of all verification results."""
    summary = "# Research Usage Verification Summary\n\n"
    
    # Calculate overall statistics
    total_findings = 0
    total_used_findings = 0
    
    for chapter_num, chapter_results in results.items():
        total_findings += chapter_results["total_findings"]
        total_used_findings += chapter_results["used_findings"]
    
    overall_score = total_used_findings / total_findings if total_findings > 0 else 0
    
    summary += f"## Overall Results\n\n"
    summary += f"- Total Chapters: {len(results)}\n"
    summary += f"- Total Research Findings: {total_findings}\n"
    summary += f"- Total Used Research Findings: {total_used_findings}\n"
    summary += f"- Overall Score: {overall_score:.2%}\n\n"
    
    summary += f"## Chapter-by-Chapter Results\n\n"
    
    for chapter_num, chapter_results in sorted(results.items(), key=lambda x: int(x[0])):
        summary += f"### Chapter {chapter_num}\n\n"
        summary += f"- Research File: {os.path.basename(chapter_results['research_file'])}\n"
        summary += f"- Chapter File: {os.path.basename(chapter_results['chapter_file'])}\n"
        summary += f"- Total Findings: {chapter_results['total_findings']}\n"
        summary += f"- Used Findings: {chapter_results['used_findings']}\n"
        summary += f"- Score: {chapter_results['overall_score']:.2%}\n\n"
    
    # Save summary report
    summary_file = os.path.join(output_dir, "summary.md")
    with open(summary_file, 'w') as f:
        f.write(summary)
    
    logger.info(f"Summary report saved to {summary_file}")
    
    return summary

def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="Verify research usage for all chapters")
    parser.add_argument("--output", type=str, default="output/research_verification", 
                        help="Directory to save verification reports")
    
    args = parser.parse_args()
    
    # Verify all research
    results = verify_all_research(args.output)
    
    if "error" in results:
        logger.error(results["error"])
        sys.exit(1)
    
    # Print summary
    print("\nResearch Usage Verification Complete")
    print(f"Reports saved to {args.output}")

if __name__ == "__main__":
    main() 