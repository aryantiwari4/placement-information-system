import re
from typing import Dict, Optional, Tuple

SECTION_ALIASES = {
    "skills": {
        "skills",
        "technical skills",
        "core skills",
        "key skills",
        "technologies",
        "proficiencies",
        "competencies",
        "skills  tools",
        "skills tools",
        "technical proficiencies",
        "technical expertise",
        "programming skills",
        "computer skills",
        "areas of expertise",
    },
    "education": {
        "education",
        "academic background",
        "educational background",
        "educational qualifications",
        "academic qualifications",
        "academics",
        "academic history",
        "qualifications",
    },
    "experience": {
        "experience",
        "work experience",
        "employment",
        "professional experience",
        "work history",
        "employment history",
        "internships",
        "internship experience",
        "career summary",
        "professional background",
    },
    "projects": {
        "projects",
        "academic projects",
        "personal projects",
        "key projects",
        "technical projects",
        "notable projects",
        "selected projects",
    },
    "certifications": {
        "certifications",
        "certificates",
        "licenses",
        "certifications  licenses",
        "licenses  certifications",
        "courses",
        "credentials",
        "certifications and licenses",
    },
}


def normalize_heading(line: str) -> str:
    """Normalize a potential heading line by lowercasing and stripping non-alpha characters."""
    return re.sub(r"[^a-z ]", "", line.lower()).strip()


def match_heading_category(line: str) -> Optional[str]:
    """Check if a line matches any known section header category.

    Returns the canonical section name (e.g. 'skills') or None.
    """
    clean_line = line.strip()
    if not clean_line:
        return None

    # Section headings are generally short (usually 1-5 words)
    words = clean_line.split()
    if len(words) > 5:
        return None

    # Lines with standard end punctuation like '.' are usually sentences, not headers
    if clean_line.endswith((".", ",", ";")):
        return None

    norm = normalize_heading(clean_line)
    if not norm:
        return None

    for category, aliases in SECTION_ALIASES.items():
        if norm in aliases:
            return category

    return None


def is_heading(line: str) -> bool:
    """Predicate indicating whether a line is a section heading."""
    return match_heading_category(line) is not None


def split_sections(text: str) -> Dict[str, str]:
    """Segment a resume text into logical sections based on detected headings.

    Returns a dictionary mapping section names ('header', 'skills', 'education',
    'experience', 'projects', 'certifications', etc.) to the raw section text.
    """
    if not text:
        return {}

    sections: Dict[str, list] = {"header": []}
    current_section = "header"

    lines = text.split("\n")
    for raw_line in lines:
        line = raw_line.strip()
        category = match_heading_category(line)
        if category:
            current_section = category
            if current_section not in sections:
                sections[current_section] = []
        else:
            sections[current_section].append(raw_line)

    # Join the accumulated lines for each section
    return {k: "\n".join(v).strip() for k, v in sections.items() if "\n".join(v).strip()}

