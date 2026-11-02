"""Jarvis API. Run:  uvicorn main:app --host 127.0.0.1 --port 8000"""

import os
import urllib.parse

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from typing import Literal

from pydantic import BaseModel, Field

from jarvis import brain, config, docbuilder, documents, engine, mail, rag, settings, templates
from jarvis.i18n import t

app = FastAPI(title="Jarvis")
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.ALLOWED_ORIGINS,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Content-Type"],
)


class CommandIn(BaseModel):
    text: str = Field(min_length=1, max_length=20000)
    lang: str = "en"
    session: str = Field(default="default", max_length=64)


class EmailIn(BaseModel):
    to: str = Field(min_length=3, max_length=254)
    subject: str = Field(default="", max_length=300)
    body: str = Field(default="", max_length=20000)
    lang: str = "en"


@app.get("/api/health")
def health():
    return {
        "ok": True,
        "brain": "claude" if brain.claude_enabled() else "offline",
        "model": config.JARVIS_MODEL if brain.claude_enabled() else None,
        "email": bool(config.SMTP_USER and config.SMTP_PASSWORD),
        "name": settings.get_name(),
    }


class NameIn(BaseModel):
    name: str = Field(min_length=1, max_length=40)


@app.post("/api/name")
def rename(body: NameIn):
    try:
        return {"name": settings.set_name(body.name)}
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.post("/api/command")
def command(body: CommandIn):
    r = engine.handle(body.session, body.text, body.lang)
    m = engine.get_session(body.session).mail
    # Subject and message are dictated: the microphone should wait longer for pauses.
    return {"reply": r.reply, "action": r.action, "needs_confirm": r.on_confirm is not None,
            "dictate": bool(m and m.get("ask") in ("subject", "body"))}


class MailSendIn(BaseModel):
    to: list[str] = Field(default_factory=list, max_length=20)
    cc: list[str] = Field(default_factory=list, max_length=20)
    bcc: list[str] = Field(default_factory=list, max_length=20)
    subject: str = Field(default="", max_length=300)
    body: str = Field(default="", max_length=20000)
    lang: str = "en"
    session: str = Field(default="default", max_length=64)


@app.post("/api/mail/send")
def mail_send(body: MailSendIn):
    """Used by the editable draft card. Clears the voice confirmation so a later "yes" cannot send twice."""
    s = engine.get_session(body.session)
    s.pending, s.mail = None, None
    try:
        return mail.send_edited(body.to, body.cc, body.bcc, body.subject, body.body, body.lang)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(502, t(body.lang, "email_fail", err=str(e)[:200]))


@app.post("/api/upload")
async def upload(file: UploadFile = File(...), session: str = Form("default", max_length=64), lang: str = Form("en")):
    data = await file.read(documents.MAX_UPLOAD_BYTES + 1)
    try:
        att = documents.load(file.filename or "file", data)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:  # corrupt docx/xlsx/pptx
        raise HTTPException(400, f"Could not read this file: {e}")
    engine.add_attachment(session, att)
    return {"name": att.name, "kind": att.kind, "size": att.size, "truncated": att.truncated,
            "reply": t(lang, "uploaded", name=att.name)}


@app.delete("/api/attachments/{name}")
def remove_attachment(name: str, session: str = "default"):
    engine.remove_attachment(session, name)
    return {"ok": True}


@app.get("/api/files/{name}")
def download(name: str):
    safe = documents.safe_name(name)
    path = os.path.join(config.OUTPUT_DIR, safe)
    if safe != name or not os.path.isfile(path):
        raise HTTPException(404, "File not found")
    return FileResponse(path, filename=safe)


class MakeIn(BaseModel):
    template: str = Field(max_length=32)
    values: dict[str, str] = Field(default_factory=dict)
    lang: str = "en"


@app.post("/api/make")
def make(body: MakeIn):
    """Build a file from a template form (no AI involved)."""
    lang = body.lang if body.lang in ("en", "hi") else "en"
    try:
        filename, content = templates.build(body.template, body.values, lang)
        name = documents.save_generated(filename, content)
    except ValueError as e:
        raise HTTPException(400, str(e))
    return {"reply": t(lang, "made", name=name), "files": [{"name": name, "url": "/api/files/" + urllib.parse.quote(name)}]}


