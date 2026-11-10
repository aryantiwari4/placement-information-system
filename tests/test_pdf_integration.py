import os
import pytest
from extractor.pdf_reader import extract_pdf_text
from extractor.cleaner import clean_text
from extractor.parser import parse_resume

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SAMPLE_DIR = os.path.join(BASE_DIR, "sample_resumes")


def test_resume_1_standard_pdf():
    pdf_path = os.path.join(SAMPLE_DIR, "sample_1_standard.pdf")
    assert os.path.exists(pdf_path)

    text = extract_pdf_text(pdf_path)
    cleaned = clean_text(text)
    result = parse_resume(cleaned)

    assert result["name"] == "Alex Morgan"
    assert result["contact"]["email"] == "alex.morgan@techcorp.io"
    assert "+1 (555) 987-6543" in result["contact"]["phone"]
    assert any("github.com/alexmorgan" in link for link in result["contact"]["links"])
    assert "Python" in result["skills"]
    assert "Docker" in result["skills"]
    assert "AWS" in result["skills"]
    assert len(result["education"]) > 0
    assert len(result["experience"]) > 0
    assert len(result["projects"]) > 0
    assert len(result["certifications"]) > 0
    assert len(result["warnings"]) == 0


def test_resume_2_twocolumn_pdf():
    pdf_path = os.path.join(SAMPLE_DIR, "sample_2_twocolumn.pdf")
    assert os.path.exists(pdf_path)

    text = extract_pdf_text(pdf_path)
    cleaned = clean_text(text)
    result = parse_resume(cleaned)

    assert result["name"] == "Priya Sharma"
    assert result["contact"]["email"] == "priya.sharma@example.com"
    assert "+91 9876543210" in result["contact"]["phone"]
    assert "Python" in result["skills"]
    assert "Machine Learning" in result["skills"]
    assert "TensorFlow" in result["skills"]


def test_resume_3_missing_sections_pdf():
    pdf_path = os.path.join(SAMPLE_DIR, "sample_3_missing_sections.pdf")
    assert os.path.exists(pdf_path)

    text = extract_pdf_text(pdf_path)
    cleaned = clean_text(text)
    result = parse_resume(cleaned)

    assert result["name"] == "Marcus Vance"
    assert result["contact"]["email"] == "marcus.vance@workmail.com"
    assert "Kubernetes" in result["skills"]
    assert "Docker" in result["skills"]
    # Education is deliberately missing in sample 3, so a warning should be registered
    assert result["status"]["education"] == "Not detected"
    assert any("Education section could not be identified" in w for w in result["warnings"])


def test_resume_4_unusual_headings_pdf():
    pdf_path = os.path.join(SAMPLE_DIR, "sample_4_unusual_headings.pdf")
    assert os.path.exists(pdf_path)

    text = extract_pdf_text(pdf_path)
    cleaned = clean_text(text)
    result = parse_resume(cleaned)

    assert result["name"] == "Elena Rostova"
    assert result["contact"]["email"] == "elena.rostova@academix.org"
    assert "Go" in result["skills"]
    assert "PostgreSQL" in result["skills"]
    # Unusual headings "Academic Background" and "Employment History" should be mapped properly
    assert result["status"]["education"] == "Detected"
    assert result["status"]["experience"] == "Detected"


def test_resume_5_scanned_empty_pdf():
    pdf_path = os.path.join(SAMPLE_DIR, "sample_5_scanned_empty.pdf")
    assert os.path.exists(pdf_path)

    text = extract_pdf_text(pdf_path)
    assert text.strip() == ""

