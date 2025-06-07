#!/usr/bin/env python
import os
import sys
import time
import asyncio
import json
import logging
from pydantic import BaseModel
from crewai.flow import Flow, listen, start
from book_writing_flow.crews.Writer_crew.writer_crew import ChapterWriterCrew
from book_writing_flow.crews.Outline_crew.outline_crew import OutlineCrew
from dotenv import load_dotenv
from book_writing_flow.tools.rag_utils import RagContentProvider
from output.book_config import RAG_CONTENT_FILES, BOOK_TITLE, BOOK_TOPIC
from book_writing_flow.book_model import Chapter, Section, BookModel

# Add the src directory to the Python path
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# Configure the Python path for relative imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("book_flow")
logger.info(f"RAG_CONTENT_FILES - book outline: {RAG_CONTENT_FILES['book_outline']}")
logger.info(f"RAG_CONTENT_FILES - chapter content: {RAG_CONTENT_FILES['chapter_content']}")

load_dotenv()

class BookState(BookModel):
    pass

class BookFlow(Flow[BookState]):
    
    def __init__(self):
        super().__init__()
        self.book_outline = BookState()
        self.book_outline.topic = BOOK_TOPIC
        self.book_outline.book_title = BOOK_TITLE
        self.book_outline.total_chapters = 0
        self.rag_chapter_content = ""
        self.rag_book_outline = ""
        
    @start()
    def initialize(self):
        logger.info("Initializing book writing flow")
        os.makedirs("/output/chapters", exist_ok=True)
        self.load_existing_chapters()
        
    def load_existing_chapters(self):
        logger.info("Loading existing chapters")
        loaded_chapters = []
        for filename in os.listdir("output/chapters"):
            if filename.endswith(".md"):
                try:
                    chapter_num = int(filename.split("_")[0])
                    with open(f"output/chapters/{filename}", "r") as f:
                        content = f.read()

                    # Parse the content to extract title and chapter content
                    lines = content.split("\n")
                    title = lines[0].replace("# ", "")
                    chapter_content = "\n".join(lines[1:])

                    chapter = Chapter(title=title, content=chapter_content)
                    loaded_chapters.append((chapter_num, chapter))
                except Exception as e:
                    logger.error(f"Error loading chapter {filename}: {e}")
        loaded_chapters.sort(key=lambda x: x[0])
        self.book_outline.chapters = [chapter for _, chapter in loaded_chapters]
        logger.info(f"Loaded {len(self.book_outline.chapters)} existing chapters")

    def load_rag_content(self):
        logger.info("Loading RAG content")
        """Load RAG content and update state with book outline and chapter content"""
        logger.info(f"RAG content files: {RAG_CONTENT_FILES}")
        rag_provider = RagContentProvider(RAG_CONTENT_FILES)
        self.rag_book_outline = rag_provider.get_file_content("book_outline")
        self.rag_chapter_content = rag_provider.get_file_content("chapter_content")
        
        if self.rag_book_outline:
            logger.info(f"Successfully loaded outline RAG content ({len(self.rag_book_outline)} chars)")
        else:
            logger.warning("Failed to load outline RAG content")
            
        if self.rag_chapter_content:
            logger.info(f"Successfully loaded full content RAG content ({len(self.rag_chapter_content)} chars)")
        else:
            logger.warning("Failed to load full content RAG content")
            
        return rag_provider
    
    @listen(initialize)
    def generate_outline(self):
        logger.info("===== STARTING OUTLINE GENERATION =====")
        total_start_time = time.time()
        self.load_rag_content()
        logger.info("Creating OutlineCrew")
        outline_crew = OutlineCrew() ##### Errors here are likely in the the prompt formatting/description/input/task definitions
        logger.info("Creating crew instance")
        crew = outline_crew.crew()
        logger.info(f"Crew agents: {[agent.__class__.__name__ for agent in crew.agents]}")
        logger.info(f"Crew tasks: {[task.description[:50] + '...' for task in crew.tasks]}")
        logger.info("Starting crew kickoff with topic: " + self.book_outline.topic)
        kickoff_start = time.time()
        try:
            outline = crew.kickoff(inputs={
                "topic": self.book_outline.topic,
                "book_title": self.book_outline.book_title,
                "book_outline": self.rag_book_outline,
                "chapter_content": self.rag_chapter_content
            })
           
            # Log the outline structure
            if hasattr(outline.pydantic, 'total_chapters'):
                logger.info(f"Outline has {outline.pydantic.total_chapters} chapters")
            if hasattr(outline.pydantic, 'chapters'):
                logger.info(f"Outline has {len(outline.pydantic.chapters)} chapters in 'chapters' attribute")
                for i, chapter in enumerate(outline.pydantic.chapters):
                    logger.info(f"Chapter {i+1}: {chapter.title} with {len(chapter.sections)} sections")
            self.book_outline.total_chapters = outline.pydantic.total_chapters
            if hasattr(outline.pydantic, 'chapters'):
                logger.info("Using new outline format with chapters and sections")
                #self.book_outline.chapters = outline.pydantic.chapters
                #*********************************** Assign the Outline from the crew to the state ***********************************
                #logger.info(f"Assigning outline to state: {outline.pydantic.chapters}")
                self.book_outline.chapters = [
                    Chapter(
                        title=ch.title,
                        content=ch.content,
                        sections=ch.sections
                    )
                    for ch in outline.pydantic.chapters
                ]
                logger.info(f"Assigning outline to state: {self.book_outline.chapters}")
                
                # Calculate and populate additional fields
                logger.info("Populating additional fields in book_outline")
                
                # Set total_chapters based on the number of chapters
                self.book_outline.total_chapters = len(self.book_outline.chapters)
                
                # Extract titles from chapters to populate book_outline.titles
                self.book_outline.titles = [chapter.title for chapter in self.book_outline.chapters]
                
                # Process each chapter and its sections
                for chapter_idx, chapter in enumerate(self.book_outline.chapters, 1):
                    # Set chapter number
                    chapter.number = chapter_idx
                    
                    # Set chapter number for each section
                    for section_idx, section in enumerate(chapter.sections, 1):
                        # Set chapter_title from parent chapter
                        section.chapter_title = chapter.title
                        
                        # Set chapter_number and section_number
                        section.chapter_number = chapter_idx
                        section.section_number = section_idx
                        
                        # Set previous_section and next_section
                        if section_idx > 1:
                            section.previous_section = chapter.sections[section_idx-2].section_title
                        if section_idx < len(chapter.sections):
                            section.next_section = chapter.sections[section_idx].section_title
                
                logger.info(f"Populated additional fields: total_chapters={self.book_outline.total_chapters}, titles count={len(self.book_outline.titles)}")
            else:
                # Backward compatibility with old format
                logger.info("Using old outline format with titles only")
                self.titles = outline.pydantic.titles
        except Exception as e:
            logger.error(f"Error during crew kickoff: {e}")
            logger.exception("Exception details:")
            raise
        logger.info("===== OUTLINE GENERATION COMPLETE =====")

    @listen(generate_outline)
    def save_book_outline(self):
        logger.info("Saving book outline")
        os.makedirs("output/outlines", exist_ok=True)
        with open("output/outlines/book_outline.md", "w") as f:
            f.write(f"# Book Outline: {self.book_outline.topic}\n\n")
            
            # Check if we have the new format with chapters and sections
            for i, chapter in enumerate(self.book_outline.chapters, 1):
                f.write(f"## {chapter.title}\n\n") #Chapter {i}:
                logger.info(f"Saving chapter: {chapter.title}")
                for section in chapter.sections:
                    if isinstance(section, Section):
                        f.write(f"- {section.section_title} ({section.type})\n")
                        logger.info(f"Saving section: {section.section_title} ({section.type})")
                    else:
                        logger.warning(f"Section is not a Section object: {section}")
                f.write("\n")
            
            f.write(f"\nTotal Chapters: {self.book_outline.total_chapters}\n")
        
        # Save book_outline directly to JSON
        with open("output/outlines/book_outline.json", "w") as f:
            # Convert Pydantic model to dict before serializing (using model_dump for Pydantic v2)
            json.dump(self.book_outline.model_dump(), f, indent=2)
            
        logger.info("Book outline saved to output/outlines/book_outline.md and output/outlines/book_outline.json")

    # #@listen(generate_outline)
    # async def generate_chapters(self):
    #     logger.info("Generating chapters")
    #     tasks = []

    #     async def write_single_chapter(chapter_index, title):
    #         # Skip if chapter already exists
    #         chapter_file = f"output/chapters/{chapter_index+1:02d}_{title.replace(' ', '_').replace(':', '_')}.md"
    #         if os.path.exists(chapter_file):
    #             logging.info(f"Chapter {chapter_index+1} already exists, skipping")
    #             with open(chapter_file, "r") as f:
    #                 content = f.read()
                    
    #             # Parse the content to extract title and chapter content
    #             lines = content.split("\n")
    #             title = lines[0].replace("# ", "")
    #             chapter_content = "\n".join(lines[1:])
                
    #             return Chapter(title=title, content=chapter_content)
            
    #         logging.info(f"MAIN: Generating chapter {chapter_index+1}: {title}")
    #         # Generate the chapter
    #         if hasattr(self.book_outline, 'chapters') and self.book_outline.chapters:
    #             logging.info("Kicking off with chapters: %s", [chapter.title for chapter in self.book_outline.chapters])
    #         else:
    #             logging.info("Using fallback titles: %s", self.titles)
    #         section_titles = [section.title for section in self.book_outline.chapters[chapter_index].sections]
    #         logger.info(f"Chapter {chapter_index+1} - Section titles: {section_titles}")
    #         result = (
    #             ChapterWriterCrew()
    #             .crew()
    #             .kickoff(inputs={
    #                 "title": title,
    #                 "outline_sections": section_titles,
    #                 "topic": self.book_outline.topic,
    #                 "chapters": [chapter.title for chapter in self.book_outline.chapters] if hasattr(self.book_outline, 'chapters') and self.book_outline.chapters else self.titles
    #             })
    #         )
            
    #         # Save the chapter immediately
    #         chapter = result.pydantic
    #         with open(chapter_file, "w") as f:
    #             f.write("# " + chapter.title + "\n")
    #             f.write(chapter.content + "\n")
            
    #         logger.info(f"Saved chapter {chapter_index+1} to {chapter_file}")
    #         return chapter

    #     # Create tasks for each chapter
    #     for i in range(self.book_outline.total_chapters):
    #         title = self.titles[i] if hasattr(self, 'titles') and self.titles else f"Chapter {i+1}"
    #         task = asyncio.create_task(
    #             write_single_chapter(
    #                 i,
    #                 title
    #             )
    #         )
    #         tasks.append(task)

    #     # Wait for all chapters to be generated concurrently
    #     chapters = await asyncio.gather(*tasks)
    #     logger.info(f"Generated {len(chapters)} chapters")
    #     self.book_outline.chapters = chapters  # Replace with new chapters

    # @listen(generate_chapters)
    # def save_book(self):
    #     logging.info("Saving complete book")
    #     # Ensure output directory exists
    #     os.makedirs("output", exist_ok=True)
        
    #     # Save book directly to output directory
    #     with open("output/book.md", "w") as f:
    #         for chapter in self.book_outline.chapters:
    #             f.write("# " + chapter.title + "\n")
    #             f.write(chapter.content + "\n")
                
    #     logging.info("Book saved to output/book.md")
        
    #     # Also save a JSON version with full state
    #     book_state = {
    #         "topic": self.book_outline.topic,
    #         "total_chapters": self.book_outline.total_chapters,
    #         "chapters": [
    #             {
    #                 "title": chapter.title,
    #                 "content": chapter.content,
    #                 "sections": [
    #                     {"title": section.section_title, "type": section.type, "content": section.content}
    #                     for section in chapter.sections
    #                 ] if hasattr(chapter, 'sections') else []
    #             }
    #             for chapter in self.book_outline.chapters
    #         ]
    #     }
        
    #     # Save book state directly to output directory
    #     with open("output/book_state.json", "w") as f:
    #         json.dump(book_state, f, indent=2)
            
    #     logger.info("Book state saved to output/book_state.json")


