import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Flask configuration
SECRET_KEY = os.environ.get("SECRET_KEY", "resume-extractor-dev-secret-key-2026")
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB maximum file size
ALLOWED_EXTENSIONS = {".pdf"}

# Security: automatically remove uploaded files after parsing
DELETE_AFTER_PROCESSING = False  # Set to True in production to immediately delete uploaded PDFs

# Ensure uploads directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

