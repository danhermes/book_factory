"""Business logic and services."""

import re
import json
import asyncio
from pathlib import Path
from typing import List, Dict
from openai import OpenAI

from .config import (
    CHAPTERS_DIR, CHAPTER_KEYWORDS, EDIT_KEYWORDS,
    CHAPTER_PATTERNS, CHAPTER_NUMBER_PATTERNS,
    AGENT_MODEL, AGENT_TEMPERATURE
)

# OpenAI client
client = OpenAI()

# Task tracking
active_tasks: Dict[str, dict] = {}

# OpenAI Function definitions for chapter editing
EDIT_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "insert_content",
            "description": "Insert new content into the chapter at a specific location. Use this to add new paragraphs, scenes, or story arc resolutions.",
            "parameters": {
                "type": "object",
                "properties": {
                    "anchor_text": {
                        "type": "string",
                        "description": "An exact quote (20-100 chars) from the chapter to use as the insertion point"
                    },
                    "position": {
                        "type": "string",
                        "enum": ["after", "before"],
                        "description": "Insert the new content before or after the anchor text's paragraph"
                    },
                    "content": {
                        "type": "string",
                        "description": "The new content to insert. Can be multiple paragraphs."
                    }
                },
                "required": ["anchor_text", "position", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "edit_content",
            "description": "Find and replace existing content in the chapter. Use this to modify, improve, or fix existing text.",
            "parameters": {
                "type": "object",
                "properties": {
                    "find_text": {
                        "type": "string",
                        "description": "The exact text to find and replace (must match exactly)"
                    },
                    "replace_text": {
                        "type": "string",
                        "description": "The replacement text"
                    }
                },
                "required": ["find_text", "replace_text"]
            }
        }
    }
]


def get_chapter_files() -> List[Path]:
    """Get all chapter files sorted by chapter number."""
    if not CHAPTERS_DIR.exists():
        return []

    chapters = list(CHAPTERS_DIR.glob("*.md"))

    def extract_number(path: Path) -> int:
        match = re.search(r'^(\d+)', path.name)
        return int(match.group(1)) if match else 999

    return sorted(chapters, key=extract_number)


def detect_chapter_reference(prompt: str) -> bool:
    """Detect if the prompt references chapters."""
    prompt_lower = prompt.lower()

    if any(kw in prompt_lower for kw in CHAPTER_KEYWORDS):
        return True

    for pattern in CHAPTER_PATTERNS:
        if re.search(pattern, prompt_lower):
            return True

    return False


def detect_edit_intent(prompt: str) -> bool:
    """Detect if the prompt is requesting an edit (vs a query)."""
    prompt_lower = prompt.lower()
    return any(kw in prompt_lower for kw in EDIT_KEYWORDS)


def detect_book_edit_intent(prompt: str) -> bool:
    """Detect if the prompt is requesting a book/chapter edit."""
    return detect_chapter_reference(prompt) and detect_edit_intent(prompt)


def extract_chapter_indices(prompt: str, total_chapters: int) -> List[int]:
    """Extract chapter indices from prompt."""
    prompt_lower = prompt.lower()

    if 'all chapter' in prompt_lower or 'every chapter' in prompt_lower or 'the book' in prompt_lower:
        return list(range(total_chapters))

    indices = set()
    for pattern in CHAPTER_NUMBER_PATTERNS:
        matches = re.findall(pattern, prompt_lower)
        for match in matches:
            chapter_num = int(match)
            if 1 <= chapter_num <= total_chapters:
                indices.add(chapter_num - 1)

    if not indices:
        return list(range(total_chapters))

    return sorted(list(indices))


def parse_edit_instructions(response_text: str) -> List[Dict]:
    """Parse edit/insert instructions from model response."""
    instructions = []

    # Pattern for INSERT blocks
    insert_pattern = re.compile(
        r'<<<INSERT>>>\s*'
        r'(AFTER|BEFORE):\s*"""(.*?)"""\s*'
        r'CONTENT:\s*"""(.*?)"""\s*'
        r'<<<END>>>',
        re.DOTALL
    )

    # Pattern for EDIT blocks
    edit_pattern = re.compile(
        r'<<<EDIT>>>\s*'
        r'FIND:\s*"""(.*?)"""\s*'
        r'REPLACE:\s*"""(.*?)"""\s*'
        r'<<<END>>>',
        re.DOTALL
    )

    for match in insert_pattern.finditer(response_text):
        instructions.append({
            'type': 'insert',
            'position': match.group(1).lower(),
            'anchor': match.group(2).strip(),
            'content': match.group(3).strip()
        })

    for match in edit_pattern.finditer(response_text):
        instructions.append({
            'type': 'edit',
            'find': match.group(1).strip(),
            'replace': match.group(2).strip()
        })

    return instructions


