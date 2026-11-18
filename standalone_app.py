"""Resume Information Extractor - Single-File Standalone Application.

Contains the complete web application: Flask backend, text extractor,
regex entity recognition, section parser, normalizer, and embedded HTML/CSS templates.

Run with:
    pip install flask pdfplumber
    python standalone_app.py
"""

import os
import re
import uuid
import logging
from typing import Any, Dict, List, Optional
from flask import Flask, request, jsonify, render_template_string
from werkzeug.utils import secure_filename
import pdfplumber

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config["SECRET_KEY"] = "standalone-secret-key-2026"
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB limit
app.config["UPLOAD_FOLDER"] = os.path.join(os.path.abspath(os.path.dirname(__file__)), "uploads")
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

# ==============================================================================
# 1. TEXT CLEANING
# ==============================================================================
def clean_text(text: str) -> str:
    """Normalize extracted text while preserving punctuation, numbers, and case."""
    if not text:
        return ""
    text = text.replace("\xa0", " ").replace("\u200b", "")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[\u2022\u2023\u25E6\u2043\u2219\u25CF\u25AA\u25AB]", " • ", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

# ==============================================================================
# 2. SECTION DETECTION & ALIASES
# ==============================================================================
SECTION_ALIASES = {
    "skills": {
        "skills", "technical skills", "core skills", "key skills", "technologies",
        "proficiencies", "competencies", "skills tools", "technical proficiencies",
        "technical expertise", "programming skills", "computer skills",
    },
    "education": {
        "education", "academic background", "educational background",
        "educational qualifications", "academic qualifications", "academics",
        "academic history", "qualifications",
    },
    "experience": {
        "experience", "work experience", "employment", "professional experience",
        "work history", "employment history", "internships", "internship experience",
        "career summary", "professional background",
    },
    "projects": {
        "projects", "academic projects", "personal projects", "key projects",
        "technical projects", "notable projects", "selected projects",
    },
    "certifications": {
        "certifications", "certificates", "licenses", "certifications licenses",
        "courses", "credentials", "certifications and licenses",
    },
}

def normalize_heading(line: str) -> str:
    return re.sub(r"[^a-z ]", "", line.lower()).strip()

def match_heading_category(line: str) -> Optional[str]:
    clean_line = line.strip()
    if not clean_line or len(clean_line.split()) > 5 or clean_line.endswith((".", ",", ";")):
        return None
    norm = normalize_heading(clean_line)
    if not norm:
        return None
    for category, aliases in SECTION_ALIASES.items():
        if norm in aliases:
            return category
    return None

def is_heading(line: str) -> bool:
    return match_heading_category(line) is not None

def split_sections(text: str) -> Dict[str, str]:
    if not text:
        return {}
    sections: Dict[str, list] = {"header": []}
    current_section = "header"
    for raw_line in text.split("\n"):
        category = match_heading_category(raw_line.strip())
        if category:
            current_section = category
            if current_section not in sections:
                sections[current_section] = []
        else:
            sections[current_section].append(raw_line)
    return {k: "\n".join(v).strip() for k, v in sections.items() if "\n".join(v).strip()}

# ==============================================================================
# 3. REGEX PATTERNS & CONTROLLED VOCABULARY
# ==============================================================================
EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
PHONE_RE = re.compile(r"(?<!\d)(?:\+?\d[\d ()-]{7,}\d)(?!\d)")
URL_RE = re.compile(r"\b(?:https?://)?(?:www\.)?[A-Za-z0-9.-]+\.[A-Za-z]{2,}(?:/[^\s,;\)]*)?\b")
DATE_RANGE_RE = re.compile(r"\b(?:19|20)\d{2}\s*(?:-|–|—|to)\s*(?:present|current|(?:19|20)\d{2})\b", re.I)

DEGREE_KEYWORDS = [
    r"\bb\.?\s*tech\b", r"\bm\.?\s*tech\b", r"\bb\.?\s*e\.?\b", r"\bm\.?\s*e\.?\b",
    r"\bb\.?\s*s\.?\b", r"\bm\.?\s*s\.?\b", r"\bbachelor(?:'s)?\b", r"\bmaster(?:'s)?\b",
    r"\bph\.?d\b", r"\bdiploma\b", r"\bhigh school\b",
]
DEGREE_RE = re.compile("|".join(DEGREE_KEYWORDS), re.IGNORECASE)

