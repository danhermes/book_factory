import os
import unicodedata
import re

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

    return text

def sanitize_all_md_files(directory="."):
    for filename in os.listdir(directory):
        if filename.lower().endswith(".md"):
            filepath = os.path.join(directory, filename)
            print(f"Sanitizing: {filename}")
            try:
                with open(filepath, "r", encoding="windows-1252", errors="replace") as f:
                    content = f.read()

                sanitized = sanitize_markdown(content)

                base, ext = os.path.splitext(filepath)
                clean_path = f"{base}_clean{ext}"
                print(f"WRITING TO: {clean_path}")
                with open(clean_path, "w", encoding="utf-8", newline="\n") as f:
                    f.write(sanitized)

                print(f"✓ Cleaned: {filename}")
            except Exception as e:
                print(f"✗ Failed: {filename} — {e}")

if __name__ == "__main__":
    sanitize_all_md_files()
