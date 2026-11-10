import re


def clean_text(text: str) -> str:
    """Normalize extracted text while preserving punctuation, numbers, and case.

    Steps performed:
    1. Replaces non-breaking spaces (\\xa0) and zero-width spaces with standard space.
    2. Collapses consecutive horizontal whitespaces (spaces, tabs) to a single space.
    3. Normalizes excessive empty lines (3 or more newlines become double newlines).
    4. Trims trailing whitespace on lines.
    5. Normalizes bullet points to standard characters for uniform parsing.
    6. Strips leading and trailing outer whitespace.
    """
    if not text:
        return ""

    # Replace non-breaking spaces and zero-width spaces
    text = text.replace("\xa0", " ").replace("\u200b", "")

    # Replace carriage returns for consistent Unix-style newlines
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Standardize common unicode bullets to standard bullet / dash
    text = re.sub(r"[\u2022\u2023\u25E6\u2043\u2219\u25CF\u25AA\u25AB]", " • ", text)

    # Collapse consecutive horizontal whitespace (spaces, tabs)
    text = re.sub(r"[ \t]+", " ", text)

    # Trim spaces before newlines
    text = re.sub(r"[ \t]+\n", "\n", text)

    # Collapse excessive line breaks (3 or more -> 2)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()

