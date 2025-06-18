import os
import unicodedata
import re
import sys
import re
import argparse

def sanitize_markdown(text: str) -> str:
    """Clean up problematic unicode and normalize markdown content."""
    text = unicodedata.normalize("NFKD", text)

    replacements = {
        "\u2014": "--",  # em dash
        "\u2013": "-",   # en dash
        "\u2018": "'",   # left single quote
        "\u2019": "'",   # right single quote
        "\u201C": '"',   # left double quote
        "\u201D": '"',   # right double quote
        "\u2026": "...", # ellipsis
        "\u00a0": " ",   # non-breaking space
        "\u0097": "--",  # rogue em dash
    }

    for bad, good in replacements.items():
        text = text.replace(bad, good)

    # Strip non-printable characters except tabs/newlines
    text = re.sub(r"[^\x09\x0A\x0D\x20-\x7E]", "", text)

    # Normalize line endings
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Collapse multiple blank lines
    text = re.sub(r'\n{3,}', '\n\n', text)

    text = re.sub(r'(?m)^\s*---\s*$', '***', text) # Replace --- with ***   

    return text

def sanitize_all_md_files(directory="."):
    for filename in os.listdir(directory):
        if filename.lower().endswith(".md"):
            filepath = os.path.join(directory, filename)
            print(f"Sanitizing: {filename}")
            try:
                with open(filepath, "r", encoding="windows-1252", errors="replace") as f:
                    lines = f.readlines()

                # Clean headers first
                cleaned_lines = list(clean_headers(lines))
                content = ''.join(cleaned_lines)
                
                # Then sanitize
                sanitized = sanitize_markdown(content)

                base, ext = os.path.splitext(filepath)
                clean_path = f"{base}_clean{ext}"
                with open(clean_path, "w", encoding="utf-8", newline="\n") as f:
                    f.write(sanitized)

                print(f"✓ Cleaned: {filename}")
            except Exception as e:
                print(f"✗ Failed: {filename} — {e}")

def clean_headers(lines):
    """
    Yield lines, skipping a header line if it's the same text
    as the most recent header (ignoring header level and blank lines).
    """
    last_header_text = None
    header_re = re.compile(r'^(#+)\s*(.+)$')

    for line in lines:
        match = header_re.match(line)
        if match:
            # Only compare the text part, ignore the number of #'s
            header_text = re.sub(r'\s+', ' ', match.group(2).strip())
            
            if header_text == last_header_text:
                # Skip this duplicate header regardless of level
                continue
            # Keep and update state
            yield line
            last_header_text = header_text
        else:
            # Non-header line - yield it but don't reset header state
            # Only reset if it's not just whitespace
            if line.strip():  # Non-empty line resets header tracking
                last_header_text = None
            yield line

def main():
    sanitize_all_md_files()


if __name__ == "__main__":
    main()
    
    
