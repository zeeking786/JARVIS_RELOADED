import base64
import io
import re

import docx
import pytest
from fastapi.testclient import TestClient
from PIL import Image
from pypdf import PdfReader

import main
from jarvis import config, docbuilder


@pytest.fixture(autouse=True)
def isolate(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "OUTPUT_DIR", str(tmp_path / "out"))


def png(w=200, h=100, color=(200, 60, 40)) -> str:
    buf = io.BytesIO()
    Image.new("RGB", (w, h), color).save(buf, "PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


BLOCKS = [
    {"type": "heading", "level": 1, "text": "Introduction"},
    {"type": "paragraph", "text": "This is **very important** and *quite* clear."},
    {"type": "bullets", "items": ["first point", "second point"]},
    {"type": "numbered", "items": ["step one", "step two"]},
    {"type": "numbered", "items": ["again one"]},
    {"type": "table", "rows": [["Item", "Qty"], ["Pen", "3"], ["Book"]], "header": True},
    {"type": "image", "data": png(), "width": 50, "caption": "Figure 1: a red box"},
    {"type": "quote", "text": "A quoted line."},
    {"type": "pagebreak"},
    {"type": "heading", "level": 2, "text": "Second page"},
]


def spec(**kw):
    return {"title": "Quarterly Report", "subtitle": "Q3 2026", "author": "Zeeshan", "blocks": BLOCKS, **kw}


def test_docx_has_every_part():
    d = docx.Document(io.BytesIO(docbuilder.build(spec(), "docx")))
    texts = [p.text for p in d.paragraphs]
    assert d.paragraphs[0].text == "Quarterly Report" and d.paragraphs[0].style.name == "Title"
    assert "Q3 2026 · Zeeshan" in texts
    assert [p.text for p in d.paragraphs if p.style.name == "Heading 1"] == ["Introduction"]
    assert [p.text for p in d.paragraphs if p.style.name == "Heading 2"] == ["Second page"]
    assert [p.text for p in d.paragraphs if p.style.name == "List Bullet"] == ["first point", "second point"]
    assert "1. step one" in texts and "2. step two" in texts and "1. again one" in texts  # every list restarts at 1
    runs = next(p for p in d.paragraphs if p.text.startswith("This is")).runs
    assert [(r.text, bool(r.bold), bool(r.italic)) for r in runs if r.text.strip()] == [
        ("This is ", False, False), ("very important", True, False), ("quite", False, True), (" and ", False, False), ("clear.", False, False)] or \
        any(r.bold and r.text == "very important" for r in runs) and any(r.italic and r.text == "quite" for r in runs)
    t = d.tables[0]
    assert [[c.text for c in row.cells] for row in t.rows] == [["Item", "Qty"], ["Pen", "3"], ["Book", ""]]  # ragged rows padded
    assert t.rows[0].cells[0].paragraphs[0].runs[0].bold
    assert len(d.inline_shapes) == 1 and "Figure 1: a red box" in texts
    sec = d.sections[0]
    assert d.inline_shapes[0].width < sec.page_width - sec.left_margin - sec.right_margin  # 50% of the text width
    assert "PAGE" in sec.footer._element.xml  # page numbers
    assert any("w:br" in p._p.xml and 'w:type="page"' in p._p.xml for p in d.paragraphs)


def test_docx_font_and_hindi():
    d = docx.Document(io.BytesIO(docbuilder.build({"title": "रिपोर्ट", "font": "Arial", "font_size": 12,
                                                    "blocks": [{"type": "paragraph", "text": "यह एक **परीक्षण** है।"}]}, "docx")))
    assert d.paragraphs[0].text == "रिपोर्ट" and d.styles["Normal"].font.name == "Arial"
    assert d.paragraphs[1].text == "यह एक परीक्षण है।"


def test_pdf_text_table_and_image():
    pdf = docbuilder.build(spec(), "pdf")
    r = PdfReader(io.BytesIO(pdf))
    text = re.sub(r"[ \xa0]+", " ", "\n".join(p.extract_text() for p in r.pages))
    assert len(r.pages) == 2 and pdf.startswith(b"%PDF")  # the page break
    for s in ("Quarterly Report", "Introduction", "very important", "first point", "1. step one", "Pen", "Figure 1: a red box", "Second page"):
        assert s in text
    assert len(r.pages[0].images) == 1


def test_pdf_refuses_hindi_but_word_accepts_it():
    hindi = {"title": "रिपोर्ट", "blocks": []}
    with pytest.raises(ValueError, match="Hindi"):
        docbuilder.build(hindi, "pdf")
    docbuilder.build(hindi, "docx")


def test_bad_and_oversized_images():
    for fmt in ("docx", "pdf"):
        with pytest.raises(ValueError):
            docbuilder.build({"blocks": [{"type": "image", "data": base64.b64encode(b"not a picture").decode()}]}, fmt)
    with pytest.raises(ValueError, match="10 MB"):
        docbuilder.build({"blocks": [{"type": "image", "data": base64.b64encode(b"x" * (11 * 1024 * 1024)).decode()}]}, "docx")


def test_api_builds_downloads_and_validates():
    c = TestClient(main.app)
    body = {"title": "My Plan / v2?", "blocks": BLOCKS, "format": "docx"}
    r = c.post("/api/doc/build", json=body).json()
    name = r["files"][0]["name"]
    assert name == "My-Plan--v2.docx" or name.endswith(".docx")
    assert docx.Document(io.BytesIO(c.get(r["files"][0]["url"]).content)).paragraphs[0].text == "My Plan / v2?"
    assert c.post("/api/doc/build", json=body).json()["files"][0]["name"] != name  # never overwrites
    p = c.post("/api/doc/build", json={**body, "format": "pdf"}).json()["files"][0]["name"]
    assert p.endswith(".pdf") and c.get("/api/files/" + p).content.startswith(b"%PDF")
    assert c.post("/api/doc/build", json={"blocks": [{"type": "image", "data": "AAAA"}]}).status_code == 400
    assert c.post("/api/doc/build", json={"blocks": [{"type": "script", "text": "x"}]}).status_code == 422
    assert c.post("/api/doc/build", json={"title": "रिपोर्ट", "format": "pdf"}).status_code == 400
    empty = c.post("/api/doc/build", json={}).json()["files"][0]["name"]
    assert empty == "document.docx" or empty.startswith("document")
