#!/usr/bin/env python
import os
import sys
import json
import re
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import StrOutputParser

from book_writing_flow.tools.rag_utils import RagContentProvider

load_dotenv()

def enhance_section(chapter_file, section_title=None, force_regenerate=False):
    """
    Enhance a specific section of a chapter or all sections if section_title is None.
    Uses RAG content and section-specific templates to improve the content.
    """
    print(f"Enhancing section in {chapter_file}")
    
    # Check if chapter file exists
    if not os.path.exists(chapter_file):
        print(f"Chapter file {chapter_file} not found")
        return
    
    # Load the chapter content
    with open(chapter_file, "r") as f:
        chapter_content = f.read()
    
    # Extract chapter title
    chapter_title_match = re.search(r"# Chapter \d+: (.+)", chapter_content)
    if not chapter_title_match:
        print("Could not extract chapter title")
        return
    
    chapter_title = chapter_title_match.group(1)
    print(f"Found chapter title: {chapter_title}")
    
    # Load section templates
    try:
        with open("section_templates.json", "r") as f:
            section_templates = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading section templates: {e}")
        return
    
    # Initialize the RAG content provider
    rag_provider = RagContentProvider({
        "expanded_outline": "rag/ChatGPT_for_Business_Expanded_Outline.txt",
        "full_content": "rag/ChatGPT_for_Business_FULL_WITH_COVER.txt"
    })
    
    # Initialize the LLM
    llm = ChatOpenAI(model="gpt-4o")
    
    # Extract sections from the chapter
    sections = []
    current_section = {"title": "", "content": "", "level": 0}
    
    lines = chapter_content.split("\n")
    for line in lines:
        # Check if line is a heading
        heading_match = re.match(r"(#+) (.+)", line)
        if heading_match and len(heading_match.group(1)) > 1:  # Skip the chapter title (h1)
            # Save previous section if it exists
            if current_section["title"]:
                sections.append(current_section)
            
            # Start new section
            current_section = {
                "title": heading_match.group(2),
                "content": line + "\n",
                "level": len(heading_match.group(1))
            }
        else:
            # Add line to current section
            current_section["content"] += line + "\n"
    
    # Add the last section
    if current_section["title"]:
        sections.append(current_section)
    
    print(f"Found {len(sections)} sections in the chapter")
    
    # Filter sections if a specific title is provided
    if section_title:
        sections = [s for s in sections if section_title.lower() in s["title"].lower()]
        if not sections:
            print(f"Section '{section_title}' not found in the chapter")
            return
        print(f"Enhancing section: {sections[0]['title']}")
    
    # Enhanced chapter content
    enhanced_content = lines[:2]  # Keep the chapter title
    
    # Process each section
    for section in sections:
        section_type = "Unknown"
        
        # Determine section type
        for known_type in section_templates.keys():
            if known_type.lower() in section["title"].lower() or f"({known_type})" in section["title"]:
                section_type = known_type
                break
        
        # If still unknown, try to infer from patterns
        if section_type == "Unknown":
            if "intro" in section["title"].lower():
                section_type = "Introduction"
            elif any(company in section["title"] for company in ["WelcomeWell", "StackHaven", "FlexTax", "LeadFleet", "BriteTeam", "WestBridge", "BrightPath"]):
                section_type = "Story"
            elif "bonus" in section["title"].lower():
                section_type = "Bonus Topic"
            elif "big box" in section["title"].lower():
                section_type = "Big Box"
            elif "outro" in section["title"].lower():
                section_type = "Outro"
            elif "transition" in section["title"].lower() or "bridge" in section["title"].lower():
                section_type = "Chapter Bridge"
            else:
                section_type = "Topic Explanation"
        
        print(f"Section '{section['title']}' identified as type: {section_type}")
        
        # Get section template
        template = section_templates.get(section_type, {
            "min_length": 500,
            "structure": ["Introduction", "Main content", "Conclusion"],
            "example_prompts": ["Write a detailed section about {topic}"]
        })
        
        # Get relevant RAG content for this section
        section_query = f"{chapter_title} {section['title']}"
        relevant_content = rag_provider.find_relevant_content(
            query=section_query,
            content_types=["expanded_outline", "full_content"],
            max_chunks=5,
            chunk_size=1000
        )
        
        rag_content_text = "\n\n".join(relevant_content) if relevant_content else "No relevant RAG content found."
        print(f"Found {len(relevant_content)} relevant RAG content chunks for section '{section['title']}'")
        
        # Check if section needs enhancement (too short or forced)
        section_word_count = len(section["content"].split())
        min_word_count = template["min_length"]
        
        if section_word_count < min_word_count or force_regenerate:
            print(f"Enhancing section '{section['title']}' (current: {section_word_count} words, target: {min_word_count}+ words)")
            
            # Format structure for the prompt
            structure_text = "\n".join([f"- {item}" for item in template["structure"]])
            
            # Create the prompt
            prompt = ChatPromptTemplate.from_messages([
                ("system", """You are an expert book writer specializing in business and technology topics with a strong background in research.
                Your task is to enhance or rewrite a section of a chapter about ChatGPT for Business.
                
                Follow these guidelines:
                - Write in a clear, engaging style appropriate for business professionals
                - Include research, data, statistics, and expert opinions to support claims
                - Develop detailed examples with specific metrics, challenges, and outcomes
                - Include real-world implementation details, not just conceptual overviews
                - Balance technical depth with accessibility
                - Maintain the original section title and purpose
                - Ensure the enhanced section meets or exceeds the minimum word count
                - Incorporate relevant content from the RAG materials provided
                - Maintain consistency with the style and tone of the RAG materials
                
                Format your response as Markdown with appropriate headings, lists, and emphasis.
                """),
                ("user", """Enhance the following section from Chapter: {chapter_title}
                
                SECTION TITLE: {section_title}
                SECTION TYPE: {section_type}
                MINIMUM WORD COUNT: {min_word_count} words
                
                CURRENT CONTENT:
                {current_content}
                
                RECOMMENDED STRUCTURE:
                {structure}
                
                RELEVANT RAG CONTENT TO INCORPORATE:
                {rag_content}
                
                Please enhance this section to:
                1. Meet or exceed the minimum word count of {min_word_count} words
                2. Follow the recommended structure while maintaining the original heading
                3. Incorporate relevant content from the RAG materials
                4. Add depth, detail, and research-backed content
                5. Include specific examples, metrics, and implementation details
                6. Maintain consistency with the book's style and tone
                
                Return the enhanced section with the same heading level as the original.
                """)
            ])
            
            # Generate the enhanced section content
            chain = prompt | llm | StrOutputParser()
            enhanced_section = chain.invoke({
                "chapter_title": chapter_title,
                "section_title": section["title"],
                "section_type": section_type,
                "min_word_count": min_word_count,
                "current_content": section["content"],
                "structure": structure_text,
                "rag_content": rag_content_text
            })
            
            # Add enhanced section to the chapter
            if section_title:  # If enhancing a specific section
                # Replace just this section in the original content
                section_pattern = re.escape(section["content"].strip())
                chapter_content = re.sub(section_pattern, enhanced_section.strip(), chapter_content)
                
                # Save the enhanced chapter
                with open(chapter_file, "w") as f:
                    f.write(chapter_content)
                
                print(f"Successfully enhanced section '{section['title']}' in {chapter_file}")
                return
            else:
                # Add to the enhanced content for full chapter regeneration
                enhanced_content.append(enhanced_section)
        else:
            # Section is already adequate, keep as is
            print(f"Section '{section['title']}' already meets length requirements ({section_word_count} words)")
            enhanced_content.append(section["content"])
    
    # If enhancing all sections, save the complete enhanced chapter
    if not section_title:
        with open(chapter_file, "w") as f:
            f.write("\n".join(enhanced_content))
        
        print(f"Successfully enhanced all sections in {chapter_file}")

if __name__ == "__main__":
    # Parse command line arguments
    if len(sys.argv) < 2:
        print("Usage: python section_enhancer.py <chapter_file> [section_title] [--force]")
        sys.exit(1)
    
    chapter_file = sys.argv[1]
    section_title = None
    force_regenerate = False
    
    if len(sys.argv) > 2:
        for arg in sys.argv[2:]:
            if arg == "--force" or arg == "-f":
                force_regenerate = True
            elif not arg.startswith("-"):
                section_title = arg
    
    # Run the section enhancer
    enhance_section(chapter_file, section_title, force_regenerate)