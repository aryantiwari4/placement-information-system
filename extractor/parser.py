import re
from typing import Any, Dict, List, Optional

from .cleaner import clean_text
from .sections import split_sections, is_heading
from .patterns import (
    extract_contacts,
    extract_skills,
    find_date_ranges,
    DATE_RANGE_RE,
)
from .normalizer import normalize_result

# Degree and educational keywords
DEGREE_KEYWORDS = [
    r"\bb\.?\s*tech\b",
    r"\bm\.?\s*tech\b",
    r"\bb\.?\s*e\.?\b",
    r"\bm\.?\s*e\.?\b",
    r"\bb\.?\s*s\.?\b",
    r"\bm\.?\s*s\.?\b",
    r"\bb\.?\s*sc\b",
    r"\bm\.?\s*sc\b",
    r"\bbachelor(?:'s)?\b",
    r"\bmaster(?:'s)?\b",
    r"\bph\.?d\b",
    r"\bdoctorate\b",
    r"\bdiploma\b",
    r"\bhigh school\b",
    r"\bsecondary school\b",
]
DEGREE_RE = re.compile("|".join(DEGREE_KEYWORDS), re.IGNORECASE)


def looks_like_contact(line: str) -> bool:
    """Check if a line contains emails, phone numbers, or web URLs."""
    line_clean = line.strip()
    if not line_clean:
        return True

    # Email signal
    if "@" in line_clean:
        return True

    # Phone signal (7 or more contiguous/spaced digits)
    if re.search(r"\d{7,}", line_clean):
        return True

    # Web URL / handles
    if line_clean.lower().startswith(("http://", "https://", "www.", "linkedin.com", "github.com")):
        return True

    # Address / Zip signals (e.g. 5-6 digit pin/zip)
    if re.search(r"\b\d{5,6}\b", line_clean) and any(w in line_clean.lower() for w in ["street", "road", "ave", "lane", "city", "state", "india", "usa"]):
        return True

    return False


def guess_name(text: str) -> Optional[str]:
    """Heuristic to detect candidate name from the top non-empty lines.

    Inspects the first 8 non-empty lines, rejecting contacts, URLs,
    and section headings, and checks word count <= 5.
    """
    lines = [x.strip() for x in text.splitlines() if x.strip()]
    for line in lines[:8]:
        # Filter out contacts, URLs, long lines, and section headings
        words = line.split()
        if not looks_like_contact(line) and 1 <= len(words) <= 5:
            if not is_heading(line):
                # Ensure the line has alphabetical characters and isn't a generic resume title
                letters_only = re.sub(r"[^A-Za-z]", "", line)
                if len(letters_only) >= 2 and line.lower() not in {"resume", "curriculum vitae", "cv", "portfolio"}:
                    return line
    return None


def split_into_entry_blocks(text: str) -> List[str]:
    """Split section text into discrete entry blocks by double newlines or bullet sequences."""
    if not text:
        return []

    # Try splitting by double newline first
    blocks = [b.strip() for b in re.split(r"\n\s*\n", text) if b.strip()]
    if len(blocks) > 1:
        return blocks

    # If all items are on single lines, split by lines starting with bullets or date ranges
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    aggregated: List[str] = []
    current: List[str] = []

    for line in lines:
        has_date = bool(DATE_RANGE_RE.search(line))
        is_bullet = line.startswith(("•", "-", "*", "–"))

        if (has_date or (not is_bullet and current)) and current:
            aggregated.append("\n".join(current))
            current = [line]
        else:
            current.append(line)

    if current:
        aggregated.append("\n".join(current))

    return aggregated if aggregated else [text]


def extract_education(section_text: str) -> List[Dict[str, Any]]:
    """Extract education entries with degree, institution, date ranges, and details."""
    if not section_text:
        return []

    entries: List[Dict[str, Any]] = []
    blocks = split_into_entry_blocks(section_text)

    for block in blocks:
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        if not lines:
            continue

        dates = find_date_ranges(block)
        date_str = dates[0] if dates else None

        # Look for degree name
        degree_match = DEGREE_RE.search(block)
        degree_name = None
        if degree_match:
            # Try to grab the line containing the degree
            for l in lines:
                if DEGREE_RE.search(l):
                    degree_name = l
                    break

        institution = None
        for l in lines:
            if l != degree_name and any(term in l.lower() for term in ["university", "college", "institute", "school", "academy", "polytechnic"]):
                institution = l
                break

        # Collect bullet details
        details = [l.lstrip("•-*– \t") for l in lines if l not in {degree_name, institution}]

        entries.append({
            "raw_block": block,
            "title": degree_name or lines[0],
            "institution": institution,
            "date_range": date_str,
            "details": details,
        })

    return entries


