"""Build a finished Word or PDF document from the blocks the Document studio sends. No AI involved.

A block is one of: heading, paragraph, quote, bullets, numbered, table, image, pagebreak.
Text may use **bold** and *italic*.
"""

import base64
import io
import os
import re
from typing import Any

_DEVANAGARI = re.compile(r"[\u0900-\u097F]")
MAX_IMAGE_BYTES = 10 * 1024 * 1024
MAX_TOTAL_IMAGE_BYTES = 40 * 1024 * 1024
FONTS = ("Calibri", "Arial", "Times New Roman", "Georgia", "Verdana", "Nirmala UI")

_MARK = re.compile(r"(\*\*.+?\*\*|\*[^*\s][^*]*?\*)")


def _runs(text: str) -> list[tuple[str, bool, bool]]:
    """'a **b** *c*' -> [('a ', F, F), ('b', T, F), (' ', F, F), ('c', F, T)]"""
    out = []
    for part in _MARK.split(text):
        if not part:
            continue
        if part.startswith("**") and part.endswith("**") and len(part) > 4:
            out.append((part[2:-2], True, False))
        elif part.startswith("*") and part.endswith("*") and len(part) > 2:
            out.append((part[1:-1], False, True))
        else:
            out.append((part, False, False))
    return out


def decode_image(data: str) -> bytes:
    if "," in data[:80] and data.startswith("data:"):
        data = data.split(",", 1)[1]
    try:
        raw = base64.b64decode(data, validate=False)
    except Exception:
        raise ValueError("An image could not be read.")
    if not raw:
        raise ValueError("An image is empty.")
    if len(raw) > MAX_IMAGE_BYTES:
        raise ValueError("An image is larger than 10 MB.")
    return raw


def _prepare(spec: dict) -> dict:
    """Decode images once and enforce limits, so both writers can trust the blocks."""
    total = 0
    blocks = []
    for b in spec.get("blocks", []):
        b = dict(b)
        if b.get("type") == "image":
            b["raw"] = decode_image(b.get("data", ""))
            total += len(b["raw"])
            if total > MAX_TOTAL_IMAGE_BYTES:
                raise ValueError("The images add up to more than 40 MB.")
        blocks.append(b)
    return {**spec, "blocks": blocks}


# ---------------------------------------------------------------- Word


def _add_runs(par, text: str, size=None, color=None, italic=None):
    from docx.shared import Pt, RGBColor

    for t, bold, ital in _runs(text):
        r = par.add_run(t)
        r.bold = bold or None
        r.italic = (ital or bool(italic)) or None
        if size:
            r.font.size = Pt(size)
        if color:
            r.font.color.rgb = RGBColor.from_string(color)


def _shade(cell, fill: str):
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn

    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill)
    tcPr.append(shd)


def _page_number_footer(section):
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn

    p = section.footer.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run()
    for kind, text in (("begin", None), (None, "PAGE"), ("end", None)):
        if kind:
            el = OxmlElement("w:fldChar")
            el.set(qn("w:fldCharType"), kind)
        else:
            el = OxmlElement("w:instrText")
            el.set(qn("xml:space"), "preserve")
            el.text = text
        run._r.append(el)


_ALIGN = {"left": 0, "center": 1, "right": 2, "justify": 3}


