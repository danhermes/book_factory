from pprint import pformat
from pydantic import Field
import sys
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

# Add the src directory to the Python path
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if src_path not in sys.path:
    sys.path.insert(0, src_path)
from tools.rag_utils import RagContentProvider
from book_model import BookModel, Chapter, Section

src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if src_path not in sys.path:
    sys.path.insert(0, src_path)
from book_model import Chapter, Section

src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
if src_path not in sys.path:
    sys.path.insert(0, src_path)
from output.book_config import RAG_CONTENT_FILES

# from src.book_writing_flow.tools.custom_tool import BrightDataWebSearchTool
# from src.book_writing_flow.tools.rag_utils import RagContentProvider

# Set up logger for this module
logger = logging.getLogger(__name__)
# Set the level to INFO to ensure messages are logged
logger.setLevel(logging.INFO)

# Add file handler for logging to a file
import os
from logging.handlers import RotatingFileHandler
# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)
# Create a file handler for this module
file_handler = RotatingFileHandler(
    "logs/writer_crew.log",
    mode="w",
    maxBytes=10485760,  # 10MB
    backupCount=5,      # Keep 5 backup logs
    encoding="utf-8"
)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)
# Don't add handlers here, let the root logger handle output

# class Section(BaseModel):
#     """Section of a chapter"""
#     chapter_title : str
#     title: str
#     type: str  # Introduction, Story, etc.
#     content: str

# class SectionInput(BaseModel):
#     """Input for generating a section"""
#     title: str
#     type: str
#     chapter_title: str
#     chapter_number: int
#     min_length: int
#     structure: List[str]
#     rag_content: str
#     previous_section: Optional[str] = None
#     next_section: Optional[str] = None

# class Chapter(BaseModel):
#     """Chapter of the book"""
#     title: str
#     content: str
#     sections: list[Section] = []

@CrewBase
class ChapterWriterCrew:
    """Chapter Writer Crew"""

    def __init__(self, chapter_number, chapter_title):
        """Initialize the ChapterWriterCrew instance"""
        self.chapter_number = chapter_number
        self.chapter_title = chapter_title
        with open("src/book_writing_flow/crews/Writer_crew/config/agents.yaml", "r", encoding='utf-8') as f:
            self.agents_config = yaml.safe_load(f)
        with open("src/book_writing_flow/crews/Writer_crew/config/tasks.yaml", "r", encoding='utf-8') as f:
            self.tasks_config = yaml.safe_load(f)
        logger.info("ChapterWriterCrew initialized")
        self.llm = LLM(model="gpt-4o")
        self._inputs = None

    @agent
    def topic_researcher(self) -> Agent:
        logger.info("Initializing topic_researcher agent")
        return Agent(config=self.agents_config["topic_researcher"],
                     llm=self.llm)
    
    @agent
    def section_writer(self) -> Agent:
        logger.info("Initializing section_writer agent")
        return Agent(config=self.agents_config["section_writer"],
                     verbose=True,
                     llm=self.llm)
    
    def load_rag_content(self, chapter_title, sections=None):
        logger.info("Loading RAG content")
        logger.info(f"load_rag_content - chapter_title: {chapter_title}")
        logger.info(f"load_rag_content - sections: {sections}")
        """Load RAG content and update state with book outline and chapter content"""
        logger.info(f"RAG content files: {RAG_CONTENT_FILES}")
        rag_provider = RagContentProvider(RAG_CONTENT_FILES)
    
        # Get chapter-level RAG content
        logger.info(f"Calling chapter find_relevant_content with chapter_title: {chapter_title}")
        chapter_content = rag_provider.find_relevant_content(
            query=chapter_title,
            content_types=["book_outline", "chapter_content"],
            max_chunks=5,
            chunk_size=1500
        )
        
        # Get section-specific RAG content if section titles are provided
        logger.info(f"Get section-specific RAG content")
        section_content = ""
        if sections:
            for section in sections:
                # Check if section is a dict or a Section object
                if isinstance(section, dict):
                    section_title_val = section.get('section_title', '')
                else:
                    # It's a Section object, access attributes directly
                    section_title_val = section.section_title if hasattr(section, 'section_title') else ''
                
                logger.info(f"Calling section find_relevant_content with chapter_title: {chapter_title}")
                logger.info(f"Calling section find_relevant_content with section_title: {section_title_val}")
                section_query = f"{chapter_title} {section_title_val}"
                logger.info(f"section_query: {section_query}")
                content = rag_provider.find_relevant_content(
                    query=section_query, #todo pass in Section
                    content_types=["book_outline", "chapter_content"],
                    max_chunks=3,
                    chunk_size=1000
                )
                if content:
                    section_content = content
        
        return {
            "chapter_content": chapter_content,
            "section_content": section_content
        }
        
    @task
    def research_topic(self) -> Task:
        """
        Override the research_topic task to focus on the outline structure.
        """       
        logger.info(f"Researching...")  
        research_task_config = dict(self.tasks_config["research_topic"])
        # First try to load from output/outlines directory
        if os.path.exists("output/outlines/book_outline.json"):
            with open("output/outlines/book_outline.json", 'r', encoding='utf-8') as f:
                outline = json.load(f)
        # Fall back to root directory if not found in output/outlines
        elif os.path.exists("book_outline.json"):
            with open("book_outline.json", 'r', encoding='utf-8') as f:
                outline = json.load(f)
        else:
            raise FileNotFoundError("book_outline.json not found in output/outlines or root directory")
        
        # Create the task with the enhanced config
        return Task(
            config=self.tasks_config['research_topic']
        )

    @agent
    def writer(self) -> Agent:
        logger.info("Initializing writer agent")
        return Agent(config=self.agents_config["writer"],
                     llm=self.llm)

    @crew
    def crew(self) -> Crew:
        """Creates the Writer Crew"""
        logger.warning("🔥 @crew method CALLED")            
        instance = self
       
        # Create a callback to store inputs
        def on_kickoff(crew_instance, inputs=None):
            # Store the inputs for access by tasks
            logger.info(f"on_kickoff")
            if inputs:
                logger.info(f"Storing inputs: {inputs}")
                self._inputs = inputs

        logger.info("Creating Writer Crew")
        return Crew(agents=self.agents,
                    tasks=self.tasks,
                    process=Process.sequential,
                    verbose=True,
                    callbacks={"on_kickoff": on_kickoff})

