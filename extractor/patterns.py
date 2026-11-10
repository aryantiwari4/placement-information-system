import re
from typing import Dict, List, Set

# Regex patterns adhering strictly to project documentation
EMAIL_RE = re.compile(
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
)

PHONE_RE = re.compile(
    r"(?<!\d)(?:\+?\d[\d ()-]{7,}\d)(?!\d)"
)

URL_RE = re.compile(
    r"\b(?:https?://)?(?:www\.)?[A-Za-z0-9.-]+\.[A-Za-z]{2,}(?:/[^\s,;\)]*)?\b"
)

DATE_RANGE_RE = re.compile(
    r"\b(?:19|20)\d{2}\s*(?:-|–|—|to)\s*(?:present|current|(?:19|20)\d{2})\b",
    re.I
)

# Controlled skill vocabulary
# Starts with the documentation's core set and expands with standard industry skills
SKILLS: Set[str] = {
    # Core from documentation
    "Python", "Java", "C", "C++", "JavaScript", "SQL",
    "HTML", "CSS", "Flask", "Django", "React",
    "Git", "GitHub", "Docker", "AWS", "Machine Learning",
    "Pandas", "NumPy", "TensorFlow",

    # Expanded programming languages & web
    "TypeScript", "Go", "Rust", "C#", "PHP", "Ruby", "Kotlin", "Swift", "R",
    "Node.js", "Express", "FastAPI", "Vue", "Angular", "Next.js", "Tailwind CSS",
    "Bootstrap", "GraphQL", "REST API",

    # Databases & Cloud / DevOps
    "PostgreSQL", "MySQL", "MongoDB", "Redis", "SQLite", "Firebase",
    "Kubernetes", "Linux", "CI/CD", "Azure", "GCP", "Google Cloud",
    "Terraform", "Jenkins", "Nginx",

    # AI / ML & Data Science
    "PyTorch", "Scikit-Learn", "Keras", "Deep Learning", "NLP",
    "Computer Vision", "Data Analysis", "Matplotlib", "Seaborn",
}


def clean_phone_number(raw_phone: str) -> str:
    """Normalize extracted phone string, removing excess whitespace and trailing symbols."""
    phone = raw_phone.strip(" ,.-;")
    # Collapse multiple spaces
    phone = re.sub(r"\s+", " ", phone)
    return phone


def is_valid_phone(phone_str: str) -> bool:
    """Check if candidate phone string has a sensible digit count (between 7 and 15 digits)."""
    digits = re.sub(r"\D", "", phone_str)
    # Reject strings that are pure dates or too short / too long
    if len(digits) < 7 or len(digits) > 15:
        return False
    # Reject common date-like numbers e.g. 20202024
    if re.fullmatch(r"(19|20)\d{6}", digits):
        return False
    return True


def clean_url(url: str, emails: List[str]) -> str:
    """Clean extracted URL and discard domain fragments belonging to emails."""
    cleaned = url.strip(".,;:()[]{}<>\"'")
    # If the URL is just an email domain (e.g., gmail.com), discard it
    for email in emails:
        if "@" in email:
            domain = email.split("@")[-1].lower()
            if cleaned.lower() == domain or cleaned.lower() == f"www.{domain}":
                return ""
    return cleaned


def extract_contacts(text: str) -> Dict[str, List[str]]:
    """Extract emails, phone numbers, and URLs from text according to project rules."""
    if not text:
        return {"emails": [], "phones": [], "urls": []}

    # Extract emails
    emails = sorted(set(EMAIL_RE.findall(text)))

    # Extract and filter phone numbers
    raw_phones = PHONE_RE.findall(text)
    valid_phones = []
    for p in raw_phones:
        cleaned_p = clean_phone_number(p)
        if is_valid_phone(cleaned_p) and cleaned_p not in valid_phones:
            valid_phones.append(cleaned_p)
    valid_phones = sorted(valid_phones)

    # Extract and filter URLs
    raw_urls = URL_RE.findall(text)
    valid_urls = []
    for u in raw_urls:
        c_url = clean_url(u, emails)
        if c_url and c_url not in valid_urls:
            valid_urls.append(c_url)
    valid_urls = sorted(valid_urls)

    return {
        "emails": emails,
        "phones": valid_phones,
        "urls": valid_urls,
    }


def extract_skills(text: str) -> List[str]:
    """Extract skills from text against the controlled vocabulary.

    Uses word-boundary matching for short names (e.g., 'C', 'R', 'Go')
    to prevent false positives inside words like 'candidate', 'education', etc.
    """
    if not text:
        return []

    found = set()
    text_lower = text.lower()

    for skill in SKILLS:
        skill_clean = skill.strip()
        # For very short skills or single-letter skills, use strict regex word boundary
        if len(skill_clean) <= 2 or skill_clean in {"Go", "C", "R", "C++", "C#"}:
            pattern = rf"(?<!\w){re.escape(skill_clean)}(?!\w)"
            if re.search(pattern, text, flags=re.IGNORECASE):
                found.add(skill_clean)
        else:
            # Case-insensitive boundary search
            pattern = rf"\b{re.escape(skill_clean.lower())}\b"
            if re.search(pattern, text_lower):
                found.add(skill_clean)

    return sorted(list(found))


def find_date_ranges(text: str) -> List[str]:
    """Find date ranges (e.g. 2020-2024, 2021 to Present) in text."""
    if not text:
        return []
    return DATE_RANGE_RE.findall(text)

