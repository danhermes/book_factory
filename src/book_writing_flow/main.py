#!/usr/bin/env python
import os
import sys
import time
import asyncio
import json
import logging

# Add the src directory to the Python path
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from pydantic import BaseModel

from crewai.flow import Flow, listen, start

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

from book_writing_flow.crews.Writer_crew.writer_crew import ChapterWriterCrew
from book_writing_flow.crews.Outline_crew.outline_crew import OutlineCrew
from book_writing_flow.config.book_config import RAG_CONTENT_FILES
from dotenv import load_dotenv

load_dotenv()

class Section(BaseModel):
    title: str = ""
    content: str = ""

class Chapter(BaseModel):
    title: str = ""
    content: str = ""
    sections: list[Section] = []

class BookState(BaseModel):
    topic: str = "ChatGPT for Business"
    total_chapters: int = 7
    titles: list[str] = []
    chapters: list[Chapter] = []


class BookFlow(Flow[BookState]):

    @start()
    def initialize(self):
        """Initialize the book state and create necessary directories"""
        print("Initializing book writing flow")
        # # Create chapters directory if it doesn't exist
        # if not os.path.exists("/output/chapters"):
        #     os.makedirs("/output/chapters")
        
        # Check for existing chapters and load them
        self.load_existing_chapters()
        
    def load_existing_chapters(self):
        """Load any existing chapters from the chapters directory"""
        if not os.path.exists("output/chapters"):
            return
            
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
                    
                    # Create a Chapter object and add to state
                    chapter = Chapter(title=title, content=chapter_content)
                    loaded_chapters.append((chapter_num, chapter))
                except Exception as e:
                    print(f"Error loading chapter {filename}: {e}")
        
        # Sort chapters by number and add to state
        loaded_chapters.sort(key=lambda x: x[0])
        self.state.chapters = [chapter for _, chapter in loaded_chapters]
        print(f"Loaded {len(self.state.chapters)} existing chapters")

    @listen(initialize)
    def generate_outline(self):
        logger.info("===== STARTING OUTLINE GENERATION =====")
        total_start_time = time.time()
        
        # Skip if we already have chapters loaded
        if self.state.chapters:
            logger.info("Chapters already loaded, skipping outline generation")
            # Extract titles from loaded chapters
            self.state.titles = [chapter.title for chapter in self.state.chapters]
            self.state.total_chapters = len(self.state.chapters)
            logger.info(f"Using {len(self.state.chapters)} existing chapters")
            return
        
        # Create and run the OutlineCrew
        logger.info("Creating OutlineCrew")
        crew_start_time = time.time()
        outline_crew = OutlineCrew()
        logger.info(f"OutlineCrew created in {time.time() - crew_start_time:.2f} seconds")
        
        # Log the RAG content files being used
        logger.info(f"RAG content files: {RAG_CONTENT_FILES}")
        
        logger.info("Creating crew instance")
        crew_instance_start = time.time()
        crew = outline_crew.crew()
        logger.info(f"Crew instance created in {time.time() - crew_instance_start:.2f} seconds")
        
        # Log the agents and tasks in the crew
        logger.info(f"Crew agents: {[agent.__class__.__name__ for agent in crew.agents]}")
        logger.info(f"Crew tasks: {[task.description[:50] + '...' for task in crew.tasks]}")
        
        logger.info("Starting crew kickoff with topic: " + self.state.topic)
        kickoff_start = time.time()
        try:
            outline = crew.kickoff(inputs={
                "topic": self.state.topic,
                "use_rag": True,
                "rag_files": list(RAG_CONTENT_FILES.keys())
            })
            kickoff_time = time.time() - kickoff_start
            logger.info(f"Crew kickoff completed in {kickoff_time:.2f} seconds")
            
            # Log the outline structure
            if hasattr(outline.pydantic, 'total_chapters'):
                logger.info(f"Outline has {outline.pydantic.total_chapters} chapters")
            
            if hasattr(outline.pydantic, 'chapters'):
                logger.info(f"Outline has {len(outline.pydantic.chapters)} chapters in 'chapters' attribute")
                for i, chapter in enumerate(outline.pydantic.chapters):
                    logger.info(f"Chapter {i+1}: {chapter.title} with {len(chapter.sections)} sections")
            
            self.state.total_chapters = outline.pydantic.total_chapters
            
            # Handle the new outline format with chapters and sections
            if hasattr(outline.pydantic, 'chapters'):
                logger.info("Using new outline format with chapters and sections")
                self.state.chapters = outline.pydantic.chapters
            else:
                # Backward compatibility with old format
                logger.info("Using old outline format with titles only")
                self.state.titles = outline.pydantic.titles
        except Exception as e:
            logger.error(f"Error during crew kickoff: {e}")
            logger.exception("Exception details:")
            raise
            
        total_time = time.time() - total_start_time
        logger.info(f"Total outline generation took {total_time:.2f} seconds")
        logger.info("===== OUTLINE GENERATION COMPLETE =====")

    @listen(generate_outline)
    def save_book_outline(self):
        logger.info("Saving book outline")
        # Ensure output directory exists
        os.makedirs("output/outlines", exist_ok=True)
        
        # Save directly to output/outlines directory
        with open("output/outlines/book_outline.md", "w") as f:
            f.write(f"# Book Outline: {self.state.topic}\n\n")
            
            # Check if we have the new format with chapters and sections
            if hasattr(self.state, 'chapters') and self.state.chapters:
                for i, chapter in enumerate(self.state.chapters, 1):
                    f.write(f"## Chapter {i}: {chapter.title}\n\n")
                    
                    for section in chapter.sections:
                        f.write(f"- {section.title}\n")
                    
                    f.write("\n")
            # Fallback to old format
            elif hasattr(self.state, 'titles') and self.state.titles:
                for i, title in enumerate(self.state.titles, 1):
                    if isinstance(title, dict):
                        # Dictionary format with sections
                        f.write(f"## {title['title']}\n\n")
                        for section in title['sections']:
                            f.write(f"- {section}\n")
                    else:
                        # Simple string format
                        title_text = title
                        # Remove "Chapter X: " if it already exists in the title
                        if title_text.startswith(f"Chapter {i}:"):
                            title_text = title_text[len(f"Chapter {i}:"):].strip()
                        f.write(f"## Chapter {i}: {title_text}\n")
                    
                    f.write("\n")
            
            f.write(f"\nTotal Chapters: {self.state.total_chapters}\n")
        
        # Also save as JSON for easier processing
        book_outline = {
            "total_chapters": self.state.total_chapters,
            "chapters": []
        }
        
        if hasattr(self.state, 'chapters') and self.state.chapters:
            for chapter in self.state.chapters:
                chapter_data = {
                    "title": chapter.title,
                    "sections": [{"title": section.title} for section in chapter.sections]
                }
                book_outline["chapters"].append(chapter_data)
        
        with open("output/outlines/book_outline.json", "w") as f:
            json.dump(book_outline, f, indent=2)
            
        logger.info("Book outline saved to output/outlines/book_outline.md and output/outlines/book_outline.json")

    @listen(generate_outline)
    async def generate_chapters(self):
        logger.info("Generating chapters")
        tasks = []

        async def write_single_chapter(chapter_index, title):
            # Skip if chapter already exists
            chapter_file = f"output/chapters/{chapter_index+1:02d}_{title.replace(' ', '_').replace(':', '_')}.md"
            if os.path.exists(chapter_file):
                logging.info(f"Chapter {chapter_index+1} already exists, skipping")
                with open(chapter_file, "r") as f:
                    content = f.read()
                    
                # Parse the content to extract title and chapter content
                lines = content.split("\n")
                title = lines[0].replace("# ", "")
                chapter_content = "\n".join(lines[1:])
                
                return Chapter(title=title, content=chapter_content)
            
            logging.info(f"MAIN: Generating chapter {chapter_index+1}: {title}")
            # Generate the chapter
            if hasattr(self.state, 'chapters') and self.state.chapters:
                logging.info("Kicking off with chapters: %s", [chapter.title for chapter in self.state.chapters])
            else:
                logging.info("Using fallback titles: %s", self.state.titles)

            result = (
                ChapterWriterCrew()
                .crew()
                .kickoff(inputs={
                    "title": title,
                    "topic": self.state.topic,
                    "chapters": [chapter.title for chapter in self.state.chapters] if hasattr(self.state, 'chapters') and self.state.chapters else self.state.titles
                })
            )
            
            # Save the chapter immediately
            chapter = result.pydantic
            with open(chapter_file, "w") as f:
                f.write("# " + chapter.title + "\n")
                f.write(chapter.content + "\n")
            
            print(f"Saved chapter {chapter_index+1} to {chapter_file}")
            return chapter

        # Create tasks for each chapter
        for i in range(self.state.total_chapters):
            title = self.state.titles[i] if hasattr(self.state, 'titles') and self.state.titles else f"Chapter {i+1}"
            task = asyncio.create_task(
                write_single_chapter(
                    i,
                    title
                )
            )
            tasks.append(task)

        # Wait for all chapters to be generated concurrently
        chapters = await asyncio.gather(*tasks)
        print(f"Generated {len(chapters)} chapters")
        self.state.chapters = chapters  # Replace with new chapters

    @listen(generate_chapters)
    def save_book(self):
        print("Saving complete book")
        # Ensure output directory exists
        os.makedirs("output", exist_ok=True)
        
        # Save book directly to output directory
        with open("output/book.md", "w") as f:
            for chapter in self.state.chapters:
                f.write("# " + chapter.title + "\n")
                f.write(chapter.content + "\n")
                
        print("Book saved to output/book.md")
        
        # Also save a JSON version with full state
        book_state = {
            "topic": self.state.topic,
            "total_chapters": self.state.total_chapters,
            "chapters": [
                {
                    "title": chapter.title,
                    "content": chapter.content,
                    "sections": [
                        {"title": section.title, "content": section.content}
                        for section in chapter.sections
                    ] if hasattr(chapter, 'sections') else []
                }
                for chapter in self.state.chapters
            ]
        }
        
        # Save book state directly to output directory
        with open("output/book_state.json", "w") as f:
            json.dump(book_state, f, indent=2)
            
        print("Book state saved to output/book_state.json")


