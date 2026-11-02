"""Reading uploaded files (-> Claude content blocks) and writing generated files."""

import base64
import csv
import io
import os
import re
from dataclasses import dataclass
from typing import Optional

from . import config

MAX_UPLOAD_BYTES = 20 * 1024 * 1024
MAX_TEXT_CHARS = 80_000

TEXT_EXT = {
    ".txt", ".md", ".csv", ".tsv", ".json", ".xml", ".yaml", ".yml", ".html", ".htm", ".css",
    ".js", ".ts", ".tsx", ".jsx", ".py", ".java", ".c", ".cpp", ".h", ".cs", ".go", ".rs",
    ".php", ".rb", ".sql", ".sh", ".bat", ".ps1", ".ini", ".toml", ".log", ".rtf",
}
IMAGE_TYPES = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".gif": "image/gif", ".webp": "image/webp"}
SUPPORTED = sorted(TEXT_EXT | set(IMAGE_TYPES) | {".pdf", ".docx", ".xlsx", ".pptx"})


@dataclass
class Attachment:
    name: str
    kind: str  # "text" | "pdf" | "image"
    size: int
    text: Optional[str] = None
    data_b64: Optional[str] = None
    media_type: Optional[str] = None
    truncated: bool = False

    def block(self) -> dict:
        if self.kind == "pdf":
            return {"type": "document", "source": {"type": "base64", "media_type": "application/pdf", "data": self.data_b64}, "title": self.name}
        if self.kind == "image":
            return {"type": "image", "source": {"type": "base64", "media_type": self.media_type, "data": self.data_b64}}
        note = " (truncated)" if self.truncated else ""
        return {"type": "text", "text": f'<attachment name="{self.name}"{note}>\n{self.text}\n</attachment>'}


def safe_name(name: str) -> str:
    name = os.path.basename(name.replace("\\", "/"))
    name = re.sub(r"[^\w.\- ()ऀ-ॿ]", "_", name).strip(" .")
    return name[:120] or "file"


def _docx_text(data: bytes) -> str:
    import docx

    d = docx.Document(io.BytesIO(data))
    lines = [p.text for p in d.paragraphs]
    for t in d.tables:
        for row in t.rows:
            lines.append(" | ".join(c.text.strip() for c in row.cells))
    return "\n".join(lines)


def _xlsx_text(data: bytes) -> str:
    import openpyxl

    wb = openpyxl.load_workbook(io.BytesIO(data), read_only=True, data_only=True)
    out = []
    for ws in wb.worksheets:
        out.append(f"## Sheet: {ws.title}")
        for i, row in enumerate(ws.iter_rows(values_only=True)):
            if i >= 2000:
                out.append("... (more rows omitted)")
                break
            out.append("\t".join("" if v is None else str(v) for v in row))
    return "\n".join(out)


def _pptx_text(data: bytes) -> str:
    from pptx import Presentation

    out = []
    for n, slide in enumerate(Presentation(io.BytesIO(data)).slides, 1):
        out.append(f"## Slide {n}")
        for shape in slide.shapes:
            if shape.has_text_frame:
                out.append(shape.text_frame.text)
    return "\n".join(out)


def _pdf_text(data: bytes) -> str:
    """Text layer only (scanned pages have none). Never raises."""
    try:
        from pypdf import PdfReader

        return "\n".join((page.extract_text() or "") for page in PdfReader(io.BytesIO(data)).pages[:200])
    except Exception:
        return ""


def load(filename: str, data: bytes) -> Attachment:
    """Raises ValueError for unsupported or oversized files."""
    name = safe_name(filename)
    ext = os.path.splitext(name)[1].lower()
    if len(data) > MAX_UPLOAD_BYTES:
        raise ValueError("File is larger than 20 MB.")
    if not data:
        raise ValueError("File is empty.")
    if ext == ".pdf":
        text = _pdf_text(data)
        return Attachment(name, "pdf", len(data), text=text[:MAX_TEXT_CHARS], data_b64=base64.b64encode(data).decode(),
                          media_type="application/pdf", truncated=len(text) > MAX_TEXT_CHARS)
    if ext in IMAGE_TYPES:
        return Attachment(name, "image", len(data), data_b64=base64.b64encode(data).decode(), media_type=IMAGE_TYPES[ext])
    if ext in TEXT_EXT:
        text = data.decode("utf-8", errors="replace")
    elif ext == ".docx":
        text = _docx_text(data)
    elif ext == ".xlsx":
        text = _xlsx_text(data)
    elif ext == ".pptx":
        text = _pptx_text(data)
    else:
        raise ValueError(f"Unsupported file type '{ext}'. Supported: {', '.join(SUPPORTED)}")
    truncated = len(text) > MAX_TEXT_CHARS
    return Attachment(name, "text", len(data), text=text[:MAX_TEXT_CHARS], truncated=truncated)


def extract_text(filename: str, data: bytes) -> str:
    """All the text of a document (no length cut), for indexing. Images have no text."""
    name = safe_name(filename)
    ext = os.path.splitext(name)[1].lower()
    if len(data) > MAX_UPLOAD_BYTES:
        raise ValueError("File is larger than 20 MB.")
    if not data:
        raise ValueError("File is empty.")
    if ext == ".pdf":
        return _pdf_text(data)
    if ext in IMAGE_TYPES:
        raise ValueError("images need OCR, which is not available")
    if ext in TEXT_EXT:
        return data.decode("utf-8-sig", errors="replace")
    if ext == ".docx":
        return _docx_text(data)
    if ext == ".xlsx":
        return _xlsx_text(data)
    if ext == ".pptx":
        return _pptx_text(data)
    raise ValueError(f"unsupported file type '{ext}'")


