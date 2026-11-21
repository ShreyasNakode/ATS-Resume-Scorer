import io
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import PyPDF2
from docx import Document

from backend.core.config import MAX_FILE_SIZE_BYTES, MAX_FILE_SIZE_MB
from backend.utils.file_utils import (
    FileParsingError,
    FileValidationError,
    TextExtractionError,
    detect_file_type,
    log_error,
    log_info,
    log_warning,
    with_fallback,
)


def validate_file(file_data: bytes, filename: str) -> Tuple[bool, str, Optional[str]]:
    """Validate file size and determine supported format."""
    file_size_bytes = len(file_data)
    if file_size_bytes > MAX_FILE_SIZE_BYTES:
        size_mb = file_size_bytes / (1024 * 1024)
        return False, f"File size ({size_mb:.2f} MB) exceeds maximum limit of {MAX_FILE_SIZE_MB} MB.", None

    if file_size_bytes == 0:
        return False, "Uploaded file is empty. Please check your file and try again.", None

    file_type = detect_file_type(file_data, filename)
    if not file_type or file_type not in ("pdf", "docx", "doc", "txt"):
        return (
            False,
            f"Unsupported file format for '{filename}'. Please upload a PDF (.pdf) or Word document (.docx).",
            None,
        )

    return True, "", file_type


def _extract_pdf_hyperlinks_pypdf2(file_data: bytes) -> List[str]:
    """Extract embedded URLs and hyperlinked text using PyPDF2 annotations."""
    urls = []
    try:
        reader = PyPDF2.PdfReader(io.BytesIO(file_data))
        for page in reader.pages:
            annots = page.get("/Annots")
            if not annots:
                continue
            for annot_ref in annots:
                try:
                    annot = annot_ref.get_object()
                    if annot.get("/Subtype") == "/Link":
                        action = annot.get("/A", {})
                        uri = action.get("/URI", "")
                        if isinstance(uri, bytes):
                            uri = uri.decode("utf-8", errors="ignore")
                        if uri and isinstance(uri, str) and uri.strip().startswith("http"):
                            urls.append(uri.strip())
                except Exception:
                    continue
    except Exception as exc:
        log_warning(f"Hyperlink extraction error: {exc}", context="PyPDF2")
    return urls


def _extract_pdf_with_pypdf2(file_data: bytes) -> str:
    """Extract full text from PDF using PyPDF2 with page parsing and hyperlink discovery."""
    text_parts = []
    try:
        reader = PyPDF2.PdfReader(io.BytesIO(file_data))
        num_pages = len(reader.pages)
        for idx in range(num_pages):
            page = reader.pages[idx]
            extracted = page.extract_text()
            if extracted:
                text_parts.append(extracted)

        full_text = "\n".join(text_parts).strip()
        hyperlinks = _extract_pdf_hyperlinks_pypdf2(file_data)
        if hyperlinks:
            full_text += "\n" + "\n".join(hyperlinks)

        if not full_text.strip():
            raise TextExtractionError(
                "PyPDF2 extracted empty text. PDF may be an image scan or password-protected."
            )
        return full_text
    except Exception as exc:
        raise TextExtractionError(f"PyPDF2 extraction failure: {exc}") from exc


def _extract_pdf_with_pdfplumber(file_data: bytes) -> str:
    """Secondary PDF text extraction fallback using pdfplumber."""
    try:
        import pdfplumber
        text_parts = []
        with pdfplumber.open(io.BytesIO(file_data)) as pdf:
            for page in pdf.pages:
                extracted = page.extract_text()
                if extracted:
                    text_parts.append(extracted)
        full_text = "\n".join(text_parts).strip()
        if not full_text:
            raise TextExtractionError("pdfplumber extracted no text.")
        return full_text
    except Exception as exc:
        raise TextExtractionError(f"pdfplumber extraction failure: {exc}") from exc


def extract_text_from_pdf(file_data: bytes) -> str:
    """Extract text from PDF using PyPDF2 as primary, pdfplumber as fallback."""
    try:
        result, used_fallback = with_fallback(
            _extract_pdf_with_pypdf2,
            _extract_pdf_with_pdfplumber,
            file_data,
            log_fallback=True,
        )
        if used_fallback:
            log_info("PDF text extracted via secondary pdfplumber fallback.", context="resume_parser")
        return result
    except Exception as exc:
        log_error(exc, context="extract_text_from_pdf")
        raise FileParsingError(
            "Failed to extract readable text from PDF. Ensure the document is not password-protected "
            "or a scanned raster image without selectable text."
        ) from exc


def extract_text_from_docx(file_data: bytes) -> str:
    """Extract text from Microsoft Word .docx using python-docx."""
    try:
        doc = Document(io.BytesIO(file_data))
        text_parts = []

        # 1. Paragraphs
        for p in doc.paragraphs:
            if p.text.strip():
                text_parts.append(p.text.strip())

        # 2. Tables and cells
        for table in doc.tables:
            for row in table.rows:
                row_cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                if row_cells:
                    text_parts.append(" | ".join(row_cells))

        # 3. Extract hyperlinks from relationships
        hyperlinks = []
        try:
            for rel in doc.part.rels.values():
                if "hyperlink" in rel.reltype.lower():
                    url = getattr(rel, "_target", "")
                    if isinstance(url, str) and url.startswith("http"):
                        hyperlinks.append(url)
        except Exception:
            pass

        full_text = "\n".join(text_parts).strip()
        if hyperlinks:
            full_text += "\n" + "\n".join(hyperlinks)

        if not full_text:
            raise FileParsingError("The DOCX document contains no selectable text or is corrupted.")

        log_info(f"Extracted {len(full_text)} chars from DOCX using python-docx.", context="resume_parser")
        return full_text
    except Exception as exc:
        log_error(exc, context="extract_text_from_docx")
        raise FileParsingError(f"Failed to extract text from DOCX file: {exc}") from exc


def extract_text_from_txt(file_data: bytes) -> str:
    """Decode plain text file with multiple encoding fallbacks."""
    for enc in ("utf-8", "latin-1", "cp1252"):
        try:
            return file_data.decode(enc).strip()
        except UnicodeDecodeError:
            continue
    return file_data.decode("utf-8", errors="ignore").strip()


def extract_text(file_data: bytes, file_type: str) -> str:
    """Route document bytes to appropriate parser."""
    if file_type == "pdf":
        return extract_text_from_pdf(file_data)
    elif file_type == "docx":
        return extract_text_from_docx(file_data)
    elif file_type == "txt":
        return extract_text_from_txt(file_data)
    elif file_type == "doc":
        raise FileValidationError(
            "Legacy binary .doc files are not directly supported. "
            "Please convert your document to .docx or .pdf in Microsoft Word or Google Docs."
        )
    else:
        raise FileValidationError(f"Unsupported file type: {file_type}")


def parse_resume_file(file_data: bytes, filename: str) -> Tuple[str, Dict]:
    """Top-level resume extraction pipeline."""
    is_valid, err_msg, file_type = validate_file(file_data, filename)
    if not is_valid:
        raise FileValidationError(err_msg)

    text = extract_text(file_data, file_type)
    cleaned_text = re.sub(r"\r\n|\r", "\n", text)
    cleaned_text = re.sub(r"[ \t]+", " ", cleaned_text)
    cleaned_text = re.sub(r"\n{3,}", "\n\n", cleaned_text).strip()

    metadata = {
        "filename": filename,
        "file_type": file_type,
        "file_size_bytes": len(file_data),
        "text_length": len(cleaned_text),
        "success": True,
    }
    return cleaned_text, metadata
