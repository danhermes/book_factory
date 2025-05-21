import unicodedata
import re

def sanitize_markdown(text: str) -> str:
    """
    Cleans up markdown text to be UTF-8 safe and Pandoc-ready.
    Strips or replaces problematic Unicode characters (like Word-style em dashes, smart quotes),
    normalizes whitespace, and ensures consistent line endings.
    """
    # Normalize unicode to NFKD (more aggressive than NFC)
    text = unicodedata.normalize("NFKD", text)

    # Replace Windows-isms
    replacements = {
        "\u2014": "--",  # em dash
        "\u2013": "-",   # en dash
        "\u2018": "'",   # left single quote
        "\u2019": "'",   # right single quote
        "\u201C": '"',   # left double quote
        "\u201D": '"',   # right double quote
        "\u2026": "...", # ellipsis
        "\u00a0": " ",   # non-breaking space
        "\u0097": "--",  # rogue em dash from Latin-1
    }

    for bad, good in replacements.items():
        text = text.replace(bad, good)

    # Remove weird control characters (except tabs and newlines)
    text = re.sub(r"[^\x09\x0A\x0D\x20-\x7E]", "", text)

    # Standardize line endings
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Optional: collapse multiple blank lines to a maximum of two
    text = re.sub(r'\n{3,}', '\n\n', text)

    return text