# ------------------------------------------------------------------ writing

CREATE_FORMATS = ["txt", "md", "html", "csv", "json", "py", "js", "docx", "xlsx", "pptx"]


def _add_runs(paragraph, text: str) -> None:
    for i, part in enumerate(text.split("**")):
        if part:
            paragraph.add_run(part).bold = i % 2 == 1


def _write_docx(content: str, path: str) -> None:
    import docx

    d = docx.Document()
    for line in content.splitlines():
        s = line.rstrip()
        if not s.strip():
            continue
        m = re.match(r"(#{1,4})\s+(.*)", s)
        if m:
            d.add_heading(m.group(2), level=len(m.group(1)))
        elif re.match(r"\s*[-*]\s+", s):
            _add_runs(d.add_paragraph(style="List Bullet"), re.sub(r"^\s*[-*]\s+", "", s))
        elif re.match(r"\s*\d+[.)]\s+", s):
            _add_runs(d.add_paragraph(style="List Number"), re.sub(r"^\s*\d+[.)]\s+", "", s))
        else:
            _add_runs(d.add_paragraph(), s)
    d.save(path)


def _write_xlsx(content: str, path: str) -> None:
    import openpyxl

    wb = openpyxl.Workbook()
    ws = wb.active
    for row in csv.reader(io.StringIO(content)):
        # Keep numbers numeric; a leading "=" is stored as text, not a formula.
        cells = []
        for v in row:
            try:
                cells.append(float(v) if "." in v else int(v))
            except ValueError:
                cells.append(v.lstrip("=") if v.startswith("=") else v)
        ws.append(cells)
    wb.save(path)


def _write_pptx(content: str, path: str) -> None:
    from pptx import Presentation

    prs = Presentation()
    slide = None
    body = None
    for line in content.splitlines():
        s = line.rstrip()
        if not s.strip():
            continue
        m = re.match(r"#{1,2}\s+(.*)", s)
        if m:
            slide = prs.slides.add_slide(prs.slide_layouts[1])
            slide.shapes.title.text = m.group(1)
            body = slide.placeholders[1].text_frame
            body.clear()
            first = True
            continue
        if slide is None:
            slide = prs.slides.add_slide(prs.slide_layouts[1])
            slide.shapes.title.text = "Presentation"
            body = slide.placeholders[1].text_frame
            first = True
        text = re.sub(r"^\s*(?:[-*]|\d+[.)])\s+", "", s).replace("**", "")
        p = body.paragraphs[0] if first else body.add_paragraph()
        first = False
        p.text = text
    prs.save(path)


def save_generated(filename: str, content: str) -> str:
    """Write a generated file into OUTPUT_DIR and return its stored name."""
    os.makedirs(config.OUTPUT_DIR, exist_ok=True)
    name = safe_name(filename)
    base, ext = os.path.splitext(name)
    ext = ext.lower().lstrip(".")
    if ext not in CREATE_FORMATS:
        ext = "txt"
    name = f"{base}.{ext}"
    n = 1
    while os.path.exists(os.path.join(config.OUTPUT_DIR, name)):
        n += 1
        name = f"{base} ({n}).{ext}"
    path = os.path.join(config.OUTPUT_DIR, name)
    if ext == "docx":
        _write_docx(content, path)
    elif ext == "xlsx":
        _write_xlsx(content, path)
    elif ext == "pptx":
        _write_pptx(content, path)
    else:
        # utf-8 with BOM for csv so Excel shows Hindi text correctly
        with open(path, "w", encoding="utf-8-sig" if ext == "csv" else "utf-8", newline="") as f:
            f.write(content)
    return name


def save_bytes(filename: str, data: bytes) -> str:
    """Write finished binary output (a .docx or .pdf) into OUTPUT_DIR and return its stored name."""
    os.makedirs(config.OUTPUT_DIR, exist_ok=True)
    base, ext = os.path.splitext(safe_name(filename))
    ext = ext.lower().lstrip(".") if ext.lower() in (".docx", ".pdf") else "docx"
    name, n = f"{base}.{ext}", 1
    while os.path.exists(os.path.join(config.OUTPUT_DIR, name)):
        n += 1
        name = f"{base} ({n}).{ext}"
    with open(os.path.join(config.OUTPUT_DIR, name), "wb") as f:
        f.write(data)
    return name


# ------------------------------------------------------------------ converting

CONVERT_TARGETS = {"docx", "txt", "md", "xlsx", "csv", "pptx"}


def _tsv_to_csv(text: str) -> str:
    out = io.StringIO()
    w = csv.writer(out)
    for line in text.splitlines():
        if line.startswith("## Sheet:") or line.startswith("... (more rows"):
            continue
        w.writerow(line.split("\t"))
    return out.getvalue()


def convert(att: "Attachment", fmt: str) -> str:
    """Convert an uploaded file's text into another format. Returns the stored file name."""
    if fmt not in CONVERT_TARGETS:
        raise ValueError(f"Cannot convert to {fmt}")
    if att.kind == "image" or not att.text:
        raise ValueError("There is no readable text in this file.")
    base, src = os.path.splitext(att.name)
    src = src.lower()
    if fmt in ("xlsx", "csv"):
        if src == ".xlsx":
            content = _tsv_to_csv(att.text)
        elif src in (".csv", ".tsv"):
            content = att.text if src == ".csv" else _tsv_to_csv(att.text)
        else:
            raise ValueError("Only CSV or Excel files can become spreadsheets.")
    else:
        content = att.text
    return save_generated(f"{base}.{fmt}", content)
