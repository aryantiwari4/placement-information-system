import os
import io
import pytest
from extractor.cleaner import clean_text
from extractor.sections import split_sections, normalize_heading, is_heading, match_heading_category
from extractor.patterns import (
    extract_contacts,
    extract_skills,
    find_date_ranges,
    clean_phone_number,
    is_valid_phone,
    SKILLS,
)
from extractor.normalizer import create_empty_result, validate, normalize_result
from extractor.parser import guess_name, parse_resume, extract_education, extract_experience
from app import app


SAMPLE_RESUME_TEXT = """
Jane Doe
Software Engineer
jane.doe@example.com | +1 (555) 234-5678 | https://github.com/janedoe | https://linkedin.com/in/janedoe

Education
Bachelor of Technology in Computer Science
State University of Technology
2018 - 2022
• Graduated with Honors (CGPA: 3.8/4.0)
• Relevant coursework: Algorithms, Distributed Systems

Work Experience
Senior Backend Developer
Acme Cloud Solutions
2022 - Present
• Designed and developed scalable REST APIs in Python using Flask and Docker
• Optimized PostgreSQL query performance, reducing 95th percentile latency by 35%
• Mentored junior engineers and led code reviews

Projects
Automated Resume Parser
2023 - 2024
• Built modular information extraction pipeline with Python, Regex and Flask
• Integrated automated validation and honest reporting

Technical Skills
Python, JavaScript, SQL, Flask, Docker, AWS, Git, GitHub, Machine Learning, PostgreSQL

Certifications
AWS Certified Solutions Architect
TensorFlow Developer Certificate
"""


def test_clean_text():
    raw = "Jane  Doe\xa0\xa0\xa0Software Engineer  \n\n\n\n\nSkills:\t\tPython"
    cleaned = clean_text(raw)
    assert "\xa0" not in cleaned
    assert "  " not in cleaned
    assert "\n\n\n" not in cleaned
    assert "Jane Doe" in cleaned
    assert "Skills: Python" in cleaned


def test_heading_normalization_and_detection():
    assert normalize_heading("TECHNICAL SKILLS") == "technical skills"
    assert normalize_heading("Work Experience:") == "work experience"
    assert is_heading("Work Experience") is True
    assert is_heading("Education") is True
    assert is_heading("Key Projects") is True
    assert is_heading("Certifications & Licenses") is True
    assert is_heading("This is a long sentence explaining experience.") is False


def test_section_splitting():
    sections = split_sections(SAMPLE_RESUME_TEXT)
    assert "education" in sections
    assert "experience" in sections
    assert "projects" in sections
    assert "skills" in sections
    assert "certifications" in sections
    assert "Bachelor of Technology" in sections["education"]
    assert "Acme Cloud Solutions" in sections["experience"]


def test_email_extraction():
    text = "Please reach out to student@example.com or support@company.org for details."
    result = extract_contacts(text)
    assert "student@example.com" in result["emails"]
    assert "support@company.org" in result["emails"]


def test_phone_extraction():
    text = "Mobile: +1 555-123-4567, Alternative: (987) 654-3210. Zip code is 90210."
    result = extract_contacts(text)
    assert len(result["phones"]) >= 1
    # Check that zip code 90210 is not captured as a phone number
    for p in result["phones"]:
        digits = "".join(filter(str.isdigit, p))
        assert len(digits) >= 7


def test_url_extraction_filters_email_domain():
    text = "Email: jane@testdomain.com. Portfolio: https://jane-portfolio.dev and github.com/jane"
    result = extract_contacts(text)
    assert "https://jane-portfolio.dev" in result["urls"]
    assert "github.com/jane" in result["urls"]
    # Ensure raw testdomain.com is filtered out as an email domain
    assert "testdomain.com" not in result["urls"]


def test_skill_extraction():
    skills_text = "Skills: Python, SQL, Flask, Git, Docker and AWS"
    extracted = extract_skills(skills_text)
    assert "Python" in extracted
    assert "SQL" in extracted
    assert "Flask" in extracted
    assert "Docker" in extracted
    assert "AWS" in extracted