@app.post("/api/email")
def send_email(body: EmailIn):
    if not (config.SMTP_USER and config.SMTP_PASSWORD):
        raise HTTPException(400, "Email is not configured. Set SMTP_USER and SMTP_PASSWORD in backend/.env")
    try:
        mail.send_smtp([body.to], [], [], body.subject, body.body)
    except Exception as e:
        raise HTTPException(502, t(body.lang, "email_fail", err=str(e)))
    return {"reply": t(body.lang, "email_sent")}


# ---------------------------------------------------------------- documents (RAG)


def _kb_state() -> dict:
    return {"embedder": rag.embedder_name(), "chunks": rag.chunk_count(), "sources": rag.sources(),
            "answers": "claude" if brain.claude_enabled() else "extractive"}


@app.get("/api/kb")
def kb_info():
    return _kb_state()


@app.post("/api/kb/upload")
def kb_upload(files: list[UploadFile] = File(...)):
    results = []
    for f in files[:50]:
        data = f.file.read(documents.MAX_UPLOAD_BYTES + 1)
        results.append(rag.index_bytes(f.filename or "file", data))
    return {"results": results, **_kb_state()}


class FolderIn(BaseModel):
    path: str = Field(min_length=1, max_length=1000)


@app.post("/api/kb/folder")
def kb_folder(body: FolderIn):
    try:
        return {"job": rag.start_folder_job(body.path)}
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.get("/api/kb/jobs/{job_id}")
def kb_job(job_id: str):
    job = rag.job_status(job_id)
    if job is None:
        raise HTTPException(404, "Unknown job")
    return job


@app.delete("/api/kb/source")
def kb_delete(name: str):
    rag.delete_source(name)
    return _kb_state()


@app.post("/api/kb/clear")
def kb_clear():
    rag.clear()
    return _kb_state()


class ModeIn(BaseModel):
    on: bool
    session: str = Field(default="default", max_length=64)


@app.post("/api/kb/mode")
def kb_mode(body: ModeIn):
    engine.get_session(body.session).kb_mode = body.on
    return {"on": body.on}


# ---------------------------------------------------------------- document studio


class DocBlock(BaseModel):
    type: Literal["heading", "paragraph", "quote", "bullets", "numbered", "table", "image", "pagebreak"]
    text: str = Field(default="", max_length=50000)
    level: int = Field(default=1, ge=1, le=3)
    items: list[str] = Field(default_factory=list, max_length=300)
    rows: list[list[str]] = Field(default_factory=list, max_length=300)
    header: bool = True
    data: str = Field(default="", max_length=16_000_000)  # base64 image
    width: int = Field(default=80, ge=10, le=100)
    caption: str = Field(default="", max_length=500)
    align: Literal["left", "center", "right", "justify"] = "left"


class DocIn(BaseModel):
    title: str = Field(default="", max_length=200)
    subtitle: str = Field(default="", max_length=200)
    author: str = Field(default="", max_length=100)
    font: str = "Calibri"
    font_size: int = Field(default=11, ge=8, le=20)
    page_numbers: bool = True
    format: Literal["docx", "pdf"] = "docx"
    blocks: list[DocBlock] = Field(default_factory=list, max_length=600)
    lang: str = "en"


@app.post("/api/doc/build")
def doc_build(body: DocIn):
    """Turn the studio's blocks into a downloadable Word or PDF file (no AI involved)."""
    lang = body.lang if body.lang in ("en", "hi") else "en"
    spec = body.model_dump()
    try:
        data = docbuilder.build(spec, body.format)
    except ValueError as e:
        raise HTTPException(400, str(e))
    slug = "".join(c if c.isalnum() or c in " -_" else "" for c in (body.title or "document")).strip().replace(" ", "-")[:60] or "document"
    name = documents.save_bytes(f"{slug}.{body.format}", data)
    return {"reply": t(lang, "made", name=name), "files": [{"name": name, "url": "/api/files/" + urllib.parse.quote(name)}]}
