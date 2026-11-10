# Resume Information Extractor

A Python-first, modular, and explainable web application for extracting structured data from PDF resumes. Built with **Flask** and **pdfplumber**, focusing on transparent rule-based extraction rather than opaque black-box models.

---

## 1. Project Goal & Design Philosophy

The **Resume Information Extractor** accepts a resume in PDF format, extracts its text stream, identifies logical sections, normalizes entities (contacts, skills, education, work history, projects, certifications), and presents them in a clean, human-readable browser dashboard.

### Core Principles:
- **Explainable & Deterministic:** Every extraction decision stems from traceable regular expressions, section alias dictionaries, and controlled vocabularies.
- **Honest Status Reporting:** Avoids artificial numerical confidence percentages. Uses factual indicators: `Detected`, `Not detected`, and `Needs review`.
- **Clean Academic & Work Utility UI:** Free of neon gradients, marketing banners, or fake "AI demo" styling. Light neutral backgrounds, crisp typography, and high data density.
- **Privacy First:** Resumes are processed locally in memory with safe temporary storage and configurable immediate file deletion.

---

## 2. Architecture & Directory Layout

```
resume_extractor/
├── app.py                     # Flask web server, upload handling, error boundaries, API
├── config.py                  # Application settings, file size limits, security flags
├── requirements.txt           # Core Python dependencies
├── extractor/
│   ├── __init__.py            # Package exports
│   ├── pdf_reader.py          # pdfplumber wrapper with multi-column layout detection
│   ├── cleaner.py             # Whitespace, unicode bullets, and newline normalization
│   ├── sections.py            # Heading normalization, section aliases, text partitioning
│   ├── patterns.py            # Regex for emails, phones, URLs, date ranges & skill vocabulary
│   ├── parser.py              # Orchestrator: name heuristics, education/experience extraction
│   └── normalizer.py          # Stable schema enforcement, validation warnings & status badges
├── templates/
│   ├── index.html             # Compact upload interface with drag-and-drop & guidelines
│   └── result.html            # Professional results dashboard, JSON export & inspector
├── static/
│   └── style.css              # Custom slate/navy utility CSS (responsive, zero external CDN)
├── sample_resumes/            # 5 synthetic benchmark resumes for regression testing
├── tests/
│   ├── __init__.py
│   ├── test_extractor.py      # Unit tests (cleaner, contacts, skills, heuristics, Flask routes)
│   └── test_pdf_integration.py# End-to-end PDF parsing and section verification tests
├── create_sample_resumes.py   # Script generating 5 varied test PDFs
└── evaluate_accuracy.py       # Automated benchmark evaluating field-level accuracy
```

---

## 3. Data Processing Pipeline

```
┌──────────────┐     ┌──────────────┐     ┌──────────────────┐
│ Uploaded PDF │ ──> │  pdf_reader  │ ──> │     cleaner      │
│  (.pdf file) │     │ (pdfplumber) │     │(whitespace/text) │
└──────────────┘     └──────────────┘     └──────────────────┘
                                                    │
                                                    ▼
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│  Web UI / JSON   │ <── │    normalizer    │ <── │     sections     │
│ (result.html/API)│     │(validate/status) │     │ (heading aliases)│
└──────────────────┘     └──────────────────┘     └──────────────────┘
                                  ▲                         │
                                  │                         ▼
                         ┌──────────────────┐     ┌──────────────────┐
                         │      parser      │ <── │     patterns     │
                         │ (name/edu/exp)   │     │(regex/vocabulary)│
                         └──────────────────┘     └──────────────────┘
```

1. **PDF Text Stream Extraction (`extractor/pdf_reader.py`):**
   Reads text page by page using `pdfplumber`. Includes automatic column-gutter detection to extract two-column layouts in natural reading order without interleaving text.
2. **Text Normalization (`extractor/cleaner.py`):**
   Replaces non-breaking spaces (`\xa0`) and zero-width spaces, standardizes unicode bullets (`•`, `▪`, `·`), collapses horizontal spaces, and trims redundant line breaks.
3. **Section Partitioning (`extractor/sections.py`):**
   Scans lines for canonical section aliases (`skills`, `education`, `experience`, `projects`, `certifications`), isolating the header block and section bodies.
