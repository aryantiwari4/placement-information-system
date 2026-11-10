import os
import uuid
import logging
from flask import Flask, render_template, request, jsonify, flash, redirect, url_for
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge

import config
from extractor.pdf_reader import extract_pdf_text, PDFExtractionError
from extractor.cleaner import clean_text
from extractor.parser import parse_resume

# Setup logging (Security note: do not log complete resume contents)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config.from_object(config)


@app.errorhandler(RequestEntityTooLarge)
def handle_file_too_large(e):
    max_mb = app.config.get("MAX_CONTENT_LENGTH", 16 * 1024 * 1024) // (1024 * 1024)
    return (
        render_template(
            "index.html",
            error=f"File exceeds the maximum allowed size of {max_mb} MB.",
        ),
        413,
    )


@app.get("/")
def home():
    """Render upload page with clean interface."""
    return render_template("index.html")


@app.get("/health")
def health_check():
    """Health check endpoint for status monitoring."""
    return jsonify({"status": "ok", "app": "Resume Information Extractor"})


@app.post("/extract")
def extract():
    """Process uploaded PDF resume, extract sections/entities, and display results."""
    file = request.files.get("resume")
    if not file or not file.filename:
        return render_template("index.html", error="Please select a resume to upload.")

    # Extension verification
    original_filename = secure_filename(file.filename) or "resume.pdf"
    ext = os.path.splitext(original_filename)[1].lower()
    if ext not in app.config.get("ALLOWED_EXTENSIONS", {".pdf"}):
        return render_template(
            "index.html",
            error="Only text-based PDF files are supported.",
        )

    # Secure unique file name generation to prevent collision or path traversal
    safe_name = f"{uuid.uuid4().hex}_{original_filename}"
    upload_path = os.path.join(app.config["UPLOAD_FOLDER"], safe_name)

    try:
        file.save(upload_path)
        logger.info(f"Received file: {original_filename} (saved as {safe_name})")

        # 1. Read PDF text stream
        raw_text = extract_pdf_text(upload_path)

        # Scanned PDF or empty text check
        if not raw_text or not raw_text.strip():
            return render_template(
                "index.html",
                error="The uploaded PDF contains no selectable text. It may be an image-only or scanned document.",
            )

        # 2. Clean text
        cleaned_text = clean_text(raw_text)

        # 3. Parse resume
        result = parse_resume(cleaned_text)

        # Check if cleanup requested
        if app.config.get("DELETE_AFTER_PROCESSING", False):
            try:
                os.remove(upload_path)
            except OSError:
                pass

        return render_template(
            "result.html",
            result=result,
            filename=original_filename,
        )

    except PDFExtractionError as exc:
        logger.error(f"PDF extraction error: {exc}")
        return render_template(
            "index.html",
            error=f"Could not read PDF: {str(exc)}",
        )
    except Exception as exc:
        logger.exception("Unexpected parsing error occurred")
        return render_template(
            "index.html",
            error="An unexpected error occurred while parsing the resume. Please ensure the file is a valid PDF.",
        )


@app.post("/api/extract")
def extract_api():
    """Programmatic API endpoint returning JSON output for automated integration and testing."""
    file = request.files.get("resume")
    if not file or not file.filename:
        return jsonify({"error": "No file uploaded under key 'resume'"}), 400

    original_filename = secure_filename(file.filename) or "resume.pdf"
    ext = os.path.splitext(original_filename)[1].lower()
    if ext not in app.config.get("ALLOWED_EXTENSIONS", {".pdf"}):
        return jsonify({"error": "Only PDF files supported"}), 400

    safe_name = f"{uuid.uuid4().hex}_{original_filename}"
    upload_path = os.path.join(app.config["UPLOAD_FOLDER"], safe_name)

    try:
        file.save(upload_path)
        raw_text = extract_pdf_text(upload_path)
        if not raw_text or not raw_text.strip():
            return (
                jsonify(
                    {
                        "error": "The PDF contains no selectable text (scanned/image-only).",
                        "status": "unreadable_text",
                    }
                ),
                422,
            )

        cleaned = clean_text(raw_text)
        result = parse_resume(cleaned)
        return jsonify({"success": True, "result": result}), 200

    except Exception as exc:
        return jsonify({"error": str(exc)}), 500
    finally:
        if os.path.exists(upload_path) and app.config.get("DELETE_AFTER_PROCESSING", False):
            try:
                os.remove(upload_path)
            except OSError:
                pass


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="127.0.0.1", port=port, debug=True)