SKILLS = {
    "Python", "Java", "C", "C++", "JavaScript", "SQL", "HTML", "CSS", "Flask", "Django",
    "React", "Git", "GitHub", "Docker", "AWS", "Machine Learning", "Pandas", "NumPy",
    "TensorFlow", "TypeScript", "Go", "Rust", "C#", "PHP", "Ruby", "Node.js", "Express",
    "FastAPI", "Vue", "Angular", "PostgreSQL", "MySQL", "MongoDB", "Redis", "SQLite",
    "Kubernetes", "Linux", "CI/CD", "Azure", "GCP", "PyTorch", "Scikit-Learn",
}

def extract_contacts(text: str) -> Dict[str, List[str]]:
    if not text:
        return {"emails": [], "phones": [], "urls": []}
    emails = sorted(set(EMAIL_RE.findall(text)))
    raw_phones = PHONE_RE.findall(text)
    phones = []
    for p in raw_phones:
        digits = re.sub(r"\D", "", p)
        if 7 <= len(digits) <= 15 and p.strip(" ,.-;") not in phones:
            phones.append(p.strip(" ,.-;"))
    raw_urls = URL_RE.findall(text)
    urls = []
    for u in raw_urls:
        c = u.strip(".,;:()[]{}<>\"'")
        is_email_domain = any("@" in em and (c.lower() == em.split("@")[-1].lower() or c.lower() == f"www.{em.split('@')[-1].lower()}") for em in emails)
        if c and not is_email_domain and c not in urls:
            urls.append(c)
    return {"emails": emails, "phones": sorted(phones), "urls": sorted(urls)}

def extract_skills(text: str) -> List[str]:
    if not text:
        return []
    found = set()
    text_lower = text.lower()
    for skill in SKILLS:
        s_clean = skill.strip()
        if len(s_clean) <= 2 or s_clean in {"Go", "C", "R", "C++", "C#"}:
            if re.search(rf"(?<!\w){re.escape(s_clean)}(?!\w)", text, re.IGNORECASE):
                found.add(s_clean)
        else:
            if re.search(rf"\b{re.escape(s_clean.lower())}\b", text_lower):
                found.add(s_clean)
    return sorted(list(found))

# ==============================================================================
# 4. PARSER & HEURISTICS
# ==============================================================================
def looks_like_contact(line: str) -> bool:
    line_clean = line.strip().lower()
    return "@" in line_clean or bool(re.search(r"\d{7,}", line_clean)) or line_clean.startswith(("http://", "https://", "www.", "linkedin.com", "github.com"))

def guess_name(text: str) -> Optional[str]:
    lines = [x.strip() for x in text.splitlines() if x.strip()]
    for line in lines[:8]:
        if not looks_like_contact(line) and 1 <= len(line.split()) <= 5 and not is_heading(line):
            if len(re.sub(r"[^A-Za-z]", "", line)) >= 2 and line.lower() not in {"resume", "curriculum vitae", "cv", "portfolio"}:
                return line
    return None

def extract_education(section_text: str) -> List[Dict[str, Any]]:
    if not section_text:
        return []
    entries = []
    blocks = [b.strip() for b in re.split(r"\n\s*\n", section_text) if b.strip()]
    for block in (blocks if len(blocks) > 1 else [section_text]):
        lines = [l.strip() for l in block.splitlines() if l.strip()]
        if not lines:
            continue
        dates = DATE_RANGE_RE.findall(block)
        degree_name = next((l for l in lines if DEGREE_RE.search(l)), lines[0])
        inst = next((l for l in lines if l != degree_name and any(t in l.lower() for t in ["university", "college", "institute", "school"])), None)
        entries.append({
            "title": degree_name,
            "institution": inst,
            "date_range": dates[0] if dates else None,
            "details": [l.lstrip("•-*– \t") for l in lines if l not in {degree_name, inst}],
        })
    return entries

