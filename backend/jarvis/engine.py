"""Per-session state: pending confirmations, chat history, attachments, fallback chain."""

import re
import urllib.parse
import webbrowser
from dataclasses import dataclass, field
from typing import Callable, Optional

from . import agent, brain, commands, documents, mail, music, rag, settings
from .commands import Result
from .i18n import t

MAX_HISTORY = 10
MAX_ATTACHMENTS = 8

# Free-form requests that should go to Claude instead of the keyword router.
_AGENT_START = re.compile(r"^(create|write|generate|draft|summari[sz]e|translate|convert|analy[sz]e|prepare|build|explain|make me|make a)\b", re.I)


@dataclass
class Session:
    pending: Optional[Callable[[], Result]] = None
    history: list = field(default_factory=list)
    attachments: list = field(default_factory=list)
    mail: Optional[dict] = None  # email being composed (see mail.py)
    kb_mode: bool = False  # every question is answered from the indexed documents (see rag.py)
    music: Optional[dict] = None  # waiting for a music folder or a song choice (see music.py)


_sessions: dict[str, Session] = {}


def get_session(session_id: str) -> Session:
    return _sessions.setdefault(session_id, Session())


def add_attachment(session_id: str, att: documents.Attachment) -> None:
    s = get_session(session_id)
    s.attachments = [a for a in s.attachments if a.name != att.name]
    s.attachments.append(att)
    del s.attachments[:-MAX_ATTACHMENTS]


def remove_attachment(session_id: str, name: str) -> None:
    s = get_session(session_id)
    s.attachments = [a for a in s.attachments if a.name != name]


def _norm(text: str) -> str:
    return re.sub(r"[.!?,।]+$", "", text.strip().lower())


def _trim(history: list) -> None:
    del history[:-MAX_HISTORY]
    # The API requires the conversation to start with a user turn.
    while history and history[0]["role"] != "user":
        history.pop(0)


def _files_action(names: list[str]) -> dict:
    return {
        "type": "files",
        "files": [{"name": n, "url": "/api/files/" + urllib.parse.quote(n)} for n in names],
    }


def _fallback(s: Session, text: str, lang: str) -> Result:
    if brain.claude_enabled():
        try:
            reply, created = agent.run(list(s.history), text, s.attachments, lang)
            if reply:
                s.history += [{"role": "user", "content": text}, {"role": "assistant", "content": reply}]
                _trim(s.history)
                return Result(reply, _files_action(created) if created else {"type": "ai"})
        except Exception as e:
            print(f"[agent] Claude failed: {e}")
            return Result(t(lang, "ai_error", err=str(e)[:200]))
    elif s.attachments:
        return Result(t(lang, "attachment_help"))
    elif _AGENT_START.match(text.strip()):
        return Result(t(lang, "need_claude"))
    try:
        summary = brain.ask_wikipedia(text, lang)
        if summary:
            return Result(t(lang, "wiki", text=summary), {"type": "wiki"})
    except Exception as e:
        print(f"[brain] Wikipedia failed: {e}")
    url = "https://www.google.com/search?q=" + urllib.parse.quote_plus(text)
    webbrowser.open(url)
    return Result(t(lang, "google"), {"type": "opened", "name": "Google", "url": url})


def handle(session_id: str, text: str, lang: str) -> Result:
    lang = lang if lang in ("en", "hi") else "en"
    s = get_session(session_id)

    # "Hey Jarvis, ..." / "... Jarvis": the wake word is not part of the command.
    woke, rest = settings.split_wake(text)
    if woke:
        text = rest
        if not text:
            return Result(t(lang, "wake_yes"))

    if s.pending is not None:
        said = _norm(text)
        pending, s.pending = s.pending, None
        if any(w in said for w in t(lang, "yes")):
            return pending()
        if any(w in said for w in t(lang, "no")):
            return Result(t(lang, "cancelled"))
        # Anything else: drop the confirmation and treat it as a new command.

    try:
        result = mail.handle(s, text, lang) or music.handle(s, text, lang) or rag.handle(s, text, lang)
        if result is None and s.kb_mode and rag.has_documents():
            # Document mode: local commands still work ("open youtube", "time"), everything else is a question.
            result = commands.route(text, lang, s.attachments) or rag.answer(text, lang)
        free_form = brain.claude_enabled() and (
            bool(s.attachments) or len(text.split()) > 6 or bool(_AGENT_START.match(text.strip()))
        )
        if result is None and not free_form:
            result = commands.route(text, lang, s.attachments)
        if result is None:
            result = _fallback(s, text, lang)
    except Exception as e:
        return Result(t(lang, "error", err=str(e)))

    if result.on_confirm:
        s.pending = result.on_confirm
    return result
