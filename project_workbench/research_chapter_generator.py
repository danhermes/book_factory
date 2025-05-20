#!/usr/bin/env python
import os
import sys
import json
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import StrOutputParser

load_dotenv()

def generate_research_chapter(chapter_index=0):
    """Generate a single chapter with extensive research and detailed case studies"""
    print(f"Generating research-rich chapter {chapter_index+1}")
    
    # Create chapters directory if it doesn't exist
    if not os.path.exists("research_chapters"):
        os.makedirs("research_chapters")
    
    # Load the outline
    try:
        with open("book_outline.json", "r") as f:
            outline = json.load(f)
            print(f"Loaded outline with {len(outline.get('chapters', []))} chapters")
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading outline: {e}")
        print("Please make sure book_outline.json exists and is valid")
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
    chapter_file = f"research_chapters/{chapter_index+1:02d}_{safe_title}.md"
    
    # Initialize the LLM with a longer timeout and higher temperature for creativity
    llm = ChatOpenAI(
        model="gpt-4o",
        temperature=0.7,
        request_timeout=300
    )
    
    # Create the research-focused prompt
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a world-class business researcher and author with expertise in AI applications for business. 
        Your task is to write an extensively researched, data-rich chapter for a book about ChatGPT for Business.
        
        CRITICAL REQUIREMENTS:
        1. Include AT LEAST 10-15 specific research citations from actual studies, surveys, and reports with years
        2. Provide SPECIFIC statistics, percentages, and data points throughout (minimum 15-20 data points)
        3. Include DETAILED case studies with company size, industry, specific metrics, and implementation details
        4. Discuss technical implementation details including integration approaches, APIs, and technical challenges
        5. Present balanced analysis including limitations, challenges, and potential drawbacks
        6. Provide specific ROI calculations and before/after metrics in case studies
        
        FORMAT REQUIREMENTS:
        - Write 4000-5000 words with substantial depth in each section
        - Use proper citation format (Author, Year) for all research references
        - Include a "Research Highlights" section summarizing key findings
        - Format case studies with clear subheadings for Challenge, Solution, Implementation, and Results
        - Include tables or structured data presentations where appropriate
        
        CASE STUDY REQUIREMENTS:
        For each case study, include:
        - Company name, size (employees/revenue), industry, and specific business challenge
        - Detailed technical implementation approach (specific models, integration methods)
        - Implementation timeline and resource investment
        - Specific before/after metrics with percentages or absolute numbers
        - ROI calculation or business impact assessment
        - Challenges encountered and how they were overcome
        - Lessons learned and best practices derived
        
        CONTENT STRUCTURE:
        1. Introduction with research context (600-800 words)
        2. Research overview and key findings (500-700 words)
        3. Detailed case studies (3-4 studies, 500-700 words each)
        4. Technical implementation details (600-800 words)
        5. Best practices derived from research (500-700 words)
        6. Limitations and challenges (400-600 words)
        7. Future directions based on research trends (300-500 words)
        8. Conclusion with synthesis of research (300-500 words)
        
        Format your response as Markdown with appropriate headings, lists, tables, and emphasis.
        """),
        ("user", """Write Chapter {chapter_number}: {chapter_title} for the book "ChatGPT for Business".
        
        This chapter should cover the following sections:
        {sections}
        
        The overall book contains these chapters:
        {all_chapters}
        
        RESEARCH REQUIREMENTS:
        1. Include AT LEAST 10-15 specific research citations from actual studies, surveys, and reports with years
        2. Provide SPECIFIC statistics, percentages, and data points throughout (minimum 15-20 data points)
        3. Reference expert opinions and thought leaders in the field with direct quotes
        4. Include detailed technical information about ChatGPT implementation
        5. Discuss both benefits and limitations based on research findings
        
        CASE STUDY REQUIREMENTS:
        For each case study, include:
        - Company name, size (employees/revenue), industry, and specific business challenge
        - Detailed technical implementation approach (specific models, integration methods)
        - Implementation timeline and resource investment
        - Specific before/after metrics with percentages or absolute numbers
        - ROI calculation or business impact assessment
        - Challenges encountered and how they were overcome
        - Lessons learned and best practices derived
        
        Make sure this chapter is extensively researched, data-rich, and provides substantial depth on the topic.
        """)
    ])
    
    # Format the sections and all chapters
    sections_text = "\n".join([f"- {section}" for section in section_titles]) if section_titles else "No specific sections provided in the outline."
    all_chapters_text = "\n".join([f"- Chapter {i+1}: {ch['title']}" for i, ch in enumerate(chapters)])
    
    # Generate the chapter content
    print("Generating research-rich chapter content...")
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
    
    print(f"Successfully generated and saved research-rich chapter {chapter_index+1} to {chapter_file}")
    return chapter_file

if __name__ == "__main__":
    # Get chapter index from command line argument or default to 0 (first chapter)
    chapter_index = 0
    if len(sys.argv) > 1:
        try:
            chapter_index = int(sys.argv[1]) - 1  # Convert from 1-based to 0-based
        except ValueError:
            print("Please provide a valid chapter number")
            sys.exit(1)
    
    # Run the specified chapter
    generate_research_chapter(chapter_index)