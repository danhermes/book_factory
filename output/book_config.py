"""
Book-specific configuration for the book writing flow.
"""

# Default book title and topic for CLI
BOOK_TITLE = "AI-Enhanced"
BOOK_TOPIC = "Personal and Professional growth through AI"

# RAG content files configuration
RAG_CONTENT_FILES = {
    "book_outline": "output/rag/book_outline.json",
    "chapter_content": "output/rag/chapter_content.txt",
    "tool_index": "output/rag/tool_index.json",
}

LLM_TEMPERATURE = 0.9
