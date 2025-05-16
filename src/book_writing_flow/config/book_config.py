"""
Book-specific configuration for the book writing flow.
"""

# RAG content files configuration
RAG_CONTENT_FILES = {
    "outline": "rag/ChatGPT_for_Business_Expanded_Outline.txt",
    "full_content": "rag/ChatGPT_for_Business_FULL_WITH_COVER.txt",
    # Add more content files as needed
}

# Book metadata
BOOK_METADATA = {
    "title": "ChatGPT for Business",
    "author": "Author Name",
    "description": "A comprehensive guide to using ChatGPT in business contexts",
}

# Chapter generation settings
CHAPTER_SETTINGS = {
    "target_word_count": 4000,
    "include_research": True,
    "include_case_studies": True,
}