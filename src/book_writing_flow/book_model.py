from pydantic import BaseModel
from typing import Optional, List

# class SectionInput(BaseModel):
#     title: str
#     type: str
#     chapter_title: str
#     chapter_number: int
#     min_length: int
#     structure: List[str]
#     rag_content: str
#     previous_section: Optional[str] = None
#     next_section: Optional[str] = None

class Section(BaseModel):
    chapter_title: Optional[str] = None
    section_title: str = ""
    type: str = ""
    description: str = ""
    story: str = ""
    tools: List[str] = []
    content: str = ""
    previous_section: Optional[str] = None
    next_section: Optional[str] = None
    chapter_number: Optional[int] = None
    section_number: Optional[int] = None
    structure: Optional[str] = None
    rag_content: Optional[str] = None
    min_length: Optional[int] = None

class Chapter(BaseModel):
    title: str = ""
    chapter_title: str = ""
    number: int = 0
    chapter_number: int = 0
    description: str = ""
    content: str = ""
    sections: List[Section] = []

class BookModel(BaseModel):
    topic: Optional[str] = "ChatGPT prompts for use by the businessperson"
    book_title: Optional[str] = "ChatGPT for the Office"
    total_chapters: Optional[int] = None
    titles: Optional[List[str]] = None
    chapters: List[Chapter] = []
