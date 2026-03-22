"""Extract text từ PDF (text layer hoặc OCR) và Markdown."""

import re
from pathlib import Path
from dataclasses import dataclass


@dataclass
class ExtractedDoc:
    text: str
    sections: list[dict]   # [{"heading": str, "level": int, "content": str}]
    page_count: int
    extraction_method: str  # pdfplumber | ocr | markdown


def extract_pdf(path: Path) -> ExtractedDoc:
    import pdfplumber
    sections = []
    full_text = ""

    with pdfplumber.open(path) as pdf:
        page_count = len(pdf.pages)
        for i, page in enumerate(pdf.pages):
            page_text = page.extract_text() or ""

            # Extract tables
            for table in page.extract_tables():
                rows = [" | ".join(str(c or "").strip() for c in row) for row in table if row]
                table_text = "\n".join(rows)
                page_text += f"\n\n[Bảng trang {i+1}]\n{table_text}"

            if page_text.strip():
                full_text += f"\n\n[Trang {i+1}]\n{page_text}"
                sections.append({
                    "heading": f"Trang {i+1}",
                    "level": 1,
                    "content": page_text,
                    "page": i + 1,
                })

    # Fallback OCR nếu không có text
    if len(full_text.strip()) < 100:
        return extract_pdf_ocr(path)

    return ExtractedDoc(
        text=full_text,
        sections=sections,
        page_count=page_count,
        extraction_method="pdfplumber",
    )


def extract_pdf_ocr(path: Path) -> ExtractedDoc:
    """Fallback OCR cho PDF scan — lazy import surya-ocr."""
    try:
        from surya.ocr import run_ocr
        from surya.model.detection.model import load_model as load_det
        from surya.model.recognition.model import load_model as load_rec
        from surya.model.recognition.processor import load_processor
        from PIL import Image
        import fitz  # pymupdf

        det_model, det_processor = load_det(), load_det()
        rec_model, rec_processor = load_rec(), load_processor()

        doc = fitz.open(path)
        full_text = ""
        sections = []

        for i, page in enumerate(doc):
            pix = page.get_pixmap(dpi=150)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            result = run_ocr([img], [["vi", "en"]], det_model, det_processor,
                             rec_model, rec_processor)
            page_text = " ".join([line.text for line in result[0].text_lines])
            full_text += f"\n\n[Trang {i+1} - OCR]\n{page_text}"
            sections.append({"heading": f"Trang {i+1}", "level": 1,
                             "content": page_text, "page": i+1})

        return ExtractedDoc(text=full_text, sections=sections,
                           page_count=len(doc), extraction_method="ocr")
    except ImportError:
        # surya-ocr không có — trả về empty với warning
        print(f"  WARN: surya-ocr chưa cài, không thể OCR {path.name}")
        return ExtractedDoc(text="", sections=[], page_count=0,
                           extraction_method="ocr_unavailable")


def extract_markdown(path: Path) -> ExtractedDoc:
    text = path.read_text(encoding="utf-8")
    pattern = r"^(#{1,3})\s+(.+)$"
    sections = []
    current = {"heading": "intro", "level": 0, "content": ""}

    for line in text.splitlines():
        match = re.match(pattern, line)
        if match:
            if current["content"].strip():
                sections.append(current)
            current = {
                "heading": match.group(2).strip(),
                "level": len(match.group(1)),
                "content": line + "\n",
            }
        else:
            current["content"] += line + "\n"

    if current["content"].strip():
        sections.append(current)

    return ExtractedDoc(
        text=text,
        sections=sections,
        page_count=0,
        extraction_method="markdown",
    )


def extract(path: Path) -> ExtractedDoc:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return extract_pdf(path)
    elif suffix in (".md", ".markdown"):
        return extract_markdown(path)
    else:
        raise ValueError(f"Unsupported file type: {suffix}")
