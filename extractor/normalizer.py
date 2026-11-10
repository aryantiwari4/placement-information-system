import re
from typing import Any, Dict, List


def create_empty_result() -> Dict[str, Any]:
    """Return a stable dictionary with standardized keys and defaults."""
    return {
        "name": None,
        "contact": {
            "email": None,
            "phone": None,
            "links": [],
        },
        "skills": [],
        "education": [],
        "experience": [],
        "projects": [],
        "certifications": [],
        "warnings": [],
        "status": {},
    }


def validate(result: Dict[str, Any]) -> List[str]:
    """Validate extracted result fields and return actionable warnings.

    Uses honest rule-based checks instead of arbitrary confidence numbers.
    """
    warnings: List[str] = []

    # Name check
    if not result.get("name"):
        warnings.append("Candidate name could not be detected.")

    # Email check
    contact = result.get("contact") or {}
    email = contact.get("email")
    if not email:
        warnings.append("No contact email detected.")
    elif "@" not in email or "." not in email:
        warnings.append("Email format may be invalid.")

    # Phone check
    phone = contact.get("phone")
    if not phone:
        warnings.append("No phone number detected.")
    elif len(re.sub(r"\D", "", phone)) < 10:
        warnings.append("Phone number appears shorter than standard (needs review).")

    # Skills check
    skills = result.get("skills") or []
    if not skills:
        warnings.append("No skills were detected from the controlled vocabulary.")

    # Education check
    education = result.get("education") or []
    if not education:
        warnings.append("Education section could not be identified.")

    # Experience check
    experience = result.get("experience") or []
    if not experience:
        warnings.append("Work experience section could not be identified.")

    return warnings


def compute_field_statuses(result: Dict[str, Any]) -> Dict[str, str]:
    """Calculate honest status indicators: 'Detected', 'Not detected', 'Needs review'."""
    contact = result.get("contact") or {}
    email = contact.get("email")
    phone = contact.get("phone")

    statuses = {}

    # Name
    statuses["name"] = "Detected" if result.get("name") else "Not detected"

    # Email
    if not email:
        statuses["email"] = "Not detected"
    elif "@" not in email or "." not in email.split("@")[-1]:
        statuses["email"] = "Needs review"
    else:
        statuses["email"] = "Detected"

    # Phone
    if not phone:
        statuses["phone"] = "Not detected"
    elif len(re.sub(r"\D", "", phone)) < 10:
        statuses["phone"] = "Needs review"
    else:
        statuses["phone"] = "Detected"

    # Links
    links = contact.get("links") or []
    statuses["links"] = "Detected" if links else "Not detected"

    # Sections
    statuses["skills"] = "Detected" if (result.get("skills") or []) else "Not detected"
    statuses["education"] = "Detected" if (result.get("education") or []) else "Not detected"
    statuses["experience"] = "Detected" if (result.get("experience") or []) else "Not detected"
    statuses["projects"] = "Detected" if (result.get("projects") or []) else "Not detected"
    statuses["certifications"] = "Detected" if (result.get("certifications") or []) else "Not detected"

    return statuses


def normalize_result(data: Dict[str, Any]) -> Dict[str, Any]:
    """Ensure result dictionary contains all expected keys, warnings, and field statuses."""
    base = create_empty_result()

    base["name"] = data.get("name")

    contact_data = data.get("contact") or {}
    base["contact"]["email"] = contact_data.get("email")
    base["contact"]["phone"] = contact_data.get("phone")
    base["contact"]["links"] = list(contact_data.get("links") or [])

    base["skills"] = list(data.get("skills") or [])
    base["education"] = list(data.get("education") or [])
    base["experience"] = list(data.get("experience") or [])
    base["projects"] = list(data.get("projects") or [])
    base["certifications"] = list(data.get("certifications") or [])

    # Include raw section texts if available for transparency
    if "raw_sections" in data:
        base["raw_sections"] = data["raw_sections"]

    # Compute validation warnings and honest status badges
    warnings = validate(base)
    base["warnings"] = warnings
    base["status"] = compute_field_statuses(base)

    return base