def test_skill_boundary_no_false_positive():
    # Make sure 'C' or 'Go' doesn't falsely match inside words like 'Candidate' or 'Good'
    text = "Candidate is Good at Communication"
    extracted = extract_skills(text)
    assert "C" not in extracted
    assert "Go" not in extracted


def test_name_heuristic():
    name = guess_name(SAMPLE_RESUME_TEXT)
    assert name == "Jane Doe"


def test_date_range_extraction():
    text = "Worked at Acme Corp from 2020 - 2023 and 2023 to Present."
    ranges = find_date_ranges(text)
    assert len(ranges) >= 2


def test_stable_result_schema():
    empty = create_empty_result()
    required_keys = ["name", "contact", "skills", "education", "experience", "projects", "certifications", "warnings", "status"]
    for key in required_keys:
        assert key in empty


def test_validation_warnings():
    incomplete = {
        "name": None,
        "contact": {"email": "invalid_email_format", "phone": None, "links": []},
        "skills": [],
    }
    warnings = validate(incomplete)
    assert any("Candidate name could not be detected" in w for w in warnings)
    assert any("Email format may be invalid" in w for w in warnings)
    assert any("No skills were detected" in w for w in warnings)


def test_end_to_end_resume_parse():
    parsed = parse_resume(SAMPLE_RESUME_TEXT)
    assert parsed["name"] == "Jane Doe"
    assert parsed["contact"]["email"] == "jane.doe@example.com"
    assert "+1 (555) 234-5678" in (parsed["contact"]["phone"] or "")
    assert "Python" in parsed["skills"]
    assert "Flask" in parsed["skills"]
    assert len(parsed["education"]) > 0
    assert len(parsed["experience"]) > 0
    assert len(parsed["projects"]) > 0
    assert len(parsed["certifications"]) > 0
    assert parsed["status"]["name"] == "Detected"
    assert parsed["status"]["email"] == "Detected"


def test_flask_app_routes():
    client = app.test_client()
    # Test GET /
    res_home = client.get("/")
    assert res_home.status_code == 200
    assert b"Extract Resume Information" in res_home.data

    # Test GET /health
    res_health = client.get("/health")
    assert res_health.status_code == 200
    assert b"Resume Information Extractor" in res_health.data

    # Test POST /extract with no file
    res_no_file = client.post("/extract")
    assert res_no_file.status_code == 200
    assert b"Please select a resume" in res_no_file.data

    # Test POST /extract with invalid extension
    data = {"resume": (io.BytesIO(b"dummy text"), "resume.txt")}
    res_invalid = client.post("/extract", data=data, content_type="multipart/form-data")
    assert res_invalid.status_code == 200
    assert b"Only text-based PDF files are supported" in res_invalid.data

    # Test POST /extract with valid sample PDF
    pdf_sample_path = os.path.join(os.path.dirname(__file__), "..", "sample_resumes", "sample_1_standard.pdf")
    if os.path.exists(pdf_sample_path):
        with open(pdf_sample_path, "rb") as f:
            pdf_bytes = f.read()
        res_valid = client.post(
            "/extract",
            data={"resume": (io.BytesIO(pdf_bytes), "sample_1_standard.pdf")},
            content_type="multipart/form-data",
        )
        assert res_valid.status_code == 200
        assert b"Alex Morgan" in res_valid.data
        assert b"alex.morgan@techcorp.io" in res_valid.data

    # Test POST /api/extract with valid sample PDF
    if os.path.exists(pdf_sample_path):
        with open(pdf_sample_path, "rb") as f:
            pdf_bytes = f.read()
        res_api = client.post(
            "/api/extract",
            data={"resume": (io.BytesIO(pdf_bytes), "sample_1_standard.pdf")},
            content_type="multipart/form-data",
        )
        assert res_api.status_code == 200
        json_data = res_api.get_json()
        assert json_data["success"] is True
        assert json_data["result"]["name"] == "Alex Morgan"

