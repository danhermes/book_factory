# Book Agent Editor

A three-panel web app for editing book chapters with AI assistance.

## Quickstart

```bash
python3 src/book_agent/run.py
```

Open http://localhost:8000

## Features

- **Left Panel**: File browser for `output/` folder
- **Middle Panel**: Markdown editor with preview mode
- **Right Panel**: AI agent for writing assistance

## Book Editing

To edit chapters, include "chapter" in your prompt:

- `"Review chapter 1 for grammar issues"`
- `"Improve all chapters for clarity"`
- `"Rewrite chapter 3 introduction"`

Progress displays in real-time with cancel option.

## Configuration

Edit `.env` in project root:

```
BOOK_AGENT_PORT=8000
AGENT_MODEL=gpt-4o
AGENT_TEMPERATURE=0.7
```

## Requirements

- Python 3.11+
- OpenAI API key in `.env`