def kickoff():
    book_flow = BookFlow()
    asyncio.run(book_flow.kickoff_async())


def generate_single_chapter_outline(chapter_index):
    """Generate an outline for a single chapter directly"""
    from book_writing_flow.crews.Outline_crew.outline_crew import OutlineCrew, Chapter, Section
    import logging
    
    logger = logging.getLogger("single_chapter_outline")
    logger.info(f"Generating outline for chapter {chapter_index} only")
    
    # Create a simplified BookFlow state with just one chapter
    book_flow = BookFlow()
    book_flow.state.topic = "ChatGPT for Business"
    book_flow.state.total_chapters = 1
    
    # Create and run the OutlineCrew for just this chapter
    logger.info("Creating OutlineCrew with RAG support")
    outline_crew = OutlineCrew()
    
    # Log the RAG content files being used
    from book_writing_flow.config.book_config import RAG_CONTENT_FILES
    logger.info(f"RAG content files: {RAG_CONTENT_FILES}")
    
    # Create the crew instance
    crew = outline_crew.crew()
    
    # Log RAG provider initialization
    from book_writing_flow.tools.rag_utils import RagContentProvider
    rag_provider = RagContentProvider(RAG_CONTENT_FILES)
    
    # Verify RAG content is accessible
    outline_content = rag_provider.get_file_content("outline")
    full_content = rag_provider.get_file_content("full_content")
    
    if outline_content:
        logger.info(f"Successfully loaded outline RAG content ({len(outline_content)} chars)")
    else:
        logger.warning("Failed to load outline RAG content")
        
    if full_content:
        logger.info(f"Successfully loaded full content RAG content ({len(full_content)} chars)")
    else:
        logger.warning("Failed to load full content RAG content")
    
    # Modify the kickoff inputs to specify we only want one chapter
    # and ensure we're using RAG content
    logger.info(f"Starting crew kickoff for chapter {chapter_index} with RAG enhancement")
    outline = crew.kickoff(inputs={
        "topic": book_flow.state.topic,
        "single_chapter": True,
        "chapter_number": chapter_index,
        "use_rag": True,
        "rag_files": list(RAG_CONTENT_FILES.keys())
    })
    
    # Extract the chapter from the result
    if hasattr(outline.pydantic, 'chapters') and outline.pydantic.chapters:
        chapter = outline.pydantic.chapters[0]
        
        # Create a single-chapter outline
        chapter_outline = {
            "total_chapters": 1,
            "chapters": [{
                "title": chapter.title,
                "sections": [{"title": section.title} for section in chapter.sections]
            }]
        }
        
        # Ensure output directory exists
        os.makedirs("output/outlines", exist_ok=True)
        
        # Save to JSON directly in output directory
        json_path = f"output/outlines/chapter{chapter_index}_outline.json"
        with open(json_path, "w") as f:
            json.dump(chapter_outline, f, indent=2)
        
        # Save to Markdown directly in output directory
        md_path = f"output/outlines/chapter{chapter_index}_outline.md"
        with open(md_path, "w") as f:
            f.write(f"# Chapter {chapter_index} Outline: {chapter.title}\n\n")
            
            for section in chapter.sections:
                f.write(f"- {section.title}\n")
            
            f.write("\n")
        
        print(f"Chapter outline saved to {json_path} and {md_path}")
        return True
    else:
        print("Failed to generate chapter outline")
        return False


def plot():
    book_flow = BookFlow()
    book_flow.plot()


if __name__ == "__main__":
    kickoff()
