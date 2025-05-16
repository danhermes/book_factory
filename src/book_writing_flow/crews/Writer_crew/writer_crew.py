from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import SerperDevTool
from pydantic import BaseModel
import os
import json
import re
import logging
from typing import List, Dict, Any, Optional
import yaml

from book_writing_flow.tools.custom_tool import BrightDataWebSearchTool
from book_writing_flow.tools.rag_utils import RagContentProvider

# Set up logger for this module
logger = logging.getLogger(__name__)
# Set the level to INFO to ensure messages are logged
logger.setLevel(logging.INFO)
# Don't add handlers here, let the root logger handle output

llm = LLM(model="gpt-4o")


class Section(BaseModel):
    """Section of a chapter"""
    chapter_title : str
    title: str
    type: str  # Introduction, Story, Topic Explanation, Bonus Topic, Big Box, Chapter Summary, Chapter Bridge, Outro
    content: str

class SectionInput(BaseModel):
    """Input for generating a section"""
    title: str
    type: str
    chapter_title: str
    chapter_number: int
    min_length: int
    structure: List[str]
    rag_content: str
    previous_section: Optional[str] = None
    next_section: Optional[str] = None

class Chapter(BaseModel):
    """Chapter of the book"""
    title: str
    content: str
    sections: list[Section] = []