def extract_experience(section_text: str) -> List[Dict[str, Any]]:
    if not section_text:
        return []
    entries = []
    blocks = [b.strip() for b in re.split(r"\n\s*\n", section_text) if b.strip()]
    for block in (blocks if len(blocks) > 1 else [section_text]):
        lines = [l.strip() for l in block.splitlines() if l.strip()]
        if not lines:
            continue
        dates = DATE_RANGE_RE.findall(block)
        entries.append({
            "title": lines[0],
            "date_range": dates[0] if dates else None,
            "bullets": [l.lstrip("•-*– \t") for l in lines[1:] if l.strip()],
        })
    return entries

def extract_projects(section_text: str) -> List[Dict[str, Any]]:
    if not section_text:
        return []
    entries = []
    blocks = [b.strip() for b in re.split(r"\n\s*\n", section_text) if b.strip()]
    for block in (blocks if len(blocks) > 1 else [section_text]):
        lines = [l.strip() for l in block.splitlines() if l.strip()]
        if not lines:
            continue
        dates = DATE_RANGE_RE.findall(block)
        title = lines[0].split("|")[0].strip() if "|" in lines[0] else lines[0]
        entries.append({
            "title": title,
            "date_range": dates[0] if dates else None,
            "tech": extract_skills(block),
            "description": [l.lstrip("•-*– \t") for l in lines[1:] if l.strip()],
        })
    return entries

def extract_certifications(section_text: str) -> List[str]:
    if not section_text:
        return []
    certs = []
    for line in section_text.splitlines():
        c = re.sub(r"^[\d\.\•\-\*\–\s]+", "", line).strip()
        if c and c not in certs:
            certs.append(c)
    return certs

# ==============================================================================
# 5. NORMALIZER & VALIDATOR
# ==============================================================================
def normalize_result(data: Dict[str, Any]) -> Dict[str, Any]:
    contact = data.get("contact") or {}
    email = contact.get("email")
    phone = contact.get("phone")
    name = data.get("name")
    skills = data.get("skills") or []

    warnings = []
    if not name:
        warnings.append("Candidate name could not be detected.")
    if not email:
        warnings.append("No contact email detected.")
    elif "@" not in email or "." not in email:
        warnings.append("Email format may be invalid.")
    if not phone:
        warnings.append("No phone number detected.")
    if not skills:
        warnings.append("No skills were detected from the controlled vocabulary.")

    status = {
        "name": "Detected" if name else "Not detected",
        "email": "Detected" if email and "@" in email and "." in email else ("Needs review" if email else "Not detected"),
        "phone": "Detected" if phone else "Not detected",
        "skills": "Detected" if skills else "Not detected",
        "education": "Detected" if data.get("education") else "Not detected",
        "experience": "Detected" if data.get("experience") else "Not detected",
        "projects": "Detected" if data.get("projects") else "Not detected",
        "certifications": "Detected" if data.get("certifications") else "Not detected",
    }

    return {
        "name": name,
        "contact": {"email": email, "phone": phone, "links": contact.get("links") or []},
        "skills": skills,
        "education": data.get("education") or [],
        "experience": data.get("experience") or [],
        "projects": data.get("projects") or [],
        "certifications": data.get("certifications") or [],
        "raw_sections": data.get("raw_sections") or {},
        "warnings": warnings,
        "status": status,
    }

# ==============================================================================
# 6. PDF EXTRACTION (MULTI-COLUMN AWARE)
# ==============================================================================
def extract_pdf_text(path: str) -> str:
    pages = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            try:
                words = page.extract_words()
                page_w, page_h = float(page.width), float(page.height)
                clean_y = [y for y in range(40, int(page_h * 0.4)) if not any(w["top"] <= y <= w["bottom"] for w in words)]
                extracted = False
                for hy in [y for y in clean_y if 60 <= y <= 160]:
                    body = [w for w in words if w["top"] >= hy]
                    if len([w for w in body if w["x1"] < page_w * 0.5]) >= 5 and len([w for w in body if w["x0"] > page_w * 0.5]) >= 5:
                        for gx in range(int(page_w * 0.3), int(page_w * 0.7), 4):
                            if not any(w["x0"] < gx and w["x1"] > gx for w in body):
                                h_crop = page.crop((0, 0, page_w, hy)).extract_text() or ""
                                l_crop = page.crop((0, hy, gx, page_h)).extract_text() or ""
                                r_crop = page.crop((gx, hy, page_w, page_h)).extract_text() or ""
                                pages.append(f"{h_crop}\n\n{l_crop}\n\n{r_crop}")
                                extracted = True
                                break
                    if extracted:
                        break
                if not extracted:
                    pages.append(page.extract_text() or "")
            except Exception:
                pages.append(page.extract_text() or "")
    return "\n\n".join(pages)

