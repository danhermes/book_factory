#!/usr/bin/env python
import os
import sys
import json
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import StrOutputParser

load_dotenv()

def generate_chapter(chapter_index=0, force_regenerate=False):
    """Generate a single chapter using direct LLM calls"""
    print(f"Generating chapter {chapter_index+1}")
    
    # Create chapters directory if it doesn't exist
    if not os.path.exists("output/chapters"):
        os.makedirs("output/chapters")
    
    # Load the outline from output/outlines directory
    try:
        # First try to load from output/outlines directory
        if os.path.exists("output/outlines/book_outline.json"):
            with open("output/outlines/book_outline.json", "r") as f:
                outline = json.load(f)
                print(f"Loaded outline from output/outlines/book_outline.json with {len(outline.get('chapters', []))} chapters")
        # Fall back to root directory if not found in output/outlines
        elif os.path.exists("book_outline.json"):
            with open("book_outline.json", "r") as f:
                outline = json.load(f)
                print(f"Loaded outline from book_outline.json with {len(outline.get('chapters', []))} chapters")
        else:
            raise FileNotFoundError("book_outline.json not found in output/outlines or root directory")
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading outline: {e}")
        print("Please make sure book_outline.json exists and is valid in either output/outlines or root directory")
        return
    
    # Get the chapter title
    chapters = outline.get("chapters", [])
    if not chapters or chapter_index >= len(chapters):
        print(f"Chapter {chapter_index+1} not found in outline")
        return
    
    chapter_title = chapters[chapter_index]["title"]
    print(f"Found chapter title: {chapter_title}")
    
    # Get chapter sections if available
    chapter_sections = chapters[chapter_index].get("sections", [])
    section_titles = [section.get("title", "") for section in chapter_sections]
    
    # Create a safe filename
    safe_title = chapter_title.replace(' ', '_').replace(':', '_').replace('/', '_').replace('\\', '_')
    chapter_file = f"output/chapters/{chapter_index+1:02d}_{safe_title}.md"
    
    # Check if chapter already exists
    if os.path.exists(chapter_file) and not force_regenerate:
        print(f"Chapter {chapter_index+1} already exists at {chapter_file}")
        return
    
    if force_regenerate and os.path.exists(chapter_file):
        print(f"Forcing regeneration of chapter {chapter_index+1}")
    
    # Initialize the LLM
    llm = ChatOpenAI(model="gpt-4o")
    
    # Create the prompt
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert book writer specializing in business and technology topics with a strong background in research.
        Your task is to write a thoroughly researched, in-depth chapter for a book about ChatGPT for Business.
        
        Follow these guidelines:
        - Write in a clear, engaging style appropriate for business professionals
        - Include SUBSTANTIAL research, data, statistics, and expert opinions to support all claims
        - Cite specific research studies, surveys, and industry reports where appropriate
        - Develop DETAILED case studies with specific metrics, challenges, and outcomes
        - Include real-world implementation details, not just conceptual overviews
        - Balance technical depth with accessibility
        - Organize the content logically with clear sections
        - Include an introduction that sets up the chapter with compelling research
        - Include a conclusion that summarizes key points
        - Write approximately 3000-4000 words with depth in each section
        
        For case studies:
        - Provide specific, detailed examples that feel authentic, not marketing pitches
        - Include actual implementation challenges and how they were overcome
        - Present realistic metrics and outcomes with specific numbers
        - Discuss limitations and lessons learned, not just successes
        - Include technical details about implementation where relevant
        
        The chapter should follow this structure:
        1. Introduction with research context and significance (500-700 words)
        2. Main content sections with substantial depth and research (each 500-800 words)
        3. Detailed case studies with specific metrics and implementation details (each 400-600 words)
        4. Research-backed best practices and implementation advice (500-700 words)
        5. Conclusion with synthesis of research and next steps (300-500 words)
        
        Format your response as Markdown with appropriate headings, lists, and emphasis.
        """),
        ("user", """Write Chapter {chapter_number}: {chapter_title} for the book "ChatGPT for Business".
        
        This chapter should cover the following sections:
        {sections}
        
        The overall book contains these chapters:
        {all_chapters}
        
        Research requirements:
        1. Include at least 5-7 specific research citations, studies, or industry reports
        2. Provide concrete statistics and data points throughout the chapter
        3. Reference expert opinions and thought leaders in the field
        4. Include detailed technical information about ChatGPT implementation
        5. Discuss both benefits and limitations based on research findings
        
        For case studies, include:
        - Specific company details (size, industry, challenges)
        - Technical implementation details (how ChatGPT was integrated)
        - Specific metrics before and after implementation
        - ROI calculations where possible
        - Challenges encountered and how they were overcome
        
        Make sure this chapter flows well with the rest of the book and covers its topic with substantial depth and research backing.
        """)
    ])
    
    # Format the sections and all chapters
    sections_text = "\n".join([f"- {section}" for section in section_titles]) if section_titles else "No specific sections provided in the outline."
    all_chapters_text = "\n".join([f"- Chapter {i+1}: {ch['title']}" for i, ch in enumerate(chapters)])
    
    # Generate the chapter content
    print("Generating chapter content...")
    chain = prompt | llm | StrOutputParser()
    chapter_content = chain.invoke({
        "chapter_number": chapter_index + 1,
        "chapter_title": chapter_title,
        "sections": sections_text,
        "all_chapters": all_chapters_text
    })
    
    # Save the chapter
    with open(chapter_file, "w") as f:
        f.write(f"# Chapter {chapter_index+1}: {chapter_title}\n\n")
        f.write(chapter_content)
    
    print(f"Successfully generated and saved chapter {chapter_index+1} to {chapter_file}")
    return chapter_file

if __name__ == "__main__":
    # Get chapter index from command line argument or default to 0 (first chapter)
    chapter_index = 0
    force_regenerate = False
    
    # Parse command line arguments
    for i, arg in enumerate(sys.argv[1:]):
        if arg == "--force" or arg == "-f":
            force_regenerate = True
        elif i == 0 and not arg.startswith("-"):
            try:
                chapter_index = int(arg) - 1  # Convert from 1-based to 0-based
            except ValueError:
                print("Please provide a valid chapter number")
                sys.exit(1)
    
    # Run the specified chapter
    generate_chapter(chapter_index, force_regenerate)