def build_docx(spec: dict) -> bytes:
    import docx
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.oxml.ns import qn
    from docx.shared import Cm, Pt

    spec = _prepare(spec)
    d = docx.Document()
    font = spec.get("font") if spec.get("font") in FONTS else "Calibri"
    normal = d.styles["Normal"]
    normal.font.name = font
    normal.font.size = Pt(spec.get("font_size", 11))
    rpr = normal.element.get_or_add_rPr()
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is not None:
        for attr in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
            rfonts.set(qn(attr), font if attr != "w:cs" else "Nirmala UI")  # Hindi text falls back to a font that has it
    for name in ("Heading 1", "Heading 2", "Heading 3", "Title"):
        d.styles[name].font.name = font

    sec = d.sections[0]
    text_width = sec.page_width - sec.left_margin - sec.right_margin
    d.core_properties.title = spec.get("title", "")
    d.core_properties.author = spec.get("author", "")

    if spec.get("title"):
        d.add_heading(spec["title"], 0)
    meta = " · ".join(x for x in (spec.get("subtitle", ""), spec.get("author", "")) if x)
    if meta:
        _add_runs(d.add_paragraph(), meta, color="666666", italic=True)

    for b in spec["blocks"]:
        kind = b.get("type")
        text = b.get("text", "")
        if kind == "heading":
            _add_runs(d.add_heading("", max(1, min(3, int(b.get("level", 1))))), text)
        elif kind == "paragraph":
            p = d.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH(_ALIGN.get(b.get("align", "left"), 0))
            _add_runs(p, text)
        elif kind == "quote":
            p = d.add_paragraph()
            p.paragraph_format.left_indent = Cm(1)
            p.paragraph_format.right_indent = Cm(1)
            _add_runs(p, text, italic=True, color="444444")
        elif kind == "bullets":
            for it in b.get("items", []):
                _add_runs(d.add_paragraph(style="List Bullet"), it)
        elif kind == "numbered":
            for i, it in enumerate(b.get("items", []), 1):  # numbered by hand so every list starts at 1
                p = d.add_paragraph()
                p.paragraph_format.left_indent = Cm(0.9)
                p.paragraph_format.first_line_indent = Cm(-0.6)
                _add_runs(p, f"{i}. {it}")
        elif kind == "table":
            rows = [list(r) for r in b.get("rows", []) if r]
            if rows:
                cols = max(len(r) for r in rows)
                tbl = d.add_table(rows=len(rows), cols=cols)
                tbl.style = "Table Grid"
                for ri, row in enumerate(rows):
                    for ci in range(cols):
                        cell = tbl.cell(ri, ci)
                        cell.text = ""
                        _add_runs(cell.paragraphs[0], row[ci] if ci < len(row) else "")
                        if ri == 0 and b.get("header", True):
                            for r in cell.paragraphs[0].runs:
                                r.bold = True
                            _shade(cell, "D9E2F3")
                d.add_paragraph()
        elif kind == "image":
            p = d.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH(_ALIGN.get(b.get("align", "center"), 1))
            width = int(text_width * max(10, min(100, int(b.get("width", 80)))) / 100)
            try:
                p.add_run().add_picture(io.BytesIO(b["raw"]), width=width)
            except Exception:
                raise ValueError("An image is not a supported picture (use PNG, JPG, GIF or BMP).")
            if b.get("caption"):
                c = d.add_paragraph()
                c.alignment = WD_ALIGN_PARAGRAPH.CENTER
                _add_runs(c, b["caption"], size=9, color="555555", italic=True)
        elif kind == "pagebreak":
            d.add_page_break()

    if spec.get("page_numbers", True):
        _page_number_footer(sec)
    buf = io.BytesIO()
    d.save(buf)
    return buf.getvalue()


# ---------------------------------------------------------------- PDF


def _pdf_fonts() -> tuple[str, str, str]:
    """(regular, bold, italic) font names. Arial from Windows if available (covers more than Helvetica)."""
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    d = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts")
    files = {"JArial": "arial.ttf", "JArial-B": "arialbd.ttf", "JArial-I": "ariali.ttf", "JArial-BI": "arialbi.ttf"}
    if all(os.path.isfile(os.path.join(d, f)) for f in files.values()):
        for name, f in files.items():
            if name not in pdfmetrics.getRegisteredFontNames():
                pdfmetrics.registerFont(TTFont(name, os.path.join(d, f)))
        from reportlab.pdfbase.pdfmetrics import registerFontFamily

        registerFontFamily("JArial", normal="JArial", bold="JArial-B", italic="JArial-I", boldItalic="JArial-BI")
        return "JArial", "JArial-B", "JArial-I"
    return "Helvetica", "Helvetica-Bold", "Helvetica-Oblique"


def _markup(text: str) -> str:
    from xml.sax.saxutils import escape

    out = []
    for t, bold, ital in _runs(text):
        t = escape(t)
        if bold:
            t = f"<b>{t}</b>"
        if ital:
            t = f"<i>{t}</i>"
        out.append(t)
    return "".join(out).replace("\n", "<br/>")


