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
logger = logging.getLogger("verify_research")

def extract_research_findings(research_file: str) -> Dict[str, List[str]]:
    """Extract research findings from a research log file."""
    findings = {}
    current_section = None
    
    try:
        with open(research_file, 'r') as f:
            content = f.read()
            
        # Extract section titles and their research findings
        section_pattern = r"### Section: (.*?)\n\n(.*?)(?=### Section:|$)"
        sections = re.findall(section_pattern, content, re.DOTALL)
        
        for section_title, section_content in sections:
            # Extract research findings for this section
            findings_pattern = r"- Source: (.*?)\n  - Finding: (.*?)\n  - Usage: (.*?)(?=\n- Source:|$)"
            section_findings = re.findall(findings_pattern, section_content, re.DOTALL)
            
            findings[section_title] = section_findings
    
    except Exception as e:
        logger.error(f"Error extracting research findings from {research_file}: {e}")
    
    return findings

def extract_section_content(chapter_file: str, section_title: str) -> str:
    """Extract the content of a specific section from a chapter file."""
    try:
        with open(chapter_file, 'r') as f:
            content = f.read()
            
        # Find the section
        section_pattern = f"## {re.escape(section_title)}\n\n(.*?)(?=\n## |$)"
        match = re.search(section_pattern, content, re.DOTALL)
        
        if match:
            return match.group(1)
        else:
            logger.warning(f"Section '{section_title}' not found in {chapter_file}")
            return ""
    
    except Exception as e:
        logger.error(f"Error extracting section content from {chapter_file}: {e}")
        return ""

def verify_research_usage(research_file: str, chapter_file: str) -> Dict[str, Any]:
    """Verify that research findings are used in the chapter content."""
    results = {
        "research_file": research_file,
        "chapter_file": chapter_file,
        "sections": {},
        "overall_score": 0,
        "total_findings": 0,
        "used_findings": 0
    }
    
    # Extract research findings
    findings = extract_research_findings(research_file)
    
    # For each section, verify that research findings are used
    for section_title, section_findings in findings.items():
        section_content = extract_section_content(chapter_file, section_title)
        
        section_results = {
            "findings": [],
            "used_count": 0,
            "total_count": len(section_findings),
            "score": 0
        }
        
        # For each finding, check if it's used in the section content
        for source, finding, usage in section_findings:
            finding_result = {
                "source": source,
                "finding": finding,
                "usage": usage,
                "used": False,
                "evidence": ""
            }
            
            # Check if the finding is used in the section content
            # This is a simple check that looks for key phrases from the finding
            # A more sophisticated approach would use semantic similarity
            key_phrases = extract_key_phrases(finding)
            for phrase in key_phrases:
                if phrase.lower() in section_content.lower():
                    finding_result["used"] = True
                    finding_result["evidence"] = f"Found phrase: '{phrase}'"
                    section_results["used_count"] += 1
                    break
            
            section_results["findings"].append(finding_result)
        
        # Calculate score for this section
        if section_results["total_count"] > 0:
            section_results["score"] = section_results["used_count"] / section_results["total_count"]
        
        results["sections"][section_title] = section_results
        results["total_findings"] += section_results["total_count"]
        results["used_findings"] += section_results["used_count"]
    
    # Calculate overall score
    if results["total_findings"] > 0:
        results["overall_score"] = results["used_findings"] / results["total_findings"]
    
    return results

def extract_key_phrases(text: str) -> List[str]:
    """Extract key phrases from a text."""
    # This is a simple implementation that extracts phrases of 3-5 words
    # A more sophisticated approach would use NLP techniques
    words = text.split()
    phrases = []
    
    for i in range(len(words) - 2):
        for j in range(3, min(6, len(words) - i + 1)):
            phrase = " ".join(words[i:i+j])
            if len(phrase) > 10:  # Only include phrases with more than 10 characters
                phrases.append(phrase)
    
    return phrases

def generate_report(results: Dict[str, Any], output_file: Optional[str] = None) -> str:
    """Generate a report of research usage verification."""
    report = f"# Research Usage Verification Report\n\n"
    report += f"Research File: {results['research_file']}\n"
    report += f"Chapter File: {results['chapter_file']}\n\n"
    
    report += f"## Overall Results\n\n"
    report += f"- Total Research Findings: {results['total_findings']}\n"
    report += f"- Used Research Findings: {results['used_findings']}\n"
    report += f"- Overall Score: {results['overall_score']:.2%}\n\n"
    
    report += f"## Section-by-Section Analysis\n\n"
    
    for section_title, section_results in results["sections"].items():
        report += f"### {section_title}\n\n"
        report += f"- Total Findings: {section_results['total_count']}\n"
        report += f"- Used Findings: {section_results['used_count']}\n"
        report += f"- Score: {section_results['score']:.2%}\n\n"
        
        report += f"#### Findings Details\n\n"
        for finding in section_results["findings"]:
            report += f"- **Source**: {finding['source']}\n"
            report += f"  - **Finding**: {finding['finding']}\n"
            report += f"  - **Usage**: {finding['usage']}\n"
            report += f"  - **Used**: {'Yes' if finding['used'] else 'No'}\n"
            if finding['used']:
                report += f"  - **Evidence**: {finding['evidence']}\n"
            report += "\n"
    
    if output_file:
        with open(output_file, 'w') as f:
            f.write(report)
        logger.info(f"Report saved to {output_file}")
    
    return report

def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="Verify that writers are using research findings")
    parser.add_argument("--research", type=str, required=True, help="Path to the research log file")
    parser.add_argument("--chapter", type=str, required=True, help="Path to the chapter file")
    parser.add_argument("--output", type=str, help="Path to save the verification report")
    
    args = parser.parse_args()
    
    # Verify research usage
    results = verify_research_usage(args.research, args.chapter)
    
    # Generate report
    report = generate_report(results, args.output)
    
    # Print summary
    print(f"\nResearch Usage Summary:")
    print(f"Total Findings: {results['total_findings']}")
    print(f"Used Findings: {results['used_findings']}")
    print(f"Overall Score: {results['overall_score']:.2%}")
    
    if not args.output:
        print("\nFull Report:")
        print(report)

if __name__ == "__main__":
    main() 