def apply_edit_instructions(original_content: str, instructions: List[Dict], task=None) -> tuple:
    """Apply edit instructions to content. Returns (modified_content, applied_count, errors)."""
    content = original_content
    applied = 0
    errors = []

    # Logging helper
    def log(msg):
        print(f"[APPLY] {msg}")
        if task:
            task['messages'].append(f"[DEBUG] {msg}")

    log(f"Starting with {len(original_content)} chars, {len(instructions)} instructions")

    for i, inst in enumerate(instructions):
        log(f"Processing instruction {i+1}: type={inst['type']}")

        if inst['type'] == 'edit':
            find_text = inst['find']
            replace_text = inst['replace']
            log(f"EDIT: looking for '{find_text[:50]}...'")

            if find_text in content:
                old_len = len(content)
                content = content.replace(find_text, replace_text, 1)
                log(f"EDIT SUCCESS: {old_len} -> {len(content)} chars")
                applied += 1
            else:
                # Try case-insensitive search
                content_lower = content.lower()
                find_lower = find_text.lower()
                pos = content_lower.find(find_lower)

                if pos != -1:
                    # Found case-insensitive match - replace at that position
                    old_len = len(content)
                    content = content[:pos] + replace_text + content[pos + len(find_text):]
                    log(f"EDIT (case-insensitive) SUCCESS: {old_len} -> {len(content)} chars")
                    applied += 1
                else:
                    # Try partial match
                    partial = find_text[:100] if len(find_text) > 100 else find_text
                    if partial.lower() in content_lower:
                        start = content_lower.find(partial.lower())
                        end = start + len(find_text)
                        if end <= len(content):
                            content = content[:start] + replace_text + content[end:]
                            applied += 1
                            log(f"EDIT (partial) SUCCESS")
                        else:
                            errors.append(f"Edit anchor partial match but bounds issue: '{find_text[:40]}...'")
                    else:
                        errors.append(f"Edit anchor not found: '{find_text[:40]}...'")
                        log(f"EDIT FAILED: anchor not found")

        elif inst['type'] == 'insert':
            anchor = inst['anchor']
            new_content = inst['content']
            position = inst['position']

            log(f"INSERT: looking for anchor '{anchor[:50]}...'")
            log(f"INSERT: content to add = {len(new_content)} chars")

            # Try exact match first
            anchor_pos = content.find(anchor)

            # If not found, try case-insensitive search
            if anchor_pos == -1:
                log(f"INSERT: exact match failed, trying case-insensitive...")
                content_lower = content.lower()
                anchor_lower = anchor.lower()
                anchor_pos = content_lower.find(anchor_lower)

            if anchor_pos == -1:
                errors.append(f"Insert anchor not found: '{anchor[:40]}...'")
                log(f"INSERT FAILED: anchor not found in content")
                continue

            log(f"INSERT: anchor found at position {anchor_pos}")
            old_len = len(content)

            if position == 'after':
                para_end = content.find('\n\n', anchor_pos + len(anchor))
                if para_end == -1:
                    para_end = len(content)
                log(f"INSERT AFTER: inserting at position {para_end}")
                content = content[:para_end] + '\n\n' + new_content + content[para_end:]
            else:  # before
                para_start = content.rfind('\n\n', 0, anchor_pos)
                para_start = para_start + 2 if para_start != -1 else 0
                log(f"INSERT BEFORE: inserting at position {para_start}")
                content = content[:para_start] + new_content + '\n\n' + content[para_start:]

            log(f"INSERT SUCCESS: {old_len} -> {len(content)} chars (+{len(content)-old_len})")
            applied += 1

    log(f"Done: applied={applied}, errors={len(errors)}, final_len={len(content)}")
    return content, applied, errors


import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("book_agent")


