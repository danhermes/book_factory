"""API routes."""

import os
import uuid
import json
import asyncio
from datetime import datetime
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, StreamingResponse

from .config import OUTPUT_DIR, STATIC_DIR, FULL_BOOK_KEYWORDS
from .models import (
    FileContent, AgentRequest, AgentResponse, TaskStatus
)
from .services import (
    get_chapter_files, detect_book_edit_intent, detect_chapter_reference,
    extract_chapter_indices, run_book_edit_task, chat_completion,
    active_tasks
)
from . import background_tasks_set

router = APIRouter()


@router.get("/")
async def root():
    """Serve the main HTML page."""
    return FileResponse(STATIC_DIR / "index.html")


@router.get("/api/files")
async def list_files():
    """List all files in the output directory."""
    files = []

    if not OUTPUT_DIR.exists():
        return {"files": []}

    for path in sorted(OUTPUT_DIR.rglob("*")):
        if path.is_file() and path.suffix in [".md", ".txt", ".json"]:
            relative_path = path.relative_to(OUTPUT_DIR)
            if str(relative_path).startswith("outlines"):
                continue
            files.append({
                "path": str(relative_path),
                "name": path.name,
                "full_path": str(path),
                "is_chapter": "chapters" in str(relative_path)
            })

    return {"files": files}


@router.get("/api/chapters")
async def list_chapters():
    """List all chapter files."""
    chapters = get_chapter_files()
    return {
        "chapters": [
            {"index": i, "name": ch.name, "path": str(ch.relative_to(OUTPUT_DIR))}
            for i, ch in enumerate(chapters)
        ]
    }


