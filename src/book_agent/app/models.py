"""Pydantic models."""

from typing import Optional, List
from pydantic import BaseModel


class FileContent(BaseModel):
    path: str
    content: str


class MessageHistory(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class AgentRequest(BaseModel):
    prompt: str
    file_content: Optional[str] = None
    file_path: Optional[str] = None
    history: Optional[List[MessageHistory]] = None


class AgentResponse(BaseModel):
    response: str
    task_id: Optional[str] = None


class BookEditRequest(BaseModel):
    prompt: str
    chapter_indices: Optional[List[int]] = None


class TaskStatus(BaseModel):
    task_id: str
    status: str
    progress: int
    total: int
    current_chapter: Optional[str] = None
    messages: List[str] = []
    completed: bool = False
    error: Optional[str] = None