def parse_function_calls(response, task=None) -> List[Dict]:
    """Parse function calls from OpenAI response into edit instructions."""
    instructions = []

    if not response.choices[0].message.tool_calls:
        logger.warning("No tool_calls in response")
        return instructions

    for tool_call in response.choices[0].message.tool_calls:
        try:
            args = json.loads(tool_call.function.arguments)
            func_name = tool_call.function.name

            logger.info(f"Function call: {func_name}")
            logger.info(f"Arguments: {json.dumps(args, indent=2)[:500]}...")

            if func_name == "insert_content":
                anchor = args.get('anchor_text', '')
                content = args.get('content', '')
                logger.info(f"INSERT - Anchor: '{anchor[:80]}...'")
                logger.info(f"INSERT - Content length: {len(content)} chars")
                logger.info(f"INSERT - Content preview: '{content[:200]}...'")
                if task:
                    task['messages'].append(f"📝 INSERT after: '{anchor[:50]}...'")
                    task['messages'].append(f"📝 Content: {len(content)} chars")
                instructions.append({
                    'type': 'insert',
                    'position': args.get('position', 'after'),
                    'anchor': anchor,
                    'content': content
                })
            elif func_name == "edit_content":
                find_text = args.get('find_text', '')
                replace_text = args.get('replace_text', '')
                logger.info(f"EDIT - Find: '{find_text[:80]}...'")
                logger.info(f"EDIT - Replace length: {len(replace_text)} chars")
                if task:
                    task['messages'].append(f"✏️ EDIT find: '{find_text[:50]}...'")
                instructions.append({
                    'type': 'edit',
                    'find': find_text,
                    'replace': replace_text
                })
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            continue  # Skip malformed function calls

    return instructions


