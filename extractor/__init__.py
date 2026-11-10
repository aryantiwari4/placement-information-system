"""Resume Information Extractor package.

Provides modular text extraction, text cleaning, section detection,
pattern-based entity recognition, and result normalization for resumes.
"""

from .cleaner import clean_text
from .pdf_reader import extract_pdf_text
from .sections import split_sections, normalize_heading, is_heading
from .patterns import extract_contacts, extract_skills, find_date_ranges, SKILLS
from .normalizer import validate, create_empty_result, normalize_result
from .parser import parse_resume

__all__ = [
    "clean_text",
    "extract_pdf_text",
    "split_sections",
    "normalize_heading",
    "is_heading",
    "extract_contacts",
    "extract_skills",
    "find_date_ranges",
    "SKILLS",
    "validate",
    "create_empty_result",
    "normalize_result",
    "parse_resume",
]