def extract_experience(section_text: str) -> List[Dict[str, Any]]:
    """Extract work experience entries with title/role, company, date ranges, and bullet points."""
    if not section_text:
        return []

    entries: List[Dict[str, Any]] = []
    blocks = split_into_entry_blocks(section_text)

    for block in blocks:
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        if not lines:
            continue

        dates = find_date_ranges(block)
        date_str = dates[0] if dates else None

        header_line = lines[0]
        # Bullet details are lines starting with bullets or following the header
        bullets = [l.lstrip("•-*– \t") for l in lines[1:] if l.strip()]

        entries.append({
            "raw_block": block,
            "title": header_line,
            "date_range": date_str,
            "bullets": bullets if bullets else lines[1:],
        })

    return entries


def extract_projects(section_text: str) -> List[Dict[str, Any]]:
    """Extract project entries with title, technologies, and description bullets."""
    if not section_text:
        return []

    entries: List[Dict[str, Any]] = []
    blocks = split_into_entry_blocks(section_text)

    for block in blocks:
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        if not lines:
            continue

        dates = find_date_ranges(block)
        date_str = dates[0] if dates else None
        title = lines[0]

        # Extract tech stack if indicated by '|' or 'Tech:' or 'Tools:'
        tech_used = []
        if "|" in title:
            parts = title.split("|", 1)
            title = parts[0].strip()
            tech_used = extract_skills(parts[1])

        bullets = [l.lstrip("•-*– \t") for l in lines[1:] if l.strip()]

        entries.append({
            "raw_block": block,
            "title": title,
            "date_range": date_str,
            "tech": tech_used or extract_skills(block),
            "description": bullets,
        })

    return entries


def extract_certifications(section_text: str) -> List[str]:
    """Extract certifications as cleaned individual item strings."""
    if not section_text:
        return []

    lines = [line.strip() for line in section_text.splitlines() if line.strip()]
    certs: List[str] = []
    for line in lines:
        # Strip leading bullets or numbers
        cleaned = re.sub(r"^[\d\.\•\-\*\–\s]+", "", line).strip()
        if cleaned and cleaned not in certs:
            certs.append(cleaned)
    return certs


def parse_resume(text: str) -> Dict[str, Any]:
    """End-to-end resume parser connecting section detection, patterns, and extraction.

    Follows the modular specification:
    1. Splits document into recognized sections.
    2. Extracts candidate contacts (email, phone, URLs).
    3. Guesses candidate name with first-line heuristics.
    4. Extracts skills from the Skills section with fallback to whole document.
    5. Extracts education, experience, projects, and certifications.
    6. Normalizes the output into a stable schema with validation warnings and status badges.
    """
    cleaned_text = clean_text(text)
    sections = split_sections(cleaned_text)
    contacts = extract_contacts(cleaned_text)

    # Search skills section first, with whole-document fallback as specified in section 10
    skills_in_section = extract_skills(sections.get("skills", ""))
    if not skills_in_section:
        skills = extract_skills(cleaned_text)
    else:
        # Also include any high-confidence skills from the whole text
        skills = sorted(list(set(skills_in_section) | set(extract_skills(cleaned_text))))

    primary_email = contacts["emails"][0] if contacts["emails"] else None
    primary_phone = contacts["phones"][0] if contacts["phones"] else None

    raw_result = {
        "name": guess_name(cleaned_text),
        "contact": {
            "email": primary_email,
            "phone": primary_phone,
            "links": contacts["urls"],
        },
        "skills": skills,
        "education": extract_education(sections.get("education", "")),
        "experience": extract_experience(sections.get("experience", "")),
        "projects": extract_projects(sections.get("projects", "")),
        "certifications": extract_certifications(sections.get("certifications", "")),
        "raw_sections": sections,
    }

    return normalize_result(raw_result)

