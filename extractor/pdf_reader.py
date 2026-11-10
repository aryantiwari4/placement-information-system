import os
from typing import Dict, Any, List, Optional
import pdfplumber


class PDFExtractionError(Exception):
    """Raised when PDF reading or text extraction encounters an error."""
    pass


def _extract_page_text_column_aware(page) -> str:
    """Extract text from a PDF page, detecting multi-column layouts when present.

    If a two-column vertical gutter is detected below the header region, text
    is extracted in natural column order (header -> left column -> right column)
    to prevent text interleaving. Otherwise, falls back to standard extraction.
    """
    try:
        words = page.extract_words()
        if not words:
            return page.extract_text() or ""

        page_width = float(page.width)
        page_height = float(page.height)

        # Look for potential header cutoffs that do not bisect any word vertically
        clean_y_splits = []
        for y in range(40, int(page_height * 0.40)):
            if not any(w["top"] <= y <= w["bottom"] for w in words):
                clean_y_splits.append(y)

        # Check candidate horizontal split points
        for header_y in [y for y in clean_y_splits if 60 <= y <= 160]:
            body_words = [w for w in words if w["top"] >= header_y]
            if not body_words:
                continue

            # Check if text is present on both the left and right halves
            left_words = [w for w in body_words if w["x1"] < page_width * 0.5]
            right_words = [w for w in body_words if w["x0"] > page_width * 0.5]

            if len(left_words) >= 5 and len(right_words) >= 5:
                # Find if a clear vertical gutter exists between 30% and 70% of page width
                mid_start = int(page_width * 0.30)
                mid_end = int(page_width * 0.70)

                for gx in range(mid_start, mid_end, 4):
                    crossing = [w for w in body_words if w["x0"] < gx and w["x1"] > gx]
                    if not crossing:
                        # Found clear vertical column gutter
                        header_crop = page.crop((0, 0, page_width, header_y)).extract_text() or ""
                        left_crop = page.crop((0, header_y, gx, page_height)).extract_text() or ""
                        right_crop = page.crop((gx, header_y, page_width, page_height)).extract_text() or ""
                        return f"{header_crop}\n\n{left_crop}\n\n{right_crop}"

    except Exception:
        # Fall back to standard extraction if layout detection encounters any issue
        pass

    return page.extract_text() or ""


def extract_pdf_text(path: str) -> str:
    """Extract plain text from a text-based PDF file using pdfplumber.

    Supports both single-column and multi-column documents.

    Args:
        path: Path to the target PDF file.

    Returns:
        Consolidated string containing text from all pages separated by double newlines.

    Raises:
        PDFExtractionError: If the file is inaccessible, corrupted, or password-protected.
    """
    if not os.path.exists(path):
        raise PDFExtractionError(f"PDF file not found at path: {path}")

    pages = []
    try:
        with pdfplumber.open(path) as pdf:
            if not pdf.pages:
                return ""
            for page in pdf.pages:
                page_text = _extract_page_text_column_aware(page)
                pages.append(page_text)
    except Exception as exc:
        raise PDFExtractionError(f"Failed to read PDF file: {exc}") from exc

    return "\n\n".join(pages)


def extract_pdf_metadata(path: str) -> Dict[str, Any]:
    """Inspect basic metadata from the PDF (e.g. page count, title, author)."""
    if not os.path.exists(path):
        return {"page_count": 0, "metadata": {}}

    try:
        with pdfplumber.open(path) as pdf:
            return {
                "page_count": len(pdf.pages),
                "metadata": pdf.metadata or {},
            }
    except Exception:
        return {"page_count": 0, "metadata": {}}