def kickoff(book_flow=None):
    if book_flow is None:
        book_flow = BookFlow()
    asyncio.run(book_flow.kickoff_async())


# def generate_single_chapter_outline(chapter_index):
#     """Generate an outline for a single chapter directly"""
#     from book_writing_flow.crews.Outline_crew.outline_crew import OutlineCrew, Chapter, Section
#     import logging
    
#     logger = logging.getLogger("single_chapter_outline")
#     logger.info(f"Generating outline for chapter {chapter_index} only")
    
#     # Create a simplified BookFlow state with just one chapter
#     book_flow = BookFlow()
# book_flow.book_outline.topic = "ChatGPT for Business"
# book_flow.book_outline.book_title = "ChatGPT for the Office"
# book_flow.book_outline.total_chapters = 1
    
#     # Create and run the OutlineCrew for just this chapter
#     logger.info("Creating OutlineCrew with RAG support")
#     outline_crew = OutlineCrew()
    
#     # Load RAG content
#     book_flow.load_rag_content()
    
#     # Create the crew instance
#     crew = outline_crew.crew()
    
#     # Modify the kickoff inputs to specify we only want one chapter
#     # and ensure we're using RAG content
#     logger.info(f"Starting crew kickoff for chapter {chapter_index} with RAG enhancement")
# outline = crew.kickoff(inputs={
#         "topic": book_flow.book_outline.topic,
#         "book_title": book_flow.book_outline.book_title,
#         "single_chapter": True,
#         "chapter_number": chapter_index,
#         "rag_files": list(RAG_CONTENT_FILES.keys())
#     })
    
