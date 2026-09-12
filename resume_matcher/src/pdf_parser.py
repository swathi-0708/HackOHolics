"""
pdf_parser.py
-------------
Extracts raw text from PDF files (job descriptions or resumes).

Strategy:
1. Try pdfplumber (best layout/text fidelity).
2. Fall back to pypdf if pdfplumber fails or returns empty text.
3. Raise a clear error if the PDF is scanned/image-only (no extractable text),
   since OCR is out of scope for this module.
"""

from __future__ import annotations
import os
from dataclasses import dataclass


class PDFParsingError(Exception):
    """Raised when a PDF cannot be parsed into usable text."""


@dataclass
class ParsedPDF:
    path: str
    filename: str
    text: str
    num_pages: int


def _extract_with_pdfplumber(path: str) -> tuple[str, int]:
    import pdfplumber

    text_parts = []
    with pdfplumber.open(path) as pdf:
        num_pages = len(pdf.pages)
        for page in pdf.pages:
            page_text = page.extract_text() or ""
            text_parts.append(page_text)
    return "\n".join(text_parts), num_pages


def _extract_with_pypdf(path: str) -> tuple[str, int]:
    from pypdf import PdfReader

    reader = PdfReader(path)
    num_pages = len(reader.pages)
    text_parts = [page.extract_text() or "" for page in reader.pages]
    return "\n".join(text_parts), num_pages


def parse_pdf(path: str, min_chars: int = 20) -> ParsedPDF:
    """
    Extract text from a single PDF file.

    Raises PDFParsingError if no usable text is found (e.g. a scanned
    image-only PDF that would need OCR).
    """
    if not os.path.isfile(path):
        raise PDFParsingError(f"File not found: {path}")

    filename = os.path.basename(path)
    text, num_pages = "", 0

    try:
        text, num_pages = _extract_with_pdfplumber(path)
    except Exception:
        pass

    if len(text.strip()) < min_chars:
        try:
            text2, num_pages2 = _extract_with_pypdf(path)
            if len(text2.strip()) > len(text.strip()):
                text, num_pages = text2, num_pages2
        except Exception:
            pass

    if len(text.strip()) < min_chars:
        raise PDFParsingError(
            f"Could not extract text from '{filename}'. It may be a scanned "
            f"image-only PDF that requires OCR, which this pipeline does not perform."
        )

    return ParsedPDF(path=path, filename=filename, text=text, num_pages=num_pages)


def parse_pdf_or_text(path: str) -> ParsedPDF:
    """
    Convenience wrapper: if `path` ends in .pdf, parse as PDF.
    If it ends in .txt, just read the raw text (useful for testing
    without generating PDFs).
    """
    if path.lower().endswith(".pdf"):
        return parse_pdf(path)
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    return ParsedPDF(path=path, filename=os.path.basename(path), text=text, num_pages=1)


def parse_directory(dir_path: str) -> list[ParsedPDF]:
    """Parse every .pdf/.txt file in a directory (non-recursive), sorted by filename."""
    results = []
    errors = []
    for fname in sorted(os.listdir(dir_path)):
        if not (fname.lower().endswith(".pdf") or fname.lower().endswith(".txt")):
            continue
        full_path = os.path.join(dir_path, fname)
        try:
            results.append(parse_pdf_or_text(full_path))
        except PDFParsingError as e:
            errors.append(str(e))
    if errors:
        print("[pdf_parser] Warnings while parsing directory:")
        for e in errors:
            print(f"  - {e}")
    return results