@CrewBase
class ChapterWriterCrew:
    """Chapter Writer Crew"""

    def __init__(self):
        """Initialize the ChapterWriterCrew instance"""

        logger.info("📦 BEFORE CREW BUILD")

        with open("src/book_writing_flow/crews/Writer_crew/config/agents.yaml", "r") as f:
            self.agents_config = yaml.safe_load(f)

        with open("src/book_writing_flow/crews/Writer_crew/config/tasks.yaml", "r") as f:
            self.tasks_config = yaml.safe_load(f)
        
        #set self.agents as the section_writer agent issue nukes it for crewai
        self.agents = {}
        self.agents = {
        "section_writer": Agent(
            config=self.agents_config["section_writer"],
            llm=llm,
            verbose=True
        ),
        "writer": Agent(
            config=self.agents_config["writer"],
            llm=llm,
            verbose=True
        ),
        "topic_researcher": Agent(
            config=self.agents_config["topic_researcher"],
            llm=llm,
            verbose=True
        )}

        logger.info("🧠 self.agents keys before kickoff: %s", list(getattr(self, "agents", {}).keys()))
        logger.info("🧠 Does section_writer exist? %s", "section_writer" in getattr(self, "agents", {}))


        logger.info("ChapterWriterCrew initialized")


    @agent
    def topic_researcher(self) -> Agent:
        logger.info("Initializing topic_researcher agent")
        return Agent(config=self.agents_config["topic_researcher"],
                     tools=[BrightDataWebSearchTool()],
                     llm=llm)
    
    @agent
    def section_writer(self) -> Agent:
        """Agent responsible for writing individual sections"""
        logger.info("section_writer() method CALLED")
        logger.info("Initializing section_writer agent")
        return Agent(config=self.agents_config["section_writer"],
                     verbose=True,
                     llm=llm)
                     
    def get_rag_content(self, chapter_title, section_titles=None):
        """Get relevant RAG content for the chapter and its sections"""
        logger.info(f"Executing get_rag_content for chapter: {chapter_title}")
        # Initialize the RAG content provider
        rag_provider = RagContentProvider({
            "expanded_outline": "rag/ChatGPT_for_Business_Expanded_Outline.txt",
            "full_content": "rag/ChatGPT_for_Business_FULL_WITH_COVER.txt"
        })
        
        # Get chapter-level RAG content
        chapter_content = rag_provider.find_relevant_content(
            query=chapter_title,
            content_types=["expanded_outline", "full_content"],
            max_chunks=5,
            chunk_size=1500
        )
        
        # Get section-specific RAG content if section titles are provided
        section_content = {}
        if section_titles:
            for section_title in section_titles:
                section_query = f"{chapter_title} {section_title}"
                content = rag_provider.find_relevant_content(
                    query=section_query,
                    content_types=["expanded_outline", "full_content"],
                    max_chunks=3,
                    chunk_size=1000
                )
                if content:
                    section_content[section_title] = content
        
        return {
            "chapter_content": chapter_content,
            "section_content": section_content
        }
        
    @task
    def write_section(self) -> Task:
        """Task for writing a single section"""
        logger.info("Creating write_section task")
        return Task(
            config=self.tasks_config["write_section"],
            agent=self.agents["section_writer"],
            output_pydantic=Section
        )

    @task
    def research_topic(self) -> Task:
        """
        Override the research_topic task to focus on the outline structure.
        """
        logger.info("Creating research_topic task")
        # In the newer version of CrewAI, we can't modify the execute method
        # Instead, we'll use the task's config and context to provide the necessary information
        
        # Create a modified config with enhanced information if needed
        task_config = dict(self.tasks_config["research_topic"])
        
        # Add additional context information
        context_items = [
            {
                "key": "outline_path",
                "value": "output/outlines/book_outline.json",
                "description": "Path to the outline file",
                "expected_output": "A file path string"
            },
            {
                "key": "use_outline",
                "value": True,
                "description": "Whether to use the outline for enhanced content",
                "expected_output": "A boolean value"
            }
        ]
        
        # Try to enhance the task with outline information
        try:
            # Read the outline file
            import json
            import os
            
            # First try to load from output/outlines directory
            if os.path.exists("output/outlines/book_outline.json"):
                with open("output/outlines/book_outline.json", 'r') as f:
                    outline = json.load(f)
            # Fall back to root directory if not found in output/outlines
            elif os.path.exists("book_outline.json"):
                with open("book_outline.json", 'r') as f:
                    outline = json.load(f)
            else:
                raise FileNotFoundError("book_outline.json not found in output/outlines or root directory")
            
            # Add outline information to the task config
            task_config["additional_info"] = f"Outline with {len(outline.get('chapters', []))} chapters"
            
            # Extract chapter titles for reference
            chapter_titles = [chapter.get("title", "") for chapter in outline.get("chapters", [])]
            if chapter_titles:
                task_config["chapter_titles"] = ", ".join(chapter_titles)
        except Exception as e:
            logger.error(f"Error loading outline for research task: {e}")
        
        # Create the task with the enhanced config
        return Task(
            config=task_config,
            context=context_items
        )

    @agent
    def writer(self) -> Agent:
        logger.info("Initializing writer agent")
        return Agent(config=self.agents_config["writer"],
                     llm=llm)

    @task
    def write_chapter(self) -> Task:
        """
        Override the write_chapter task to generate each section separately
        and combine them into a complete chapter.
        """
        logger.info("Creating write_chapter task")
        
        async def execute(self, *args, **kwargs):
            """Custom execution logic to generate each section separately"""
            logger.info("Executing write_chapter task with section-by-section approach")
            
            # Get the chapter title from the inputs
            chapter_title = kwargs.get("title", "")
            chapter_number = 1  # Default to chapter 1
            
            # Try to extract chapter number from title
            match = re.search(r"Chapter (\d+)", chapter_title)
            if match:
                chapter_number = int(match.group(1))
            
            # Load the outline
            outline = None
            try:
                # First try to load from output/outlines directory
                if os.path.exists("output/outlines/book_outline.json"):
                    with open("output/outlines/book_outline.json", 'r') as f:
                        outline = json.load(f)
                # Fall back to root directory if not found in output/outlines
                elif os.path.exists("book_outline.json"):
                    with open("book_outline.json", 'r') as f:
                        outline = json.load(f)
                else:
                    raise FileNotFoundError("book_outline.json not found in output/outlines or root directory")
            except Exception as e:
                logger.error(f"Error loading outline: {e}")
                # Create a minimal outline with just the chapter title
                outline = {
                    "chapters": [
                        {
                            "title": chapter_title,
                            "sections": []
                        }
                    ]
                }
            
            # Find the matching chapter in the outline
            chapter_data = None
            for chapter in outline.get("chapters", []):
                if chapter_title in chapter.get("title", ""):
                    chapter_data = chapter
                    break
            
            if not chapter_data:
                logger.warning(f"Chapter '{chapter_title}' not found in outline")
                return Chapter(title=chapter_title, content="", sections=[])
            
            # Extract section information
            section_titles = []
            
            # Get the sections from the outline
            outline_sections = []
            for section in chapter_data.get("sections", []):
                section_title = section.get("title", "")
                outline_sections.append(section_title)
            
            # If no sections are found in the chapter data, try to parse them from the outline.md file
            if not outline_sections:
                try:
                    # Try to load the outline.md file
                    if os.path.exists("output/outlines/book_outline.md"):
                        with open("output/outlines/book_outline.md", "r") as f:
                            outline_md = f.read()
                        
                        # Find the chapter section
                        chapter_pattern = f"## Chapter {chapter_title.split(':')[0].strip()}: .*?\\n\\n(.*?)\\n\\n##"
                        chapter_match = re.search(chapter_pattern, outline_md, re.DOTALL)
                        
                        if chapter_match:
                            chapter_content = chapter_match.group(1)
                            # Extract section titles
                            section_lines = [line.strip() for line in chapter_content.split("\n") if line.strip().startswith("- ")]
                            outline_sections = [line[2:] for line in section_lines]
                except Exception as e:
                    logger.error(f"Error parsing outline.md: {e}")
            
            if not outline_sections:
                logger.warning(f"No sections found for chapter '{chapter_title}'")
                return Chapter(title=chapter_title, content="", sections=[])
            
            # Load section templates
            section_templates = {}
            try:
                if os.path.exists("section_templates.json"):
                    with open("section_templates.json", 'r') as f:
                        section_templates = json.load(f)
            except Exception as e:
                logger.error(f"Error loading section templates: {e}")
                # # Create default section templates
                # section_templates = {
                #     "Introduction": {
                #         "min_length": 600,
                #         "structure": ["Opening hook", "Context", "Preview of key concepts"]
                #     },
                #     "Story": {
                #         "min_length": 800,
                #         "structure": ["Company background", "Challenge", "Solution", "Results"]
                #     },
                #     "Topic Explanation": {
                #         "min_length": 700,
                #         "structure": ["Definition", "Key components", "Best practices"]
                #     },
                #     "Bonus Topic": {
                #         "min_length": 500,
                #         "structure": ["Introduction", "Key insights", "Applications"]
                #     },
                #     "Big Box": {
                #         "min_length": 900,
                #         "structure": ["Technical overview", "Implementation details", "Advanced concepts"]
                #     },
                #     "Outro": {
                #         "min_length": 500,
                #         "structure": ["Summary", "Key takeaways", "Future outlook"]
                #     },
                #     "Chapter Bridge": {
                #         "min_length": 300,
                #         "structure": ["Recap", "Connection to next chapter", "Preview"]
                #     }
                # }
            
            # Add debug logging
            logger.info("About to call get_rag_content")
            try:
                # Get RAG content for the chapter and sections using the stored instance
                rag_content = self._instance.get_rag_content(chapter_title, outline_sections)
                logger.info("Successfully got RAG content")
            except Exception as e:
                logger.error(f"Error in get_rag_content: {e}")
                raise
            
            # Generate a brief chapter introduction
            chapter_intro = f"# {chapter_title}\n\nThis chapter explores {chapter_title.split(':')[-1].strip()}.\n\n"
            
            # Generate each section separately
            sections = []
            for i, section_title in enumerate(outline_sections):
                logger.info(f"Generating section: {section_title}")
                
                # Determine section type
                section_type = "Unknown"
                if "(" in section_title and ")" in section_title:
                    section_type = section_title.split("(")[-1].split(")")[0]
                else:
                    # Try to infer section type from title
                    if "intro" in section_title.lower():
                        section_type = "Introduction"
                    elif any(company in section_title for company in ["WelcomeWell", "StackHaven", "FlexTax", "LeadFleet", "BriteTeam", "WestBridge", "BrightPath"]):
                        section_type = "Story"
                    elif "bonus" in section_title.lower():
                        section_type = "Bonus Topic"
                    elif "big box" in section_title.lower():
                        section_type = "Big Box"
                    elif "outro" in section_title.lower():
                        section_type = "Outro"
                    elif "transition" in section_title.lower() or "bridge" in section_title.lower():
                        section_type = "Chapter Bridge"
                    else:
                        section_type = "Topic Explanation"
                
                logger.info(f"Templating: {section_title}")               
                # Get section template
                template = section_templates.get(section_type, {
                    "min_length": 500,
                    "structure": ["Introduction", "Main content", "Conclusion"]
                })
                logger.info(f"TDonr Templating: {section_title}")   
                # Get section-specific RAG content
                section_rag = ""
                if section_title in rag_content["section_content"]:
                    section_rag = "\n\n".join(rag_content["section_content"][section_title])
                
                # Get surrounding sections for context
                prev_section = outline_sections[i-1] if i > 0 else None
                next_section = outline_sections[i+1] if i < len(outline_sections) - 1 else None
                
                # # Create section input
                # section_input = SectionInput(
                #     title=section_title,
                #     type=section_type,
                #     chapter_title=chapter_title,
                #     chapter_number=chapter_number,
                #     min_length=template["min_length"],
                #     structure=template["structure"],
                #     rag_content=section_rag,
                #     previous_section=prev_section,
                #     next_section=next_section
                # )
                
                # Generate the section using the section writer task
                logger.info(f"Creating task for section: {section_title} (type: {section_type})")
                try:
                    logger.info("About to call write_section")
                    #section_task = self._instance.write_section()
                    #section_task = self._instance.tasks["write_section"]
                    section_task = Task(
                            config=self.tasks_config["write_section"],
                            agent=self.agents["section_writer"],
                            output_pydantic=Section
                    )
                    logger.info("Successfully got section_task")
                except Exception as e:
                    logger.error(f"Error in write_section: {e}")
                    raise
                logger.info("🚀 chapter_title = %s", chapter_title)
        
                # Create a context dictionary with all the section-specific information
                section_context = {
                    "title": section_title,
                    "type": section_type,
                    "chapter_title": chapter_title,
                    "chapter_number": chapter_number,
                    "min_length": template["min_length"],
                    "structure": ", ".join(template["structure"]),  # Convert list to string for template
                    "rag_content": section_rag,
                    "previous_section": prev_section if prev_section else "None",
                    "next_section": next_section if next_section else "None"
                }
                
                # Execute the task with the context, which will apply the section-specific prompts
                section_result = await section_task.execute(**section_context)
                
                # Add the section to the list
                sections.append(Section(
                    chapter_title=chapter_title,
                    title=section_title,
                    type=section_type,
                    content=section_result.content
                ))
            
            # Combine all sections into a complete chapter
            logging.info("Cpmbine chapts")
            chapter_content = chapter_intro
            for section in sections:
                chapter_content += f"## {section.title}\n\n{section.content}\n\n"
            
            # Create the chapter
            chapter = Chapter(
                title=chapter_title,
                content=chapter_content,
                sections=sections
            )
            
            return chapter
        
        # Create the task with custom execution logic and use the configuration from tasks.yaml
        logging.info("define task")
        logger.warning("🚀 IN wriue chap: agents dict keys = %s", list(self.tasks_config.keys()))
        #logger.warning("🚀 IN erotw chap: section_writer agent = %s", self.agents.get("writer", "MISSING"))

        task = Task(
            config=self.tasks_config["write_chapter"],
            agent=self.agents["writer"],
            output_pydantic=Chapter
        )
        logging.info("wxwcutw task")
        # Set the custom execution method
        task.async_execution = execute.__get__(task, Task)
        
        return task

    @crew
    def crew(self) -> Crew:
        """Creates the Writer Crew"""
        logger.warning("🔥 @crew method CALLED")
        #logger.warning("🚀 IN CREW: agents dict keys = %s", list(self.agents.keys()))
        #logger.warning("🚀 IN CREW: section_writer agent = %s", self.agents.get("section_writer", "MISSING"))

        logger.info("Creating Writer Crew")
        return Crew(agents=self.agents,
                    tasks=self.tasks,
                    process=Process.sequential,
                    verbose=True)