def parse_resume(text: str) -> Dict[str, Any]:
    cleaned = clean_text(text)
    sections = split_sections(cleaned)
    contacts = extract_contacts(cleaned)
    skills = extract_skills(sections.get("skills", "")) or extract_skills(cleaned)
    raw = {
        "name": guess_name(cleaned),
        "contact": {
            "email": contacts["emails"][0] if contacts["emails"] else None,
            "phone": contacts["phones"][0] if contacts["phones"] else None,
            "links": contacts["urls"],
        },
        "skills": sorted(list(set(skills))),
        "education": extract_education(sections.get("education", "")),
        "experience": extract_experience(sections.get("experience", "")),
        "projects": extract_projects(sections.get("projects", "")),
        "certifications": extract_certifications(sections.get("certifications", "")),
        "raw_sections": sections,
    }
    return normalize_result(raw)

# ==============================================================================
# 7. EMBEDDED HTML TEMPLATES
# ==============================================================================
INDEX_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Resume Information Extractor</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #f8fafc; color: #0f172a; margin: 0; padding: 0; }
        header { background: #fff; border-bottom: 1px solid #e2e8f0; padding: 14px 24px; display: flex; justify-content: space-between; align-items: center; }
        .logo { font-size: 18px; font-weight: 700; color: #1e3a8a; }
        main { max-width: 640px; margin: 40px auto; padding: 0 20px; }
        .card { background: #fff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 28px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
        .dropzone { border: 2px dashed #cbd5e1; border-radius: 6px; padding: 32px 20px; text-align: center; background: #fafbfc; position: relative; cursor: pointer; margin-bottom: 20px; }
        .dropzone input { position: absolute; width: 100%; height: 100%; top: 0; left: 0; opacity: 0; cursor: pointer; }
        .btn { display: block; width: 100%; padding: 12px; background: #1e3a8a; color: #fff; font-weight: 600; font-size: 15px; border: none; border-radius: 6px; cursor: pointer; }
        .btn:hover { background: #172554; }
        .error { background: #fee2e2; color: #991b1b; padding: 12px; border-radius: 6px; margin-bottom: 16px; font-size: 14px; }
        .note { font-size: 12px; color: #64748b; margin-top: 20px; line-height: 1.5; }
    </style>
</head>
<body>
    <header><div class="logo">📄 Resume Information Extractor</div><div>Modular Parser</div></header>
    <main>
        <div class="card">
            <h2>Extract Resume Information</h2>
            <p style="color:#64748b;font-size:14px;margin-bottom:20px;">Upload a PDF resume to extract contacts, skills, education, and experience deterministically.</p>
            {% if error %}<div class="error">⚠️ {{ error }}</div>{% endif %}
            <form action="/extract" method="post" enctype="multipart/form-data">
                <div class="dropzone">
                    <div style="font-size:32px;margin-bottom:8px;">📁</div>
                    <div><strong style="color:#2563eb;">Choose a PDF file</strong> or drag & drop</div>
                    <input type="file" name="resume" accept=".pdf" required onchange="document.getElementById('fn').innerText = this.files[0].name;">
                    <div id="fn" style="font-size:13px;color:#64748b;margin-top:8px;">No file chosen</div>
                </div>
                <button type="submit" class="btn">Extract information</button>
            </form>
            <div class="note">🔒 <strong>Privacy:</strong> Processed locally in memory. Only text-based PDFs supported.</div>
        </div>
    </main>
</body>
</html>
"""

RESULT_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{{ result.name or 'Extracted Resume' }}</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #f8fafc; color: #0f172a; margin: 0; padding: 24px; }
        .container { max-width: 900px; margin: 0 auto; }
        .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
        .card { background: #fff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 20px; margin-bottom: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
        .pill { font-size: 12px; padding: 3px 8px; border-radius: 999px; background: #dcfce7; color: #166534; font-weight: 600; }
        .skill-tag { display: inline-block; background: #f1f5f9; border: 1px solid #cbd5e1; padding: 3px 8px; border-radius: 4px; font-size: 13px; margin: 3px; }
        .btn { padding: 6px 12px; border-radius: 4px; font-size: 13px; text-decoration: none; border: 1px solid #cbd5e1; background: #fff; color: #334155; cursor: pointer; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <a href="/" class="btn">← Back to Upload</a>
            <button onclick="downloadJSON()" class="btn">Export JSON</button>
        </div>
        <div class="card">
            <span style="font-size:12px;text-transform:uppercase;color:#64748b;font-weight:600;">Candidate</span>
            <h1 style="margin:4px 0 12px;color:#1e3a8a;">{{ result.name or 'Name Not Detected' }}</h1>
            <p><strong>Email:</strong> {{ result.contact.email or 'Not detected' }} | <strong>Phone:</strong> {{ result.contact.phone or 'Not detected' }}</p>
            {% if result.contact.links %}
                <p><strong>Links:</strong> {% for l in result.contact.links %}<a href="{{ l }}" target="_blank" style="color:#2563eb;margin-right:8px;">{{ l }}</a>{% endfor %}</p>
            {% endif %}
        </div>
        <div class="card">
            <h3>Technical Skills ({{ result.skills|length }})</h3>
            <div>{% for s in result.skills %}<span class="skill-tag">{{ s }}</span>{% endfor %}</div>
        </div>
        {% if result.experience %}
        <div class="card">
            <h3>Work Experience</h3>
            {% for e in result.experience %}
                <div style="margin-bottom:14px;">
                    <strong>{{ e.title }}</strong> <span style="font-size:12px;color:#64748b;">{{ e.date_range or '' }}</span>
                    <ul>{% for b in e.bullets %}<li>{{ b }}</li>{% endfor %}</ul>
                </div>
            {% endfor %}
        </div>
        {% endif %}
        {% if result.education %}
        <div class="card">
            <h3>Education</h3>
            {% for ed in result.education %}
                <div><strong>{{ ed.title }}</strong> - {{ ed.institution or '' }} <span style="font-size:12px;color:#64748b;">{{ ed.date_range or '' }}</span></div>
            {% endfor %}
        </div>
        {% endif %}
    </div>
    <script>
        function downloadJSON() {
            const data = {{ result | tojson }};
            const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
            const a = document.createElement('a');
            a.href = URL.createObjectURL(blob);
            a.download = 'resume_parsed.json';
            a.click();
        }
    </script>
</body>
</html>
"""

# ==============================================================================
# 8. FLASK ROUTES
# ==============================================================================
@app.get("/")
def home():
    return render_template_string(INDEX_HTML)

@app.post("/extract")
def extract():
    file = request.files.get("resume")
    if not file or not file.filename:
        return render_template_string(INDEX_HTML, error="Please select a resume file.")
    if not file.filename.lower().endswith(".pdf"):
        return render_template_string(INDEX_HTML, error="Only PDF resumes are supported.")

    safe_name = f"{uuid.uuid4().hex}_{secure_filename(file.filename)}"
    save_path = os.path.join(app.config["UPLOAD_FOLDER"], safe_name)
    try:
        file.save(save_path)
        raw_text = extract_pdf_text(save_path)
        if not raw_text.strip():
            return render_template_string(INDEX_HTML, error="The PDF contains no selectable text (it may be scanned/image-only).")
        result = parse_resume(raw_text)
        return render_template_string(RESULT_HTML, result=result)
    finally:
        if os.path.exists(save_path):
            try:
                os.remove(save_path)
            except OSError:
                pass

@app.post("/api/extract")
def extract_api():
    file = request.files.get("resume")
    if not file or not file.filename:
        return jsonify({"error": "No file uploaded under key 'resume'"}), 400
    safe_name = f"{uuid.uuid4().hex}_{secure_filename(file.filename)}"
    save_path = os.path.join(app.config["UPLOAD_FOLDER"], safe_name)
    try:
        file.save(save_path)
        raw_text = extract_pdf_text(save_path)
        if not raw_text.strip():
            return jsonify({"error": "No selectable text"}), 422
        return jsonify({"success": True, "result": parse_resume(raw_text)})
    finally:
        if os.path.exists(save_path):
            try:
                os.remove(save_path)
            except OSError:
                pass

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