class write_chapter_task: #Not Task, Not Baseclass
    """
    Override the write_chapter task to generate each section separately
    and combine them into a complete chapter.
    """
    description: str = ""
    expected_output: str = ""
    config: dict = {}
    research_content: str = ""
    llm: LLM = LLM(model="gpt-4o")
    tasks_config: dict = {} # = Field(default_factory=dict)
    agents_config: dict = {} # = Field(default_factory=dict)
    context_key_values: List[Dict] = [] # = Field(default_factory=list)
    research_content: str = ""

    
    def __init__(self, description, expected_output, config, research_content, chapter_title, chapter_number):#**kwargs):
        logger.info("Starting write_chapter_task __init__")
        self.chapter_title = chapter_title
        self.chapter_number = chapter_number
        self.description = description
        logger.info(f"write_chapter_task __init__ - description assigned.")
        self.expected_output = expected_output
        self.agents_config = config
        self.research_content = research_content
        logger.info(f"write_chapter_task __init__ - llm assigned.")
        #self.llm = LLM(model="gpt-4o")
        #super().__init__(description=description, expected_output=expected_output, config=config, research_content=research_content, **kwargs)
        logger.info(f"write_chapter_task __init__ - selfs assigned.")
        # Extract tasks_config before it's passed to super or potentially used by other logic in kwargs
        #kwargs["tasks_config"] = config
        # self.tasks_config = tasks
        # self.agents_config = agents
        self.research_content = research_content
        # Initialize the parent Task class with remaining kwargs
        logger.info("Creating write_chapter task")

        if self.tasks_config is None:
            logger.error("CRITICAL - write_chapter_task __init__: 'tasks_config' was not provided during instantiation. "
                         "self.tasks_config will be an empty dictionary. "
                         "This will likely lead to errors when trying to access specific task configurations like 'write_section' in the execute() method.")
            self.tasks_config = {} # Initialize to empty dict to prevent immediate NoneType error later.

        # self.context_key_values = []     # Initialize self.context as an empty list before appending
        # logger.info("isinstance")
        # inputs = kwargs.get('inputs', {})
        # if isinstance(inputs, dict):
        #     for key, value in inputs.items():
        #         self.context_key_values.append({
        #             "key": key,
        #             "value": value,
        #             "description": f"Input for {key}"
        #         })
        #else:
            #logger.error(f"Expected 'inputs' to be a dict, got {type(inputs).__name__}: {inputs}")
            #logger.info(f"Added inputs to context: {list(kwargs.get('inputs', {}).keys())}")

    async def execute(self):
        """Custom execution logic to generate each section separately"""
        
        logger.info("Executing write_chapter task with section-by-section approach")
        
        # # Get the chapter title from the task's context
        # chapter_title = "Unknown Chapter"
        # for item in self.context_key_values:
        #     if item.get("key") == "chapter_title":
        #         chapter_title = item.get("value")
        #         break
        
        # Log the chapter title for debugging
        logger.info(f"execute - write_chapter_task - Using chapter title: {self.chapter_title}")
        
        # Important: We must use the exact section titles from the book_outline.md file
        # This ensures the generated chapter matches the outline exactly
        logger.info("Using exact section titles from the book outline")
         
        # Load the outline
        outline = None
        try:
            # First try to load from output/outlines directory
            if os.path.exists("output/outlines/book_outline.json"):
                with open("output/outlines/book_outline.json", 'r', encoding='utf-8') as f:
                    #outline = json.load(f)
                    outline_dict = json.load(f)
                    outline = BookModel(**outline_dict) 
            # Fall back to root directory if not found in output/outlines
            elif os.path.exists("book_outline.json"):
                with open("book_outline.json", 'r', encoding='utf-8') as f:
                    #outline = json.load(f)
                    outline_dict = json.load(f)
                    outline = BookModel(**outline_dict)
            else:
                raise FileNotFoundError("book_outline.json not found in output/outlines or root directory")
        except Exception as e:
            logger.error(f"Error loading outline: {e}")
            # Create a minimal outline with just the chapter title
            outline = {
                "chapters": [
                    {
                        "title": self.chapter_title,
                        "sections": []
                    }
                ]
            }

        # Load the research log file for this chapter
        #chapter_number = 1  # Default to chapter 1
        
        # Try to extract chapter number from title using regex
        # Log the chapter title for debugging
        logger.info(f"Extracting chapter number from title: '{self.chapter_title}'")

        chapter_data = outline.chapters[self.chapter_number - 1]
        outline_sections = chapter_data.sections or []
        logger.info(f"outline_sections: {outline_sections}")
        
        if not chapter_data:
            logger.warning(f"Chapter '{self.chapter_title}' not found in outline")
            return Chapter(title=self.chapter_title, content="", sections=[])
        
        # If no sections are found in the chapter data, try to parse them from the outline.md file
        if not outline_sections:
            logger.info(f"No sections found for chapter. Parse the '{self.chapter_title}' from the outline.md file")
            try:
                # Try to load the outline.md file
                if os.path.exists("output/outlines/book_outline.md"):
                    with open("output/outlines/book_outline.md", "r", encoding='utf-8') as f:
                        outline_md = f.read()
                    
                    # Find the chapter section
                    chapter_pattern = f"## Chapter {self.chapter_title.split(':')[0].strip()}: .*?\\n\\n(.*?)\\n\\n##"
                    chapter_match = re.search(chapter_pattern, outline_md, re.DOTALL)
                    
                    if chapter_match:
                        chapter_content = chapter_match.group(1)
                        # Extract section titles
                        section_lines = [line.strip() for line in chapter_content.split("\n") if line.strip().startswith("- ")]
                        outline_sections = [line[2:] for line in section_lines]
            except Exception as e:
                logger.error(f"Error parsing outline.md: {e}")
        
        if not outline_sections:
            logger.warning(f"No sections found for chapter '{self.chapter_title}'")
            return Chapter(title=self.chapter_title, content="", sections=[])
        
        # # Load section templates --------------------- Do this in the prompt!!!!!!!
        # section_templates = {}
        # try:
        #     if os.path.exists("section_templates.json"):
        #         with open("section_templates.json", 'r') as f:
        #             section_templates = json.load(f)
        # except Exception as e:
        #     logger.error(f"Error loading section templates: {e}")
 
        # Add debug logging
        # logger.info("About to call load_rag_content")
        try:
        #     # Get RAG content for the chapter and sections using the stored instance
            logger.info(f"Calling load_rag_content with chapter_title: {self.chapter_title}")
            rag_content = ChapterWriterCrew(self.chapter_number, self.chapter_title).load_rag_content(self.chapter_title, outline_sections)
            logger.info("Successfully got RAG content")
        except Exception as e:
             logger.error(f"Error in load_rag_content: {e}")
             raise
        
        # Generate a brief chapter introduction
        chapter_intro = f"# {self.chapter_title}\n\nThis chapter explores {self.chapter_title.split(':')[-1].strip()}.\n\n"
        
        # Generate each section separately
        next_section_number = 0
        sections = []
        for section in chapter_data.sections:
            logger.info(f"Section class:\n{pformat(section.model_dump())}")
            section.section_number = next_section_number
            next_section_number += 1
            section_title = section.section_title
            section_type = section.type
            logger.info(f"Generating section: {section_title}")
            logger.info(f"Section type: {section_type}")    
          
            #Get section-specific RAG content
            section_rag = ""
            if section_title in rag_content["section_content"]:
                section_rag = "\n\n".join(rag_content["section_content"][section_title])
            
            # Get surrounding sections for context
            i = section.section_number
            logger.info(f"section_number: {section.section_number}")
            prev_section = outline_sections[i-1] if i > 0 else None
            next_section = outline_sections[i+1] if i < len(outline_sections) - 1 else None
            
            # Generate the section using the section writer task
            logger.info(f"Creating task for section: {section_title} (type: {section_type})")
            try:
  
                escaped_title = re.escape(section_title.strip())
            #                 logger.info(f"Escaped section title: '{escaped_title}'")
                pattern = rf"^##\ {escaped_title}\n(.*?)(?=^## |\Z)"
                logger.info(f"Full regex pattern: '{pattern}'")
                match = []
                match = re.search(pattern, self.research_content, re.DOTALL | re.MULTILINE)
                logger.info(f"Match: {match}")

                if match:
                    section_research = match.group(0).strip()
                    logger.info(f"Match found! Section research length: {len(section_research)}")
                else:
                    # If no exact match, use the whole research
                    section_research = self.research_content
                    logger.info("No match found, using entire research content")
            #         else:
            #             logger.info(f"Research file does not exist: {research_log_file}")
            #         #logging.info(f"***** section_research: {section_research}")
            #         #logger.info(f"***** section_research length: {len(section_research)}")
            #     except Exception as e:
            #         logger.error(f"Error loading research for section {section_title}: {e}")

                logger.info("Create section Task")
                # # Get the agents from the task's inputs
                # agents = None
                # for item in self.context_key_values:
                #     if item.get("key") == "agents":
                #         agents = item.get("value")
                #         break
                # if not agents:
                #     raise ValueError("No agents found in task inputs")
                
                # logger.info(f"***+++ Research file exists: {os.path.exists(research_log_file)}")
                # if os.path.exists(research_log_file):
                #     logger.info(f"Research file size: {os.path.getsize(research_log_file)} bytes")
                #     #logger.info(f"First 200 chars of research content: {research_content}")
                #     logger.info(f"Section-specific research found: {bool(match)}")
                #     logger.info(f"Section base title: {section_title}")
                #     logger.info(f"Section research length: {len(section_research)}")
                #     logger.info(f"****** Section research: {section_research}")
                #     logger.info(f"***---")
                #     logger.info(f"📦 tasks_config keys: {list(self.tasks_config.keys())}")
                section_writer_config = self.agents_config['section_writer']
                section_writer_agent = Agent(
                    role=section_writer_config["role"],
                    goal=section_writer_config["goal"],
                    backstory=section_writer_config["backstory"]
                )
                # Create the task with the agent
                section_task = Task(
                        description=self.description, #self.tasks_config["write_section"]["description"], #"Write the {title} section for the chapter.", # using the section research *{section_research}* and the ChatGPT prompts verbatim found in the researched stories.",
                        expected_output=self.expected_output, #self.tasks_config["write_section"]["expected_output"], #"A well-written section with appropriate content",
                        agent=section_writer_agent   
                )
                logger.info("Successfully got section_task")
            except Exception as e:
                logger.error(f"Error in write_section: {e}")
                raise
            logger.info("🚀 chapter_title = %s", self.chapter_title)
    
            # Create a local crew instance for this section
            # Create the section crew with the section_writer_agent
            # logger.info(f"Creating section crew with agents: {self.agents_config['section_writer']}")

            logger.info(f"Initiating the writing crew")
            section_crew = Crew(
                agents=[section_writer_agent],
                tasks=[section_task],
                process=Process.sequential,
                verbose=True
            )

            # x=Crew(agents=self.agents,
            #             tasks=self.tasks,
            #             process=Process.sequential,
            #             verbose=True)
            # context_items.append({
            #         "key": "sections",
            #         "value": sections,
            #         "description": f"Exact section titles and types for chapter: {chapter_title}",
            #         "expected_output": "A list of section information"
            #     })
            # # Create the task with the enhanced config
            # return Task(
            #   config=task_config,
            #   context=context_items
            # )
            #crew.kickoff(inputs={'topic': 'AI Agents'})
            #https://docs.crewai.com/concepts/tasks#yaml-configuration-recommended
            #CrewAI inserting input fields into prompts. Use input in Kickoff and format-like curlybraces in prompts.
            #https://www.google.com/search?q=crewai+insert+input+fields+into+task+prompt&sca_esv=3c74e91ebde8004a&biw=1955&bih=897&sxsrf=AHTn8zoOMnHBkWTdEOk99XHadsIUsycyUg%3A1747996452160&ei=JE8waMrFCYf9ptQPsaWFqAM&oq=crewai+insert+input+fields&gs_lp=Egxnd3Mtd2l6LXNlcnAiGmNyZXdhaSBpbnNlcnQgaW5wdXQgZmllbGRzKgIIADIFECEYoAEyBRAhGKABMgUQIRirAjIFECEYqwIyBRAhGKsCSIj6AlDUzQJYh-MCcAJ4AZABAJgBcaABlgiqAQQxMC4yuAEDyAEA-AEBmAIOoALFCMICChAAGLADGNYEGEfCAgQQIxgnwgIFEAAY7wXCAggQABiiBBiJBcICCBAAGIAEGKIEmAMAiAYBkAYIkgcEMTIuMqAH-zqyBwQxMC4yuAe8CMIHBjAuMTEuM8gHIA&sclient=gws-wiz-serp
            #Task(context=[research_task]  # This task will wait for research_task to complete
            # Execute the section crew and get the result
            logger.info(f"Kicking off section crew with inputs: {section_title}")
            section_result = section_crew.kickoff(
                                        inputs={
                                "title": section_title,  # Use section_title instead of chapter_title
                                "section_type": section_type,
                                "chapter_title": self.chapter_title,
                                #"min_length": template["min_length"], #todo from JSON?
                                # "structure": ", ".join(template["structure"]),  # Convert list to string for template
                                "section_research": section_research,
                                "rag_content": section_rag,
                                "previous_section": prev_section.section_title if prev_section else "None",
                                "next_section": next_section.section_title if next_section else "None"
                        }
            )
            logger.info(f"Kickoff completed")
            logger.info(f"SECTION RESULT!!::: {section_result}")
            # Extract the section from the CrewOutput object
            # The result is in the pydantic attribute
            section_content = None
            # if hasattr(section_result, 'pydantic'):
            #     logger.info(f"SECTION RESULT ---- Pydantic")
            #     section_content = section_result #.pydantic
            # else:
            logger.info(f"section_result type: {type(section_result)}")
            logger.info(f"SECTION RESULT ---- Section class")
            # Create a default section if we couldn't extract it
            section_content = Section(
                chapter_title=self.chapter_title,
                section_title=section_title,
                type=section_type,
                content=section_result.raw 
            )
                
            logger.info(f"Generated section: {section_content.section_title} with content length: {len(section_content.content) if hasattr(section_content, 'content') else 0}")
            sections.append(section_content)
        
        # Combine all sections into a complete chapter
        logging.info("Combining chapter sections")
        #chapter_content = f"## Chapter {self.chapter_number}: {self.chapter_title}\n\n"
        chapter_content = ""
        chapter_content += f"{chapter_intro}\n\n"
        for section in sections:
            chapter_content += f"## {section.section_title}\n\n{section.content}\n\n"
               
        # Create the chapter object
        chapter = Chapter(
            title=self.chapter_title,
            content=chapter_content,
            sections=sections
        )
        
        return chapter
    
    # def load_rag_content(self):
    #         logger.info("Loading RAG content")
    #         """Load RAG content and update state with book outline and chapter content"""
    #         logger.info(f"RAG content files: {RAG_CONTENT_FILES}")
    #         rag_provider = RagContentProvider(RAG_CONTENT_FILES)
    #         # self.state.book_outline = rag_provider.get_file_content("book_outline")
    #         # self.state.chapter_content = rag_provider.get_file_content("chapter_content")
            
    #         if self.state.book_outline:
    #             logger.info(f"Successfully loaded outline RAG content ({len(self.state.book_outline)} chars)")
    #         else:
    #             logger.warning("Failed to load outline RAG content")
                
    #         if self.state.chapter_content:
    #             logger.info(f"Successfully loaded full content RAG content ({len(self.state.chapter_content)} chars)")
    #         else:
    #             logger.warning("Failed to load full content RAG content")
                
    #         return rag_provider


    # Create the task with custom execution logic and use the configuration from tasks.yaml
    # logging.info("define task")
    # logger.warning("🚀 IN wriue chap: agents dict keys = %s", list(self.tasks_config.keys()))
    #logger.warning("🚀 IN erotw chap: section_writer agent = %s", self.agents.get("writer", "MISSING"))

    # task = Task(
    #     config=self.tasks_config["write_chapter"],
    #     agent=self.agents["writer"],
    #     output_pydantic=Chapter
    # )
    # logging.info("wxwcutw task")
    # Bind the custom execute method to this task instance
    #task.execute = execute.__get__(task, Task)

    # Actually run it — and return the output
    # chapter_result = await task.execute()

    # return chapter_result

   