@router.get("/api/file/{file_path:path}")
async def read_file(file_path: str):
    """Read the content of a specific file."""
    full_path = OUTPUT_DIR / file_path

    if not full_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    if not full_path.is_file():
        raise HTTPException(status_code=400, detail="Path is not a file")

    try:
        content = full_path.read_text(encoding="utf-8")
        return {"path": file_path, "content": content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/file/{file_path:path}")
async def save_file(file_path: str, file_content: FileContent):
    """Save content to a specific file."""
    full_path = OUTPUT_DIR / file_path

    if not full_path.parent.exists():
        full_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        # Write and force flush to disk
        print(f"[SAVE] Writing to: {full_path}")
        print(f"[SAVE] Content length: {len(file_content.content)} chars")
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(file_content.content)
            f.flush()
            os.fsync(f.fileno())

        # Verify write
        verify_stat = os.stat(full_path)
        print(f"[SAVE] Verified: {verify_stat.st_size} bytes on disk")
        return {"success": True, "path": file_path, "bytes": len(file_content.content)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/agent", response_model=AgentResponse)
async def agent_chat(request: AgentRequest):
    """Send a prompt to the AI agent."""
    try:
        # Check for book edit request
        if detect_book_edit_intent(request.prompt):
            chapters = get_chapter_files()
            if chapters:
                # Check if user is referring to currently open file
                prompt_lower = request.prompt.lower()
                use_current_file = any(kw in prompt_lower for kw in [
                    'the file', 'this file', 'that file', 'current file',
                    'open file', 'loaded file', 'the doc', 'this doc'
                ])

                if use_current_file and request.file_path:
                    # Find the index of the currently open file
                    chapter_indices = []
                    for i, ch in enumerate(chapters):
                        if ch.name in request.file_path or request.file_path in str(ch):
                            chapter_indices = [i]
                            break

                    if not chapter_indices:
                        # File not found in chapters, try direct path
                        return AgentResponse(
                            response=f"Could not find '{request.file_path}' in chapters. Try specifying 'chapter X'."
                        )
                else:
                    chapter_indices = extract_chapter_indices(request.prompt, len(chapters))

                task_id = str(uuid.uuid4())

                active_tasks[task_id] = {
                    'status': 'running',
                    'progress': 0,
                    'total': len(chapter_indices),
                    'current_chapter': None,
                    'messages': [],
                    'completed': False,
                    'error': None,
                    'started': datetime.now().isoformat()
                }

                task = asyncio.create_task(
                    run_book_edit_task(task_id, request.prompt, chapter_indices)
                )
                background_tasks_set.add(task)
                task.add_done_callback(background_tasks_set.discard)

                chapters_to_edit = [chapters[i].name for i in chapter_indices if i < len(chapters)]
                return AgentResponse(
                    response=f"Starting book edit for {len(chapter_indices)} chapter(s): {', '.join(chapters_to_edit[:3])}{'...' if len(chapters_to_edit) > 3 else ''}. Task ID: `{task_id}`",
                    task_id=task_id
                )

        # Check for chapter query
        if detect_chapter_reference(request.prompt):
            chapters = get_chapter_files()
            if chapters:
                chapter_indices = extract_chapter_indices(request.prompt, len(chapters))
                prompt_lower = request.prompt.lower()

                full_book_query = any(kw in prompt_lower for kw in FULL_BOOK_KEYWORDS)
                chapters_to_load = chapter_indices if full_book_query else chapter_indices[:3]

                chapter_context = ""
                for i in chapters_to_load:
                    if i < len(chapters):
                        content = chapters[i].read_text(encoding='utf-8')
                        word_count = len(content.split())
                        max_len = 8000 if full_book_query else 15000
                        if len(content) > max_len:
                            content = content[:max_len] + "\n\n[... truncated ...]"
                        chapter_context += f"\n\n## {chapters[i].name} ({word_count:,} words)\n{content}"

                system_message = f"""You are a helpful writing assistant for a book editing application.
Answer questions accurately based on the chapter content provided.
Loaded {len(chapters_to_load)} chapter(s) for context.

To EDIT chapters, include action words like: edit, rewrite, revise, improve, fix, change."""

                messages = [{"role": "system", "content": system_message}]

                if request.history:
                    for h in request.history[-10:]:
                        messages.append({"role": h.role, "content": h.content})

                user_message = f"""Chapter content:
---{chapter_context}
---

Question: {request.prompt}"""
                messages.append({"role": "user", "content": user_message})

                return AgentResponse(response=chat_completion(messages))

        # Regular chat
        system_message = """You are a helpful writing assistant for a book editing application.
To edit chapters, include "chapter" AND an action word (edit, rewrite, improve, etc.)."""

        messages = [{"role": "system", "content": system_message}]

        if request.history:
            for h in request.history[-10:]:
                messages.append({"role": h.role, "content": h.content})

        user_message = request.prompt
        if request.file_content:
            user_message = f"""Current file: {request.file_path or 'Unknown'}

File content:
---
{request.file_content[:8000]}
---

Request: {request.prompt}"""

        messages.append({"role": "user", "content": user_message})

        return AgentResponse(response=chat_completion(messages))

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")


@router.get("/api/task/{task_id}")
async def get_task_status(task_id: str):
    """Get the status of a running task."""
    task = active_tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return TaskStatus(
        task_id=task_id,
        status=task.get('status', 'unknown'),
        progress=task.get('progress', 0),
        total=task.get('total', 0),
        current_chapter=task.get('current_chapter'),
        messages=task.get('messages', []),
        completed=task.get('completed', False),
        error=task.get('error')
    )


@router.get("/api/task/{task_id}/stream")
async def stream_task_status(task_id: str):
    """Stream task status updates using SSE."""
    task = active_tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    async def event_generator():
        last_message_count = 0
        while True:
            task = active_tasks.get(task_id)
            if not task:
                break

            current_count = len(task.get('messages', []))
            if current_count > last_message_count:
                for msg in task['messages'][last_message_count:]:
                    data = json.dumps({
                        'type': 'message',
                        'message': msg,
                        'progress': task.get('progress', 0),
                        'total': task.get('total', 0),
                        'completed': task.get('completed', False)
                    })
                    yield f"data: {data}\n\n"
                last_message_count = current_count

            if task.get('completed') or task.get('error'):
                data = json.dumps({
                    'type': 'complete',
                    'completed': True,
                    'error': task.get('error')
                })
                yield f"data: {data}\n\n"
                break

            await asyncio.sleep(0.5)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
    )


@router.post("/api/task/{task_id}/cancel")
async def cancel_task(task_id: str):
    """Cancel a running task."""
    task = active_tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    task['cancelled'] = True
    task['messages'].append("Cancellation requested...")
    return {"success": True}


@router.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "output_dir": str(OUTPUT_DIR),
        "chapters_count": len(get_chapter_files()),
        "active_tasks": len(active_tasks)
    }
