"""
Extracts plain text from an uploaded resume/JD file so the same
downstream AI pipeline can be used regardless of file format.

Supports: .pdf, .docx, .txt
"""

import io
from PyPDF2 import PdfReader
import docx


def extract_text_from_file(file_storage):
    """
    file_storage: a werkzeug FileStorage object from request.files
    Returns: extracted plain text (str)
    """
    filename = file_storage.filename.lower()
    raw_bytes = file_storage.read()

    if filename.endswith(".pdf"):
        return _extract_pdf(raw_bytes)
    elif filename.endswith(".docx"):
        return _extract_docx(raw_bytes)
    elif filename.endswith(".txt"):
        return raw_bytes.decode("utf-8", errors="ignore")
    else:
        raise ValueError("Unsupported file type. Please upload .pdf, .docx, or .txt")


def _extract_pdf(raw_bytes):
    reader = PdfReader(io.BytesIO(raw_bytes))
    text_parts = [page.extract_text() or "" for page in reader.pages]
    return "\n".join(text_parts)


def _extract_docx(raw_bytes):
    document = docx.Document(io.BytesIO(raw_bytes))
    paragraphs = [p.text for p in document.paragraphs]
    return "\n".join(paragraphs)
