"""Configuration and constants."""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Paths
BASE_DIR = Path(__file__).parent.parent.parent.parent  # book_factory root
OUTPUT_DIR = BASE_DIR / "output"
CHAPTERS_DIR = OUTPUT_DIR / "chapters"
STATIC_DIR = Path(__file__).parent.parent / "static"

# Agent settings
AGENT_MODEL = os.getenv("AGENT_MODEL", "gpt-4o")
AGENT_TEMPERATURE = float(os.getenv("AGENT_TEMPERATURE", "0.7"))

# Keywords for detection
CHAPTER_KEYWORDS = [
    'all chapters', 'every chapter', 'the book', 'this book', 'entire book',
    'throughout the book', 'across all', 'each chapter',
    'chapters', 'the chapter', 'the chap', 'this chap', 'that chap',
    'in book', 'in the book', 'in this book', 'whole book', 'full book',
    'the file', 'this file', 'that file', 'the doc', 'this doc', 'the document',
    'current file', 'open file', 'loaded file', 'in file', 'into file'
]

EDIT_KEYWORDS = [
    'edit ', 'rewrite', 'revise', 'improve', 'fix ', 'change ',
    'update ', 'modify', 'remove ', 'add ', 'insert', 'delete',
    'replace', 'shorten', 'expand', 'rephrase', 'restructure',
    'correct', 'enhance', 'polish', 'refine', 'strengthen',
    'write ', 'write this', 'write that', 'put ', 'put this', 'put that',
    'resolve', 'include', 'incorporate', 'weave', 'integrate',
    'append', 'prepend', 'inject', 'drop in', 'slip in',
    # Action-oriented phrases
    'make it', 'need more', 'want more', 'add more', 'more detail',
    'just do', 'do it', 'stop talking', 'actually do',
    # Single word triggers when combined with file/chapter reference
    'tweak', 'adjust', 'flesh out', 'beef up', 'punch up'
]

FULL_BOOK_KEYWORDS = [
    'the book', 'this book', 'entire book', 'whole book', 'full book',
    'all chapters', 'every chapter', 'in book', 'in this book', 'in the book'
]

CHAPTER_PATTERNS = [
    r'chapter\s*\d+',
    r'\bch\s*\d+',
    r'\bchap\s*\d+',
]

CHAPTER_NUMBER_PATTERNS = [
    r'chapter\s*(\d+)',
    r'\bch\s*(\d+)',
    r'\bchap\s*(\d+)',
]