def build_pdf(spec: dict) -> bytes:
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import Image, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
    from PIL import Image as PILImage

    spec = _prepare(spec)
    everything = " ".join([spec.get("title", ""), spec.get("subtitle", "")] + [
        " ".join([b.get("text", ""), b.get("caption", "")] + list(b.get("items", [])) + [c for r in b.get("rows", []) for c in r])
        for b in spec["blocks"]])
    if _DEVANAGARI.search(everything):
        raise ValueError("Hindi text cannot be written to PDF here. Create the Word file, then use Save as PDF in Word.")

    reg, bold, ital = _pdf_fonts()
    size = spec.get("font_size", 11)
    base = ParagraphStyle("b", fontName=reg, fontSize=size, leading=size * 1.4, spaceAfter=6)
    styles = {
        "title": ParagraphStyle("t", parent=base, fontName=bold, fontSize=size + 13, leading=(size + 13) * 1.2, spaceAfter=4, textColor=colors.HexColor("#1F3864")),
        "h1": ParagraphStyle("h1", parent=base, fontName=bold, fontSize=size + 6, leading=(size + 6) * 1.25, spaceBefore=12, spaceAfter=6, textColor=colors.HexColor("#2F5496")),
        "h2": ParagraphStyle("h2", parent=base, fontName=bold, fontSize=size + 3, leading=(size + 3) * 1.25, spaceBefore=10, spaceAfter=4, textColor=colors.HexColor("#2F5496")),
        "h3": ParagraphStyle("h3", parent=base, fontName=bold, fontSize=size + 1, spaceBefore=8, spaceAfter=3),
        "quote": ParagraphStyle("q", parent=base, fontName=ital, leftIndent=24, rightIndent=24, textColor=colors.HexColor("#444444")),
        "meta": ParagraphStyle("m", parent=base, fontName=ital, textColor=colors.HexColor("#666666")),
        "caption": ParagraphStyle("c", parent=base, fontName=ital, fontSize=size - 2, alignment=TA_CENTER, textColor=colors.HexColor("#555555")),
    }
    align = {"left": TA_LEFT, "center": TA_CENTER, "right": TA_RIGHT, "justify": TA_JUSTIFY}
    margin = 2.2 * cm
    frame_w = A4[0] - 2 * margin
    story: list[Any] = []
    if spec.get("title"):
        story.append(Paragraph(_markup(spec["title"]), styles["title"]))
    meta = " · ".join(x for x in (spec.get("subtitle", ""), spec.get("author", "")) if x)
    if meta:
        story.append(Paragraph(_markup(meta), styles["meta"]))
    if spec.get("title") or meta:
        story.append(Spacer(1, 6))

    for b in spec["blocks"]:
        kind, text = b.get("type"), b.get("text", "")
        if kind == "heading":
            story.append(Paragraph(_markup(text), styles[f"h{max(1, min(3, int(b.get('level', 1))))}"]))
        elif kind == "paragraph":
            story.append(Paragraph(_markup(text), ParagraphStyle("p", parent=base, alignment=align.get(b.get("align", "left"), TA_LEFT))))
        elif kind == "quote":
            story.append(Paragraph(_markup(text), styles["quote"]))
        elif kind in ("bullets", "numbered"):
            for i, it in enumerate(b.get("items", []), 1):
                mark = "&bull;" if kind == "bullets" else f"{i}."
                story.append(Paragraph(f"{mark}&nbsp;&nbsp;{_markup(it)}", ParagraphStyle("li", parent=base, leftIndent=20, firstLineIndent=-14, spaceAfter=3)))
        elif kind == "table":
            rows = [list(r) for r in b.get("rows", []) if r]
            if rows:
                cols = max(len(r) for r in rows)
                cell = ParagraphStyle("cell", parent=base, fontSize=size - 1, leading=(size - 1) * 1.3, spaceAfter=0)
                data = [[Paragraph(_markup(r[c] if c < len(r) else ""), cell) for c in range(cols)] for r in rows]
                tbl = Table(data, colWidths=[frame_w / cols] * cols, repeatRows=1 if b.get("header", True) else 0)
                st = [("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#999999")), ("VALIGN", (0, 0), (-1, -1), "TOP")]
                if b.get("header", True):
                    st.append(("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#D9E2F3")))
                tbl.setStyle(TableStyle(st))
                story += [tbl, Spacer(1, 10)]
        elif kind == "image":
            try:
                w0, h0 = PILImage.open(io.BytesIO(b["raw"])).size
            except Exception:
                raise ValueError("An image is not a supported picture (use PNG, JPG, GIF or BMP).")
            w = frame_w * max(10, min(100, int(b.get("width", 80)))) / 100
            h = w * h0 / w0
            maxh = A4[1] - 2 * margin - 40
            if h > maxh:
                w, h = w * maxh / h, maxh
            img = Image(io.BytesIO(b["raw"]), width=w, height=h)
            img.hAlign = {"left": "LEFT", "right": "RIGHT"}.get(b.get("align", "center"), "CENTER")
            story.append(img)
            if b.get("caption"):
                story.append(Paragraph(_markup(b["caption"]), styles["caption"]))
            story.append(Spacer(1, 8))
        elif kind == "pagebreak":
            story.append(PageBreak())

    numbered = spec.get("page_numbers", True)

    def footer(canvas, doc):
        if numbered:
            canvas.setFont(reg, 9)
            canvas.setFillColor(colors.HexColor("#666666"))
            canvas.drawCentredString(A4[0] / 2, margin / 2, str(doc.page))

    buf = io.BytesIO()
    SimpleDocTemplate(buf, pagesize=A4, leftMargin=margin, rightMargin=margin, topMargin=margin, bottomMargin=margin,
                      title=spec.get("title", ""), author=spec.get("author", "")).build(story or [Spacer(1, 1)], onFirstPage=footer, onLaterPages=footer)
    return buf.getvalue()


def build(spec: dict, fmt: str) -> bytes:
    return build_pdf(spec) if fmt == "pdf" else build_docx(spec)
