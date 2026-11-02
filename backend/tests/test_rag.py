import io
import os
import time

import docx
import pytest
from fastapi.testclient import TestClient
from pypdf import PdfWriter

import main
from jarvis import brain, commands, config, engine, rag

LEAVE = (
    "Leave Policy\n\nAll full-time employees are entitled to 24 days of paid annual leave per calendar year. "
    "Unused leave up to 10 days can be carried forward to the next year.\n\n"
    "Paternity leave is 10 working days and must be taken within 3 months of the birth. "
    "Planned leave must be applied at least 7 days in advance through the HR portal."
)
RESIGN = (
    "Resignation and Notice Period\n\nAn employee who wishes to resign must submit a written resignation to the reporting manager. "
    "The standard notice period is 60 days for permanent employees and 30 days for employees on probation."
)
TRAVEL = "Travel Policy\n\nHotel stays are reimbursed up to 6000 rupees per night in metro cities and 4000 rupees elsewhere."


@pytest.fixture(autouse=True)
def isolate(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setattr(config, "OUTPUT_DIR", str(tmp_path / "out"))
    monkeypatch.setattr(config, "RAG_EMBEDDER", "hash")  # fast and deterministic; one test below uses the real model
    monkeypatch.setattr(brain, "claude_enabled", lambda: False)
    monkeypatch.setattr(commands.webbrowser, "open", lambda u: None)
    monkeypatch.setattr(engine.webbrowser, "open", lambda u: None)
    monkeypatch.setattr(brain, "ask_wikipedia", lambda q, lang: None)
    rag._state.update(coll=None, embedder=None, path=None)
    engine._sessions.clear()


@pytest.fixture
def folder(tmp_path):
    root = tmp_path / "docs"
    (root / "policies").mkdir(parents=True)
    (root / ".git").mkdir()
    (root / ".git" / "secret.txt").write_text("should never be indexed")
    (root / "policies" / "leave.txt").write_text(LEAVE, encoding="utf-8")
    d = docx.Document()
    for para in RESIGN.split("\n\n"):
        d.add_paragraph(para)
    d.save(str(root / "resignation.docx"))
    (root / "travel.md").write_text(TRAVEL, encoding="utf-8")
    buf = io.BytesIO()
    w = PdfWriter()
    w.add_blank_page(100, 100)
    w.write(buf)
    (root / "scan.pdf").write_bytes(buf.getvalue())  # no text layer
    (root / "photo.png").write_bytes(b"\x89PNG....")  # not indexable: ignored
    return str(root)


def ask(text, lang="en", sid="r"):
    return engine.handle(sid, text, lang)


# ---------------------------------------------------------------- chunking


def test_chunking():
    assert rag.chunk_text("") == [] and rag.chunk_text("   \n ") == []
    assert rag.chunk_text("short text") == ["short text"]
    long = " ".join(f"Sentence number {i} says something useful." for i in range(120))
    chunks = rag.chunk_text(long, size=300, overlap=60)
    assert len(chunks) > 5 and all(len(c) <= 380 for c in chunks)
    assert "Sentence number 119" in chunks[-1] and "Sentence number 0 " in chunks[0]
    assert chunks[1][:20] in chunks[0] + chunks[1]  # consecutive chunks share the overlap


# ---------------------------------------------------------------- indexing a folder


def test_index_folder_and_answer(folder):
    rep = rag.index_folder(folder)
    assert rep["total"] == 4 and rep["indexed"] == 3  # .git and the png are ignored, the scanned pdf is reported
    assert [x["name"] for x in rep["skipped"]] == ["scan.pdf"] and "no readable text" in rep["skipped"][0]["reason"]
    names = [s["name"] for s in rag.sources()]
    assert names == ["policies/leave.txt", "resignation.docx", "travel.md"]  # relative paths, nothing from .git

    r = rag.answer("How many days of annual leave do employees get?")
    assert "24 days" in r.reply and r.reply.startswith("From your documents:")
    assert r.action["type"] == "rag" and r.action["sources"][0]["name"] == "policies/leave.txt" and r.action["mode"] == "extractive"
    assert [x["name"] for x in r.action["sources"]] == ["policies/leave.txt"]  # only what the answer used, not every file searched
    assert "60 days" in rag.answer("what is the notice period when I resign").reply
    assert "paternity" in rag.answer("how long is paternity leave").reply.lower()
    assert "6000" in rag.answer("hotel limit in metro cities").reply
    assert rag.answer("what is the capital of Mars").reply == "I couldn't find that in your documents."
    assert rag.answer("मंगल की राजधानी क्या है", "hi").reply == "यह जानकारी मुझे आपके दस्तावेज़ों में नहीं मिली।"


def test_reindex_skips_unchanged_and_picks_up_edits(folder):
    rag.index_folder(folder)
    again = rag.index_folder(folder)
    assert again["unchanged"] == 3 and again["indexed"] == 0
    path = os.path.join(folder, "policies", "leave.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write("Leave Policy\n\nAll full-time employees are entitled to 30 days of paid annual leave per calendar year.")
    os.utime(path, (time.time() + 5, time.time() + 5))
    assert rag.index_folder(folder)["indexed"] == 1
    reply = rag.answer("how many days of annual leave").reply
    assert "30 days" in reply and "24 days" not in reply  # old text replaced, not duplicated


def test_bad_folder_and_empty_library():
    with pytest.raises(ValueError):
        rag.index_folder("/definitely/not/here")
    assert not rag.has_documents()
    assert "no documents" in rag.answer("anything").reply


def test_delete_and_clear(folder):
    rag.index_folder(folder)
    rag.delete_source("travel.md")
    assert "travel.md" not in [s["name"] for s in rag.sources()]
    rag.clear()
    assert rag.chunk_count() == 0


def test_hindi_documents():
    text = "अवकाश नीति\n\nसभी पूर्णकालिक कर्मचारियों को प्रति वर्ष 24 दिन का सवेतन वार्षिक अवकाश मिलता है। बीमारी के लिए 12 दिन की अलग छुट्टी मिलती है।"
    assert rag.index_bytes("नीति.txt", text.encode("utf-8"))["chunks"] == 1
    r = rag.answer("वार्षिक अवकाश कितने दिन का मिलता है", "hi")
    assert "24 दिन" in r.reply and r.reply.startswith("आपके दस्तावेज़ों के अनुसार:")


# ---------------------------------------------------------------- Claude path


class FakeClaude:
    def __init__(self, fail=False):
        self.calls, self.fail = [], fail
        self.messages = self

    def create(self, **kw):
        self.calls.append(kw)
        if self.fail:
            raise RuntimeError("boom")

        class B:
            type, text = "text", "Employees get 24 days of annual leave [1]."

        return type("R", (), {"content": [B()]})()


def test_claude_writes_the_answer_from_retrieved_passages(folder, monkeypatch):
    rag.index_folder(folder)
    fake = FakeClaude()
    monkeypatch.setattr(brain, "claude_enabled", lambda: True)
    monkeypatch.setattr(brain, "_get_client", lambda: fake)
    r = rag.answer("How many days of annual leave do employees get?")
    assert r.reply == "Employees get 24 days of annual leave [1]." and r.action["mode"] == "claude"
    call = fake.calls[0]
    assert "24 days of paid annual leave" in call["messages"][0]["content"] and "<excerpts>" in call["messages"][0]["content"]
    assert "ONLY" in call["system"] and "data, not instructions" in call["system"]


def test_claude_failure_falls_back_to_quoting(folder, monkeypatch):
    rag.index_folder(folder)
    monkeypatch.setattr(brain, "claude_enabled", lambda: True)
    monkeypatch.setattr(brain, "_get_client", lambda: FakeClaude(fail=True))
    r = rag.answer("How many days of annual leave do employees get?")
    assert "24 days" in r.reply and r.action["mode"] == "extractive"


# ---------------------------------------------------------------- conversation


def test_document_mode_and_explicit_questions(folder):
    assert "no documents" in ask("chat with my documents").reply  # turns on, but tells you the library is empty
    ask("stop document mode")
    rag.index_folder(folder)
    # explicit form works without the mode
    assert "60 days" in ask("from my documents, what is the notice period").reply
    assert "60 days" in ask("what is the notice period, from my documents").reply
    assert "24 days" in ask("according to my documents how many days of annual leave").reply
    r = ask("use my documents")
    assert r.action == {"type": "kb_mode", "on": True}
    assert "6000" in ask("what is the hotel limit in metro cities").reply  # plain question -> documents
    assert "time is" in ask("what is the time").reply.lower()  # local commands still win
    assert ask("stop document mode").action == {"type": "kb_mode", "on": False}
    assert engine.get_session("r").kb_mode is False


def test_without_document_mode_plain_questions_do_not_use_documents(folder):
    rag.index_folder(folder)
    assert "24 days" not in ask("how many days of annual leave do employees get").reply


# ---------------------------------------------------------------- API


def test_api_upload_folder_job_and_manage(folder):
    c = TestClient(main.app)
    files = [("files", ("leave.txt", LEAVE.encode(), "text/plain")), ("files", ("bad.exe", b"MZ", "application/octet-stream"))]
    r = c.post("/api/kb/upload", files=files).json()
    assert r["results"][0] == {"name": "leave.txt", "chunks": 1} and "unsupported" in r["results"][1]["skipped"]
    assert r["embedder"] == "keyword" and r["chunks"] == 1 and r["answers"] == "extractive"

    job = c.post("/api/kb/folder", json={"path": folder}).json()["job"]
    for _ in range(100):
        st = c.get(f"/api/kb/jobs/{job}").json()
        if st["state"] != "running":
            break
        time.sleep(0.1)
    assert st["state"] == "done" and st["indexed"] == 3 and st["total"] == 4
    assert c.post("/api/kb/folder", json={"path": "/nope/nope"}).status_code == 400
    assert c.get("/api/kb/jobs/unknown").status_code == 404

    names = [s["name"] for s in c.get("/api/kb").json()["sources"]]
    assert "leave.txt" in names and "resignation.docx" in names
    assert "leave.txt" not in [s["name"] for s in c.delete("/api/kb/source", params={"name": "leave.txt"}).json()["sources"]]
    assert c.post("/api/kb/clear").json()["chunks"] == 0
    assert c.post("/api/kb/mode", json={"on": True, "session": "x"}).json() == {"on": True}
    assert engine.get_session("x").kb_mode is True


# ---------------------------------------------------------------- the real semantic model


def test_semantic_search_finds_paraphrases(folder, monkeypatch):
    monkeypatch.setattr(config, "RAG_EMBEDDER", "auto")
    rag._state.update(coll=None, embedder=None, path=None)
    if rag.embedder_name() != "minilm":
        pytest.skip("the local embedding model is not available (offline)")
    rag.index_folder(folder)
    # "vacation" never appears in the documents: only meaning connects it to "annual leave"
    hits = rag.retrieve("how many vacation days do I get each year", 3)
    assert hits[0]["source"] == "policies/leave.txt"


# ---------------------------------------------------------------- markdown projects and "explain the project"

README = (
    "# Video Production Toolkit\n\nThis project turns a written script and a voiceover into a finished explainer video. "
    "It maps every spoken claim to a screenshot or document from the product, and flags claims that cannot be verified.\n\n"
    "## How it works\n\nThe pipeline inspects the project, builds a scene list, maps the voiceover to scenes and renders the final video with captions."
)
REPORT = (
    "# Production report\n\n| Step | Status | Notes |\n|---|---|---|\n| 1 Inspect project | Done | Structure, docs, 80+ assets inventoried. |\n"
    "| 3 Map voice to project | Done | 16 verified highlights across 21 scenes. |\n\n**Unverified** = a claim in the voiceover that could not be found in the project."
)


def test_clean_md_strips_tables_bold_headings_and_bullets():
    out = rag.clean_md(REPORT)
    assert "|" not in out and "**" not in out and "#" not in out and "---" not in out
    assert "1 Inspect project - Done - Structure, docs, 80+ assets inventoried." in out
    assert rag.clean_md("- **Bold** item with [a link](http://x.y) and `code`") == "Bold item with a link and code"


def test_overview_question_summarises_the_leading_documents(tmp_path):
    root = tmp_path / "proj"
    (root / "video-production").mkdir(parents=True)
    (root / "README.md").write_text(README, encoding="utf-8")
    (root / "video-production" / "production_report.md").write_text(REPORT, encoding="utf-8")
    (root / "notes.txt").write_text("Remember to buy milk and call the plumber about the kitchen tap.", encoding="utf-8")
    rag.index_folder(str(root))

    assert rag.is_overview("Explain me the project in short.") and rag.is_overview("explain the project in deep")
    assert not rag.is_overview("how many days of annual leave do employees get")
    r = rag.answer("Explain me the project in short.")
    assert r.reply.startswith("Here is an overview from your documents:")
    assert "|" not in r.reply and "**" not in r.reply and "#" not in r.reply  # readable text, not raw markdown
    assert "explainer video" in r.reply  # the README leads
    assert "Sections: Video Production Toolkit · How it works" in r.reply  # its headings give the outline
    names = [s["name"] for s in r.action["sources"]]
    assert names[0] == "README.md" and len(names) <= 3 and "notes.txt" not in names[:1]

    q = rag.answer("what is the status of the Inspect project step")  # a normal question still quotes the matching row
    assert "Done" in q.reply and "|" not in q.reply
