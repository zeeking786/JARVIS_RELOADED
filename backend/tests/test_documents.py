import io
from types import SimpleNamespace as NS

import docx
import openpyxl
import pytest
from fastapi.testclient import TestClient

import main
from jarvis import agent, brain, config, documents, engine


@pytest.fixture(autouse=True)
def isolate(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "OUTPUT_DIR", str(tmp_path / "out"))
    engine._sessions.clear()


def make_docx(text):
    d = docx.Document()
    d.add_paragraph(text)
    buf = io.BytesIO()
    d.save(buf)
    return buf.getvalue()


def test_load_formats():
    assert documents.load("a.txt", "नमस्ते".encode()).text == "नमस्ते"
    assert "hello docx" in documents.load("a.docx", make_docx("hello docx")).text
    wb = openpyxl.Workbook()
    wb.active.append(["x", 1])
    buf = io.BytesIO()
    wb.save(buf)
    assert "x\t1" in documents.load("b.xlsx", buf.getvalue()).text
    assert documents.load("c.pdf", b"%PDF-1.4").kind == "pdf"
    with pytest.raises(ValueError):
        documents.load("evil.exe", b"MZ")
    with pytest.raises(ValueError):
        documents.load("big.txt", b"x" * (documents.MAX_UPLOAD_BYTES + 1))


def test_save_generated_formats_and_safe_names():
    name = documents.save_generated("../../Plan.docx", "# Title\n- one\n1. two\n**bold** text")
    assert name == "Plan.docx"
    d = docx.Document(f"{config.OUTPUT_DIR}/{name}")
    assert [p.text for p in d.paragraphs][0] == "Title"
    assert documents.save_generated("Plan.docx", "x") == "Plan (2).docx"
    assert documents.save_generated("t.xlsx", "a,b\n1,2\n=SUM(A1)").endswith("xlsx")
    assert documents.save_generated("s.pptx", "# One\n- a\n# Two\n- b") == "s.pptx"
    assert documents.save_generated("x.exe", "hi") == "x.txt"


class FakeClient:
    """Claude asks to create a file, then replies."""

    def __init__(self):
        self.calls = []
        self.messages = self

    def create(self, **kw):
        self.calls.append(kw)
        if len(self.calls) == 1:
            tool = NS(type="tool_use", id="t1", name="create_file", input={"filename": "letter.docx", "content": "# Hi\nBody"})
            return NS(stop_reason="tool_use", content=[tool])
        return NS(stop_reason="end_turn", content=[NS(type="text", text="I made your letter.")])


def test_agent_creates_file_and_download(monkeypatch):
    fake = FakeClient()
    monkeypatch.setattr(brain, "claude_enabled", lambda: True)
    monkeypatch.setattr(brain, "_get_client", lambda: fake)
    c = TestClient(main.app)

    r = c.post("/api/upload", files={"file": ("notes.txt", b"project alpha")}, data={"session": "s1"})
    assert r.status_code == 200 and r.json()["name"] == "notes.txt"

    r = c.post("/api/command", json={"text": "write a formal letter using my notes", "session": "s1"}).json()
    assert r["reply"] == "I made your letter."
    assert r["action"]["files"][0]["name"] == "letter.docx"
    first = fake.calls[0]
    assert first["model"] == config.JARVIS_AGENT_MODEL
    assert "project alpha" in first["messages"][0]["content"][0]["text"]

    got = c.get(r["action"]["files"][0]["url"])
    assert got.status_code == 200 and got.content[:2] == b"PK"
    assert c.get("/api/files/..%2Fmain.py").status_code == 404


def test_without_claude_key_is_honest(monkeypatch):
    monkeypatch.setattr(brain, "claude_enabled", lambda: False)
    r = engine.handle("s2", "write me a report on solar power", "en")
    assert "without AI" in r.reply
    c = TestClient(main.app)
    assert c.post("/api/upload", files={"file": ("a.exe", b"MZ")}, data={"session": "s2"}).status_code == 400


def test_short_commands_still_local_with_claude(monkeypatch):
    monkeypatch.setattr(brain, "claude_enabled", lambda: True)
    monkeypatch.setattr(agent, "run", lambda *a, **k: pytest.fail("agent should not run"))
    assert "time" in engine.handle("s3", "what is the time", "en").reply.lower()
