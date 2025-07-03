import time
import logging
import os
import yaml
from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import SerperDevTool
from pydantic import BaseModel
from old.reader_tool import ReaderTool
#from book_writing_flow.tools.outline_parser import OutlineParser
from book_writing_flow.tools.rag_utils import RagContentProvider
from book_writing_flow.config.book_config import RAG_CONTENT_FILES
from book_writing_flow.book_model import BookModel

# Configure logging
logger = logging.getLogger("outline_crew")

class Outline(BookModel):
    pass

@CrewBase
class OutlineCrew:

    def __init__(self):
        self.agents_config = None
        self.tasks_config = None
        self.llm = LLM(model="gpt-4o")

        # # Use absolute paths for configuration files
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
        agents_config_path = os.path.join(project_root, "src/book_writing_flow/crews/Outline_crew/config/agents.yaml")
        tasks_config_path = os.path.join(project_root, "src/book_writing_flow/crews/Outline_crew/config/tasks.yaml")

        # Load agents config
        try:
            with open(agents_config_path, 'r') as f:
                self.agents_config = yaml.safe_load(f)
            logger.info(f"Successfully loaded agents config from {agents_config_path}")
        except Exception as e:
            logger.warning(f"Error loading agents config: {e}")

        # Load tasks config
        try:
            with open(tasks_config_path, 'r') as f:
                self.tasks_config = yaml.safe_load(f)
            logger.info(f"Successfully loaded tasks config from {tasks_config_path}")
            logger.info(f"tasks_config: {self.tasks_config['research_task']['expected_output']}")
        except Exception as e:
            logger.warning(f"Error loading tasks config: {e}")
        logger.info("OutlineCrew __init__ method complete.")
    
    @agent
    def research_agent(self) -> Agent:
        logger.info(f"research_agent method")
        return Agent(
            config=self.agents_config["research_agent"],
            llm=self.llm
        )

    @task
    def research_task(self) -> Task:
        logger.info(f"research_task method")
        return Task(
             config=self.tasks_config['research_task'],
             output_pydantic=Outline
        )
    
    @agent
    def outline_writer(self) -> Agent:
        logger.info(f"outline_writer method")
        return Agent(
            config=self.agents_config["outline_writer"],
            llm=self.llm
        )

    @task
    def write_outline(self) -> Task:
        logger.info(f"write_outline method")
        return Task(
            config=self.tasks_config['write_outline'],
            output_pydantic=Outline
        )

    @crew
    def crew(self) -> Crew:
        logger.info(f"crew method")
        logger.info(f"Agents: {len(self.agents)} agents")
        logger.info(f"Tasks: {len(self.tasks)} tasks")
        crew = Crew(agents=self.agents,
                   tasks=self.tasks,
                   process=Process.sequential,
                   verbose=True
        )
        logger.info(f"Crew has {len(crew.agents)} agents and {len(crew.tasks)} tasks")
        return crew