4. **Deterministic Entity Extraction (`extractor/patterns.py`):**
   - **Contacts:** Regex extraction of RFC-compliant emails, international phone formats, and profile links (GitHub, LinkedIn, personal domains).
   - **Skills:** Matches tokens against a controlled vocabulary with word boundary checks (preventing false matches like single-letter "C" inside "Candidate").
   - **Date Ranges:** Matches historical and current tenures (`2020 - 2024`, `2021 to Present`).
5. **Name Detection & Section Parsing (`extractor/parser.py`):**
   Inspects the document header, discarding contacts, URLs, and section headings to determine candidate name. Parses structured education degrees, job tenures, and project tech tags.
6. **Normalization & Honest Validation (`extractor/normalizer.py`):**
   Produces a fixed JSON schema with status badges (`Detected`, `Not detected`, `Needs review`) and flags format anomalies.

---

## 4. Quick Start & Execution

### Prerequisites
- Python 3.10+ (Tested on Python 3.12)

### 1. Activate Environment & Run Application
```powershell
# Navigate to project directory
cd C:\Users\Aryan\.gemini\antigravity\scratch\resume_extractor

# Activate existing virtual environment
.\.venv\Scripts\activate

# Run the Flask web application
python app.py
```
Open your browser and navigate to:
```
http://127.0.0.1:5000/
```

### 2. Run the Test Suite
```powershell
pytest tests -v
```
All 19 automated unit and integration tests will execute and verify all components.

### 3. Run the Field-Level Accuracy Benchmark
```powershell
python evaluate_accuracy.py
```
This tests the parser across 5 diverse resume layouts:
1. **Standard One-Page Resume:** (Alex Morgan) — Single column, standard headings.
2. **Two-Column Layout Resume:** (Priya Sharma) — Side-by-side skills and experience columns.
3. **Missing Sections Resume:** (Marcus Vance) — No education; tests warning emission.
4. **Unusual Headings Resume:** (Elena Rostova) — "Academic Background", "Competencies".
5. **Scanned / Image-Only Resume:** Blank text stream; tests graceful error alerts.

---

## 5. Security & Privacy Safeguards

- **Safe Generated Filenames:** Uploaded files are prefixed with cryptographic UUIDs to avoid collision and prevent directory traversal (`uuid.uuid4().hex + '_' + secure_filename(...)`).
- **File Size Limits:** Strictly constrained via `MAX_CONTENT_LENGTH = 16 * 1024 * 1024` (16MB).
- **Execution Safeguard:** Only text streams are extracted; no macro, script, or embedded executable content is executed.
- **Privacy & No Full Logging:** The server logs request metadata and filenames, never sensitive candidate text or full resumes.
- **Configurable Auto-Deletion:** `DELETE_AFTER_PROCESSING` in `config.py` can automatically remove uploads after parsing.

---

## 6. Viva Defense Guide (Questions & Answers)

1. **Why Python?**
   Python has the industry standard ecosystem for document parsing (`pdfplumber`, `pdfminer.six`), high-performance regex engines, and rich natural language toolkits.
2. **Why Flask?**
   Flask is lightweight, unopinionated, and introduces minimal boilerplate. It allows direct control over HTTP requests, file uploads, and template rendering without heavy framework overhead.
3. **Why Regex & Rule-Based Parsing instead of an LLM?**
   - **Cost & Latency:** Rule-based extraction executes in milliseconds with zero API costs.
   - **Explainability:** When a field is extracted or missed, the reason is 100% auditable through regex patterns or section dictionaries.
   - **Determinism:** LLMs suffer from hallucinations, high latency, and unpredictable output schemas; our parser guarantees an identical schema for every invocation.
4. **Why Section Detection?**
   Section detection provides context. For example, the word "Python" under a "Technical Skills" heading represents a candidate competency, whereas "Python" mentioned in an experience bullet represents tool usage. Partitioning prevents cross-contamination.
5. **What are the Primary Limitations?**
   - **Multi-column and tabular layouts:** Extracted text streams can interleave across column boundaries unless column-aware segmentation or spatial bounding boxes are used.
   - **Scanned or image-only documents:** PDFs without embedded text streams require optical character recognition (OCR, e.g. Tesseract) as an upstream pre-processing step.

