from typing import List, Dict, Any
import re
import logging
import time

# Configure logging
logger = logging.getLogger("outline_parser")

class OutlineParser:
    """Parser for extracting chapters and sections from the outline."""
    
    @staticmethod
    def parse_content(content: str) -> Dict[str, Any]:
        """
        Parse the content into a structured outline.
        
        Args:
            content: The text content of the outline file.
            
        Returns:
            A dictionary with total_chapters and chapters list.
        """
        logger.info("===== PARSING CONTENT =====")
        start_time = time.time()
        
        lines = content.strip().split('\n')
        logger.info(f"Content has {len(lines)} lines")
        
        chapters = []
        current_chapter = None
        
        # Regular expressions for identifying different parts of the outline
        chapter_pattern = re.compile(r'^Chapter (\d+): (.+)$')
        section_pattern = re.compile(r'^- (.+?)(?:: (.+))?$')
        
        logger.info("Starting to parse content line by line")
        
        for line in lines:
            line = line.strip()
            
            # Skip empty lines and the title
            if not line or line == "Expanded Outline - ChatGPT for Business" or line == "Introduction":
                continue
                
            # Check if this is a chapter heading
            chapter_match = chapter_pattern.match(line)
            if chapter_match:
                if current_chapter:
                    chapters.append(current_chapter)
                
                current_chapter = {
                    "title": chapter_match.group(2),
                    "sections": []
                }
                continue
            
            # Check if this is a section
            section_match = section_pattern.match(line)
            if section_match and current_chapter:
                section_type = section_match.group(1).strip()
                
                # Handle different section types
                if section_type.startswith("Theme:"):
                    # Add theme as the first section (introduction)
                    current_chapter["sections"].append({
                        "title": f"Theme: {section_type.replace('Theme:', '').strip()} (Introduction)"
                    })
                elif section_type.startswith("Original Stories:"):
                    # Split stories into individual sections
                    stories = section_type.replace("Original Stories:", "").strip().split(", ")
                    for story in stories:
                        current_chapter["sections"].append({
                            "title": f"Story: {story} (Story)"
                        })
                elif section_type.startswith("Topic Explanations:"):
                    # Split topic explanations into individual sections
                    topics = section_type.replace("Topic Explanations:", "").strip().split(", ")
                    for topic in topics:
                        current_chapter["sections"].append({
                            "title": f"{topic} (Topic Explanation)"
                        })
                elif section_type.startswith("Bonus Topics:"):
                    # Split bonus topics into individual sections
                    bonuses = section_type.replace("Bonus Topics:", "").strip().split(", ")
                    for bonus in bonuses:
                        current_chapter["sections"].append({
                            "title": f"{bonus} (Bonus Topic)"
                        })
                elif section_type.startswith("Big Box:"):
                    # Add big box as a technical section
                    current_chapter["sections"].append({
                        "title": f"{section_type.replace('Big Box:', '').strip()} (Big Box)"
                    })
                elif section_type.startswith("Chapter Bridge:"):
                    # Add chapter bridge as a transition section
                    current_chapter["sections"].append({
                        "title": f"{section_type.replace('Chapter Bridge:', '').strip()} (Chapter Bridge)"
                    })
                elif section_type.startswith("Outro:"):
                    # Add outro as a closing section
                    current_chapter["sections"].append({
                        "title": f"{section_type.replace('Outro:', '').strip()} (Outro)"
                    })
                elif section_type.startswith("Chapter Summary:"):
                    # Add chapter summary
                    current_chapter["sections"].append({
                        "title": f"{section_type.replace('Chapter Summary:', '').strip()} (Chapter Summary)"
                    })
        
        # Add the last chapter
        if current_chapter:
            chapters.append(current_chapter)
        
        # Log parsing results
        logger.info(f"Parsed {len(chapters)} chapters")
        for i, chapter in enumerate(chapters):
            logger.info(f"Chapter {i+1}: {chapter['title']} with {len(chapter['sections'])} sections")
        
        parsing_time = time.time() - start_time
        logger.info(f"Content parsing completed in {parsing_time:.2f} seconds")
        logger.info("===== CONTENT PARSING COMPLETE =====")
        
        return {
            "total_chapters": len(chapters),
            "chapters": chapters
        }
    
    # For backward compatibility
    @staticmethod
    def parse_pdf_content(content: str) -> Dict[str, Any]:
        """Alias for parse_content for backward compatibility."""
        return OutlineParser.parse_content(content)