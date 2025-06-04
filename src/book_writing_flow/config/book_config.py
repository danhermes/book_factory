"""
Book-specific configuration for the book writing flow.
"""

# RAG content files configuration
RAG_CONTENT_FILES = {
    "book_outline": "rag/ChatGPT_in_the_Office.md",
    "chapter_content": "rag/chatgpt_office_use_cases_detailed_outline.txt",
    # Add more content files as needed
}

# Book metadata
BOOK_METADATA = {
    "title": "ChatGPT for the Office",
    "author": "Dan Hermes",
    "description": "A comprehensive guide to using ChatGPT in business contexts",
}

# Chapter generation settings
CHAPTER_SETTINGS = {
    "target_word_count": 4000,
    "include_research": True,
    "include_case_studies": True,
}