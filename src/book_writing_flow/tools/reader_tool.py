from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type
import os

class ReaderToolInput(BaseModel):
    """Input schema for ReaderTool."""
    file_path: str = Field(..., description="Path to the file to read.")

class ReaderTool(BaseTool):
    name: str = "Reader Tool"
    description: str = "Use this tool to read and extract content from a file."
    args_schema: Type[BaseModel] = ReaderToolInput

    def _run(self, file_path: str) -> str:
        """Read the content of a file."""
        # Check for RAG files with special handling
        if file_path == "expanded_outline_chatgpt_for_business.txt" or file_path == "outline":
            actual_path = "rag/ChatGPT_for_Business_Expanded_Outline.txt"
        elif file_path == "full_content_chatgpt_for_business.txt" or file_path == "full_content":
            actual_path = "rag/ChatGPT_for_Business_FULL_WITH_COVER.txt"
        else:
            actual_path = file_path
            
        # Check if the file exists
        if not os.path.exists(actual_path):
            return f"Error: File not found at {file_path} (tried {actual_path})"
        
        # Read and return the file content
        try:
            with open(actual_path, 'r') as f:
                content = f.read()
            return content
        except Exception as e:
            return f"Error reading file {actual_path}: {e}"