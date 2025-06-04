import time
import logging
import os
import yaml
from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import SerperDevTool
from pydantic import BaseModel
from book_writing_flow.tools.custom_tool import BrightDataWebSearchTool
from book_writing_flow.tools.reader_tool import ReaderTool
from book_writing_flow.tools.outline_parser import OutlineParser
from book_writing_flow.tools.rag_utils import RagContentProvider
from book_writing_flow.config.book_config import RAG_CONTENT_FILES

# Configure logging
logger = logging.getLogger("outline_crew")

llm = LLM(model="gpt-4o")

class Section(BaseModel):
    """Section of a chapter"""
    title: str
    content: str = ""

class Chapter(BaseModel):
    """Chapter of the book"""
    title: str
    content: str = ""
    sections: list[Section] = []

class Outline(BaseModel):
    """Outline of the book"""
    total_chapters: int
    chapters: list[Chapter]

@CrewBase
class OutlineCrew:

    def __init__(self):
        self.agents_config = None
        self.tasks_config = None
        self.task_expected_output = None
        self.outline_path = None

        # # Use absolute paths for configuration files
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
        agents_config_path = os.path.join(project_root, "src/book_writing_flow/crews/Outline_crew/config/agents.yaml")
        tasks_config_path = os.path.join(project_root, "output/tasks/tasks.outline.yaml")
        task_expected_output_path = os.path.join(project_root, "output/tasks/tasks.outline.expected_output.yaml")
        outline_path = RAG_CONTENT_FILES["book_outline"]
        logging.info(f"RAG_CONTENT_FILES: {RAG_CONTENT_FILES['book_outline']}")
    
        # Load agents configuration
        try:
            with open(agents_config_path, 'r') as f:
                self.agents_config = yaml.safe_load(f)
            logger.info(f"Successfully loaded agents config from {agents_config_path}")
        except Exception as e:
            logger.warning(f"Error loading agents config: {e}")
            # Provide default configurations
            agents_config = {
                "research_agent": {
                    "name": "Research Agent",
                    "description": "Researches topics and gathers information.",
                    "goal": "Gather comprehensive information about the topic."
                },
                "outline_writer": {
                    "name": "Outline Writer",
                    "description": "Creates detailed book outlines.",
                    "goal": "Create a well-structured book outline with chapters and sections."
                }
            }
            logger.info("Using default agent configurations")
    
        # # Initialize RAG provider
        rag_provider = RagContentProvider(RAG_CONTENT_FILES)
        
        # Store inputs for access by tasks
        self._inputs = {}
        
        # Load task configurations
        try:
            with open(tasks_config_path, 'r') as f:
                self.tasks_config = yaml.safe_load(f)
            logger.info(f"Successfully loaded tasks config from {tasks_config_path}")
            logger.info(f"tasks_config: {self.tasks_config['research_task']['expected_output']}")
        except Exception as e:
            logger.warning(f"Error loading tasks config: {e}")
            # Provide default configurations
            tasks_config = {
                "research_task": {
                    "description": "Research the topic and gather information.",
                    "expected_output": "A list of insights and key points about the topic.",
                    "agent": "research_agent"
                },
                "write_outline": {
                    "description": "Create a detailed outline for a book.",
                    "agent": "outline_writer"
                }
            }
            logger.info("Using default task configurations")
        
        # Load expected output
        try:
            with open(task_expected_output_path, 'r') as f:
                self.task_expected_output = yaml.safe_load(f)
            logger.info(f"Successfully loaded expected output from {task_expected_output_path}")
            logger.info(f"task_expected_output: {self.task_expected_output['expected_output']}")
        except Exception as e:
            logger.warning(f"Error loading expected output: {e}")
            task_expected_output = {"expected_output": "A detailed book outline with chapters and sections."}
    
    def get_inputs(self):
        """Get the inputs passed to the crew during kickoff"""
        return self._inputs
    
    @agent
    def research_agent(self) -> Agent:
        # # Create a proper agent configuration dictionary
        # agent_config = {
        #     "name": self.agents_config["research_agent"]["name"],
        #     "description": self.agents_config["research_agent"]["description"],
        #     "goal": self.agents_config["research_agent"]["goal"]
        # }
        
        return Agent(
            config=self.agents_config["research_agent"],
            tools=[BrightDataWebSearchTool(), ReaderTool()],
            llm=llm,
            context=[
                {
                    "key": "rag_files",
                    "value": {
                        "outline": "rag/ChatGPT_for_Business_Expanded_Outline.txt",
                        "full_content": "rag/ChatGPT_for_Business_FULL_WITH_COVER.txt"
                    },
                    "description": "Paths to RAG content files"
                }
            ]
        )

    @task
    def research_task(self) -> Task:
        # Add debug logging
        logger.info(f"In research_task method, tasks_config type: {type(self.tasks_config)}")
        logger.info(f"In research_task method, tasks_config keys: {list(self.tasks_config.keys()) if hasattr(self.tasks_config, 'keys') else 'No keys method'}")
        
        # Create a task with proper context format
        try:
            x = 0
            #if 'research_task' in self.tasks_config:
                #logger.info(f"Found research_task in tasks_config: {self.tasks_config['research_task']['expected_output']}")
            task_config = dict(self.tasks_config['research_task'])
            #else:
            #    raise KeyError("research_task")
        except KeyError as e:
            logger.error(f"KeyError: {e} - research_task not found in tasks_config")
            # Use a default configuration
            logger.info("Using default research_task configuration")
            task_config = {
                "description": "Research the topic and gather information about ChatGPT for Business.",
                "expected_output": "A list of insights and key points about ChatGPT for Business.",
                "agent": "research_agent"
            }
            
        return Task(
            config=task_config,
            context=[
                {
                    "key": "outline_path",
                    "value": self.outline_path,
                    "description": "Path to the outline file",
                    "expected_output": "A file path string"
                }
            ]
        )
    
    @agent
    def outline_writer(self) -> Agent:
        # # Create a proper agent configuration dictionary
        # agent_config = {
        #     "name": self.agents_config["outline_writer"]["name"],
        #     "description": self.agents_config["outline_writer"]["description"],
        #     "goal": self.agents_config["outline_writer"]["goal"]
        # }
        
        return Agent(
            config=self.agents_config["outline_writer"],
            tools=[ReaderTool()],
            llm=llm,
            context=[
                {
                    "key": "rag_files",
                    "value": {
                        "outline": "rag/ChatGPT_for_Business_Expanded_Outline.txt",
                        "full_content": "rag/ChatGPT_for_Business_FULL_WITH_COVER.txt"
                    },
                    "description": "Paths to RAG content files"
                },
                {
                    "key": "rag_access_instructions",
                    "value": "To access the RAG files, use the Reader Tool with either the file paths or these aliases: 'expanded_outline_chatgpt_for_business.txt' or 'outline' for the outline file, and 'full_content_chatgpt_for_business.txt' or 'full_content' for the full content file.",
                    "description": "Instructions for accessing RAG content"
                },
                {
                    "key": "chapter1_stories",
                    "value": ["WelcomeWell", "StackHaven", "FlexTax", "LeadFleet", "BriteTeam"],
                    "description": "Case studies for Chapter 1: Customer Experience"
                }
            ]
        )

    @task
    def write_outline(self) -> Task:
        """
        Override the write_outline task to use RAG-enhanced content.
        This keeps the standard crew workflow but enhances it with RAG.
        """
        logger.info("===== STARTING WRITE_OUTLINE TASK CREATION =====")
        start_time = time.time()
        
        # In the newer version of CrewAI, we can't modify the execute method
        # Instead, we'll use the task's config and context to provide the necessary information
        
        # Create a modified config with enhanced description if needed
        task_config = dict(self.tasks_config["write_outline"])
        logger.info(f"Original task config keys: {list(task_config.keys())}")
        if "description" in task_config:
            logger.info(f"Original description length: {len(task_config['description'])} characters")
        
        # Check if we're generating a single chapter outline
        single_chapter = False
        chapter_number = None
        
        # Try to enhance the task description with RAG content
        try:
            # Get the outline content
            logger.info("Getting outline content from RAG provider")
            content_start = time.time()
            outline_content = self.rag_provider.get_file_content("outline")
            logger.info(f"Got outline content in {time.time() - content_start:.2f} seconds")
            
            if outline_content:
                logger.info(f"Outline content length: {len(outline_content)} characters")
                # Parse the outline content into a structured outline
                logger.info("Parsing outline content")
                parse_start = time.time()
                parsed_outline = OutlineParser.parse_content(outline_content)
                logger.info(f"Parsed outline in {time.time() - parse_start:.2f} seconds")
                logger.info(f"Parsed outline has {len(parsed_outline['chapters'])} chapters")
                for i, chapter in enumerate(parsed_outline['chapters']):
                    logger.info(f"Chapter {i+1}: {chapter['title']} with {len(chapter['sections'])} sections")
                
                # Enhance the task description with RAG content
                if "description" in task_config:
                    logger.info("Enhancing task description with RAG content")
                    enhance_start = time.time()
                    original_description = task_config["description"]
                    
                    # Create a query based on the task description
                    query = f"Book outline for ChatGPT for Business with chapters and sections"
                    
                    # Enhance the description with relevant content
                    enhanced_description = self.rag_provider.enhance_prompt(
                        original_description,
                        query,
                        content_types=["outline", "full_content"],
                        max_chunks=5
                    )
                    
                    # Update the task description
                    task_config["description"] = enhanced_description
                    logger.info(f"Enhanced description in {time.time() - enhance_start:.2f} seconds")
                
                # Add the parsed outline as additional context
                task_config["additional_info"] = f"Parsed outline with {len(parsed_outline['chapters'])} chapters"
        except Exception as e:
            logger.error(f"Error enhancing task with RAG content: {e}")
        
       
        # Check if we're generating a single chapter outline
        # This will be passed from the kickoff inputs
        inputs = self.get_inputs()
        if inputs and 'single_chapter' in inputs and inputs['single_chapter']:
            logger.info("Generating outline for a single chapter")
            if 'chapter_number' in inputs:
                chapter_number = inputs['chapter_number']
                logger.info(f"Generating outline for chapter {chapter_number}")
                
                # Modify the task description to focus on a single chapter
                if "description" in task_config:
                    logger.info(f"Original description: {task_config['description']}")
                    task_config["description"] = task_config["description"].replace(
                        "Create a logical flow between chapters",
                        f"Create a detailed outline for Chapter {chapter_number}"
                    )
                    logger.info(f"Modified description: {task_config['description']}")
                    task_config["description"] = task_config["description"].replace(
                        "ensure each chapter tells a cohesive story",
                        "ensure this chapter tells a cohesive story"
                    )
                    logger.info(f"Modified description 2: {task_config['description']}")
                # Create the context list with standard items
                #context_items = [
                    # {
                    #     "key": "outline_path",
                    #     "value": self.outline_path,
                    #     "description": "Path to the outline file",
                    #     "expected_output": "A file path string"
                    # },
                    # {
                    #     "key": "use_rag",
                    #     "value": True,
                    #     "description": "Whether to use RAG for enhanced content",
                    #     "expected_output": "A boolean value"
                    # },
                    # {
                    #     "key": "rag_files",
                    #     "value": {
                    #         "outline": "rag/ChatGPT_for_Business_Expanded_Outline.txt",
                    #         "full_content": "rag/ChatGPT_for_Business_FULL_WITH_COVER.txt"
                    #     },
                    #     "description": "Paths to RAG content files that should be used to enhance the outline",
                    #     "expected_output": "A dictionary mapping content types to file paths"
                    # }
                #]
         
                # # Add chapter number to context
                # context_items.append({
                #     "key": "single_chapter",
                #     "value": True,
                #     "description": "Whether to generate a single chapter outline",
                #     "expected_output": "A boolean value"
                # })
                # context_items.append({
                #     "key": "chapter_number",
                #     "value": chapter_number,
                #     "description": "The chapter number to generate",
                #     "expected_output": "An integer"
                # })
        
        # Create the task with the enhanced config
        logger.info(f"Total write_outline task creation took {time.time() - start_time:.2f} seconds")
        logger.info("===== WRITE_OUTLINE TASK CREATION COMPLETE =====")
        
        # Initialize context_items if it wasn't defined in the single chapter case
        #if not locals().get('context_items'):
        context_items = [
            {
                "key": "book_title",
                "value": "ChatGPT for Business",
                "description": "The title of the book",
                "expected_output": "A string"
            },
            {
                "key": "expected_output",
                "value": self.task_expected_output["expected_output"],
                "description": "Prompt from file tasks.outline.expected_output.yaml",
                "expected_output": "A string"
            }
        ]
            
        return Task(
            config=task_config,
            output_pydantic=Outline,
            context=context_items
        )

    @crew
    def crew(self) -> Crew:
        """Creates the Outline Crew"""
        logger.info("===== CREATING OUTLINE CREW =====")
        start_time = time.time()
        
        # Log the agents and tasks being used
        logger.info(f"Agents: {len(self.agents)} agents")
        logger.info(f"Tasks: {len(self.tasks)} tasks")
        
        # Store the current instance for access in the callback
        instance = self
        
        # Create a callback to store inputs
        def on_kickoff(crew_instance, inputs=None):
            # Store the inputs for access by tasks
            if inputs:
                logger.info(f"Storing inputs: {inputs}")
                instance._inputs = inputs
        
        crew = Crew(agents=self.agents,
                   tasks=self.tasks,
                   process=Process.sequential,
                   verbose=True,
                   callbacks={"on_kickoff": on_kickoff}) #delete on_kickoff - not used
        
        logger.info(f"Crew created in {time.time() - start_time:.2f} seconds")
        logger.info(f"Crew has {len(crew.agents)} agents and {len(crew.tasks)} tasks")
        return crew