#     # Extract the chapter from the result
#     if hasattr(outline.pydantic, 'chapters') and outline.pydantic.chapters:
#         chapter = outline.pydantic.chapters[0]
        
#         # Create a single-chapter outline
#         chapter_outline = {
#             "total_chapters": 1,
#             "chapters": [{
#                 "title": chapter.title,
#                 "sections": [{"title": section.title} for section in chapter.sections]
#             }]
#         }
        
#         # Ensure output directory exists
#         os.makedirs("output/outlines", exist_ok=True)
        
#         # Save to JSON directly in output directory
#         json_path = f"output/outlines/chapter{chapter_index}_outline.json"
#         with open(json_path, "w") as f:
#             json.dump(chapter_outline, f, indent=2)
        
#         # Save to Markdown directly in output directory
#         md_path = f"output/outlines/chapter{chapter_index}_outline.md"
#         with open(md_path, "w") as f:
#             f.write(f"# Chapter {chapter_index} Outline: {chapter.title}\n\n")
            
#             for section in chapter.sections:
#                 f.write(f"- {section.title}\n")
            
#             f.write("\n")
        
#         print(f"Chapter outline saved to {json_path} and {md_path}")
#         return True
#     else:
#         print("Failed to generate chapter outline")
#         return False


# def plot():
#     book_flow = BookFlow()
#     book_flow.plot()


if __name__ == "__main__":
    import argparse
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Book Writing Flow")
    parser.add_argument("--topic", type=str, default=BOOK_TOPIC,
                        help="Book topic")
    parser.add_argument("--book-title", type=str, default=BOOK_TITLE,
                        help="Book title")
    args = parser.parse_args()
    
    # Create BookFlow instance and set topic and book_title
    book_flow = BookFlow()
    book_flow.book_outline.topic = args.topic
    book_flow.book_outline.book_title = args.book_title
    
    # Kickoff the flow with our configured book_flow instance
    kickoff(book_flow)