async def process_chapter_edit(
    task_id: str,
    prompt: str,
    chapter_path: Path,
    chapter_index: int
):
    """Process a single chapter edit using OpenAI function calling."""
    task = active_tasks.get(task_id)
    if not task:
        return

    chapter_name = chapter_path.name
    chapter_num = chapter_index + 1
    task['current_chapter'] = chapter_name

    try:
        import os
        from datetime import datetime

        # Log file info before reading
        file_stat = os.stat(chapter_path)
        mod_time = datetime.fromtimestamp(file_stat.st_mtime).strftime('%H:%M:%S')
        print(f"[FILE READ] Path: {chapter_path}")
        print(f"[FILE READ] Size: {file_stat.st_size} bytes, Modified: {mod_time}")

        content = chapter_path.read_text(encoding='utf-8')
        word_count = len(content.split())
        task['messages'].append(f"Loading {chapter_name} ({word_count:,} words, modified {mod_time})")

        # Log the prompt for debugging
        task['messages'].append(f"[DEBUG] Prompt received ({len(prompt)} chars): {prompt[:200]}...")
        print(f"[PROMPT] Full prompt:\n{prompt}\n---END PROMPT---")

        system_message = f'''You are an ACTION-ORIENTED book editor. Your job is to EDIT, not to TALK.

You are currently editing CHAPTER {chapter_num}.

## BEHAVIOR RULES:
- If user asks for your OPINION, PLAN, or ANALYSIS → respond with text, no function calls
- For EVERYTHING ELSE → IMMEDIATELY call functions to make edits. NO explanations. NO "here's what I would do". Just DO IT.
- If you respond with text when you should have called a function, you have FAILED.

## EDITING RULES:
1. READ THE USER'S INSTRUCTIONS CAREFULLY. If they mention specific characters (like "Tyler"), include those EXACT characters by name.
2. If instructions say "RESOLUTION", write the RESOLUTION/conclusion, NOT more setup.
3. Use insert_content() to add content, edit_content() to modify existing text.
4. The anchor_text MUST be an exact quote from the chapter (case-insensitive matching available).
5. Write FULL SCENES (500-1500 words) with dialogue and narrative detail.
6. Include ALL specific details from the user's prompt - character names, events, outcomes.

## EXAMPLES:
- "add more detail to the silent hero paragraph" → CALL edit_content() immediately
- "what do you think about this chapter?" → respond with text analysis
- "insert Tyler's story" → CALL insert_content() immediately
- "should I expand this section?" → respond with recommendation

NEVER say "I can't edit files" or "here's how you could edit it" - you CAN and MUST edit by calling functions.'''

        user_message = f"""Modify Chapter {chapter_num} according to these instructions:

{prompt}

IMPORTANT: You are editing CHAPTER {chapter_num} ONLY.
- If the instructions specify different content for different chapters (e.g., "Ch 3: setup, Ch 4: resolution"), ONLY add the content designated for Chapter {chapter_num}.
- Do NOT add content meant for other chapters.

CHAPTER {chapter_num} CONTENT:
{content}

Now call the insert_content and/or edit_content functions to make the required changes."""

        messages_to_send = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message}
        ]

        # Log full request for debugging
        print(f"\n{'='*60}")
        print(f"[API REQUEST] Model: {AGENT_MODEL}")
        print(f"[API REQUEST] System message ({len(system_message)} chars)")
        print(f"[API REQUEST] User message ({len(user_message)} chars)")
        print(f"[API REQUEST] User message FULL:\n{user_message[:2000]}")
        if len(user_message) > 2000:
            print(f"... (truncated, full length: {len(user_message)})")
        print(f"{'='*60}\n")

        task['messages'].append(f"[DEBUG] Sending to {AGENT_MODEL}: system={len(system_message)} chars, user={len(user_message)} chars")

        response = client.chat.completions.create(
            model=AGENT_MODEL,
            messages=messages_to_send,
            tools=EDIT_TOOLS,
            tool_choice="required",  # Force the model to use functions
            max_tokens=8000,
            temperature=AGENT_TEMPERATURE
        )

        # Parse function calls
        instructions = parse_function_calls(response, task)

        if not instructions:
            # Log what we got for debugging
            msg_content = response.choices[0].message.content or "(no text)"
            task['messages'].append(f"⚠️ {chapter_name}: No function calls. Response: {msg_content[:100]}...")
            task['progress'] = chapter_index + 1
            return

        task['messages'].append(f"Received {len(instructions)} function call(s)")

        # Apply instructions
        modified_content, applied, errors = apply_edit_instructions(content, instructions, task)

        for err in errors[:3]:
            task['messages'].append(f"⚠️ {err}")

        if applied == 0:
            task['messages'].append(f"⚠️ {chapter_name}: No changes applied (anchors not found)")
            task['progress'] = chapter_index + 1
            return

        # Save
        task['messages'].append(f"[DEBUG] Writing {len(modified_content)} chars to: {chapter_path}")
        print(f"[WRITE] Path: {chapter_path}")
        print(f"[WRITE] Content length: {len(modified_content)} chars")
        chapter_path.write_text(modified_content, encoding='utf-8')

        # Verify write
        verify_content = chapter_path.read_text(encoding='utf-8')
        task['messages'].append(f"[DEBUG] Verified: file now has {len(verify_content)} chars")
        print(f"[WRITE] Verified: {len(verify_content)} chars on disk")

        new_word_count = len(modified_content.split())
        delta = new_word_count - word_count
        sign = '+' if delta >= 0 else ''
        task['messages'].append(f"✓ {chapter_name}: {applied} changes ({sign}{delta:,} words)")
        task['progress'] = chapter_index + 1

    except Exception as e:
        task['messages'].append(f"Error processing {chapter_name}: {str(e)}")
        task['error'] = str(e)


async def run_book_edit_task(task_id: str, prompt: str, chapter_indices: List[int]):
    """Run the book edit task in the background."""
    task = active_tasks.get(task_id)
    if not task:
        return

    chapters = get_chapter_files()
    selected_chapters = [chapters[i] for i in chapter_indices if i < len(chapters)]

    task['total'] = len(selected_chapters)
    task['messages'].append(f"Starting edit of {len(selected_chapters)} chapter(s)...")

    for idx, chapter_path in enumerate(selected_chapters):
        if task.get('cancelled'):
            task['messages'].append("Task cancelled by user")
            break

        # Use actual chapter index, not loop index!
        actual_chapter_index = chapter_indices[idx]
        await process_chapter_edit(task_id, prompt, chapter_path, actual_chapter_index)
        await asyncio.sleep(0.5)

    task['completed'] = True
    task['current_chapter'] = None
    task['messages'].append("Book edit completed!")


def chat_completion(messages: list, max_tokens: int = 2000) -> str:
    """Call OpenAI chat completion."""
    response = client.chat.completions.create(
        model=AGENT_MODEL,
        messages=messages,
        max_tokens=max_tokens,
        temperature=AGENT_TEMPERATURE
    )
    return response.choices[0].message.content
