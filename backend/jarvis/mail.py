"""Spoken email, step by step: who -> (which one?) -> CC -> BCC -> subject -> message -> confirm -> send.

Everything is parsed locally (no AI). Any sentence can pre-fill steps ("email Ravi saying I will be late"),
and Jarvis only asks for what is still missing. Every address it hears is saved to data/contacts.json, so
next time a name (or part of an address) is enough; if several saved addresses match, you pick by number.
Sending uses SMTP when configured, otherwise a pre-filled Gmail compose window opens.
"""

import json
import os
import re
import smtplib
import threading
import urllib.parse
import webbrowser
from email.message import EmailMessage
from typing import Optional

from . import config
from .commands import Result
from .i18n import t

_lock = threading.Lock()
_DEVANAGARI = re.compile(r"[ऀ-ॿ]")
_EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")

_TRIGGER_EN = re.compile(
    r"\b(?:send|write|compose|draft|shoot)\s+(?:an?\s+|the\s+|him\s+|her\s+|them\s+)?(?:e-?mail|mail)\b|^\s*(?:e-?mail|mail)\b(?=\s+\S)",
    re.I,
)
_CANCEL = re.compile(r"^\W*(cancel|stop|never ?mind|forget it|discard|रद्द|छोड़ो|छोड़ दो|रहने दो|कैंसिल)\W*$", re.I)
_SKIP = re.compile(r"^\W*(skip|none|nothing|no|nope|no cc|no bcc|not now|स्किप|नहीं|कोई नहीं|नहीं चाहिए)\W*$", re.I)
_NUMBERS = {
    "one": 1, "first": 1, "1st": 1, "two": 2, "second": 2, "2nd": 2, "to": 2, "too": 2, "three": 3, "third": 3, "3rd": 3,
    "four": 4, "fourth": 4, "for": 4, "five": 5, "fifth": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9,
    "एक": 1, "पहला": 1, "पहली": 1, "दो": 2, "दूसरा": 2, "दूसरी": 2, "तीन": 3, "तीसरा": 3, "तीसरी": 3, "चार": 4, "चौथा": 4,
    "पाँच": 5, "पांच": 5,
}


# ---------------------------------------------------------------- contacts
# One file (data/contacts.json): a list of {"name": "...", "email": "..."}. Every address Jarvis
# hears is remembered; the name is optional and is searched together with the address.


def _contacts_path() -> str:
    os.makedirs(config.DATA_DIR, exist_ok=True)
    return os.path.join(config.DATA_DIR, "contacts.json")


def load_contacts() -> list[dict]:
    try:
        with open(_contacts_path(), encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        return []
    if isinstance(data, dict):  # older format: {name: email}
        return [{"name": k, "email": v} for k, v in data.items()]
    return [c for c in data if isinstance(c, dict) and c.get("email")] if isinstance(data, list) else []


def remember(email: str, name: str = "") -> None:
    """Save an address (and the name it goes by, if any). Never duplicates an address."""
    email, name = email.strip().lower(), name.strip().lower()
    with _lock:
        book = load_contacts()
        for c in book:
            if c["email"] == email:
                if name and not c.get("name"):
                    c["name"] = name
                break
        else:
            book.append({"name": name, "email": email})
        with open(_contacts_path(), "w", encoding="utf-8") as f:
            json.dump(book, f, ensure_ascii=False, indent=1)


def search(query: str) -> list[dict]:
    """Contacts whose name or address contains the query. An exact name match wins outright."""
    q = query.strip().lower()
    if not q:
        return []
    book = load_contacts()
    hits = [c for c in book if c.get("name") == q] or [c for c in book if q in c.get("name", "") or q in c["email"]]
    seen, out = set(), []
    for c in hits:
        if c["email"] not in seen:
            seen.add(c["email"])
            out.append(c)
    return out


# ---------------------------------------------------------------- parsing helpers


def normalize_spoken(s: str) -> str:
    """'ravi at gmail dot com' -> 'ravi@gmail.com' (English and Hindi speech)."""
    s = re.sub(r"\s*(?:at the rate(?: of)?|at sign|एट द रेट|एट दी रेट)\s*", "@", s, flags=re.I)
    domain = r"(?=[\w-]+(?:\.[a-z]{2,}\b|\s+(?:dot|डॉट|डाट)\s+[a-z]{2,}))"
    s = re.sub(r"\s+at\s+(?:that|the|d)\s+" + domain, "@", s, flags=re.I)  # heard "at that finance.com"
    s = re.sub(r"\s+at\s+" + domain, "@", s, flags=re.I)
    s = re.sub(r"\s+(?:at|एट)\s+(?=\S+\s+(?:dot|डॉट|डाट)\s+)", "@", s, flags=re.I)
    s = re.sub(r"\s+(?:dot|डॉट|डाट)\s+", ".", s, flags=re.I)
    if "@" in s:
        s = re.sub(r"\s*([@.])\s*", r"\1", s)
    return s


def find_email(s: str) -> str:
    m = _EMAIL.search(normalize_spoken(s))
    return m.group(0).lower() if m else ""


def _entry(token: str) -> dict:
    """A recipient: an address (saved on the spot), or a name looked up in the contacts file."""
    token = token.strip(" .,;:")
    addr = find_email(token)
    if addr:
        remember(addr)
        return {"name": "", "email": addr, "cands": []}
    hits = search(token)
    base = {"name": token.title(), "email": "", "cands": []}
    if len(hits) == 1:
        return {**base, "name": (hits[0].get("name") or "").title() or token.title(), "email": hits[0]["email"]}
    return {**base, "cands": hits}


def _entries(s: str) -> list[dict]:
    s = normalize_spoken(s)
    parts = re.split(r"\s*(?:,|&|\band\b|(?<!\S)और(?!\S))\s*", s)
    return [_entry(p) for p in parts if p.strip(" .,;:") and not re.fullmatch(r"(?:to|with|for)", p.strip().lower())]


def _parse_en(text: str) -> dict:
    text = normalize_spoken(text)
    m = _TRIGGER_EN.search(text)
    rest = text[m.end():].strip() if m else text.strip()
    rest = re.sub(r"^(?:to|for)\s+", "", rest, flags=re.I)
    body = ""
    bm = re.search(r"\b(?:saying|says|body|message|telling (?:him|her|them)|tell (?:him|her|them)|(?<!\bat\s)that(?!\s+[\w-]+\.[a-z]{2,}))\b[:,]?\s*(.*)$", rest, re.I | re.S)
    if bm:
        body, rest = bm.group(1).strip(), rest[: bm.start()]
    fields = {"subject": "", "bcc": "", "cc": ""}
    for key, pat in (
        ("subject", r"\b(?:subject|about|regarding)\b[:,]?\s*(.+?)(?=\s+\b(?:cc|bcc)\b|$)"),
        ("bcc", r"\bbcc\b[:,]?\s*(.+?)(?=\s+\bcc\b|\s+\bsubject\b|$)"),
        ("cc", r"\bcc\b[:,]?\s*(.+?)(?=\s+\bbcc\b|\s+\bsubject\b|$)"),
    ):
        sm = re.search(pat, rest, re.I)
        if sm:
            fields[key] = sm.group(1).strip()
            rest = rest[: sm.start()] + " " + rest[sm.end():]
    rest = re.sub(r"\b(?:with|and)\s*$", "", rest.strip(), flags=re.I).strip()
    return {"to": rest, "cc": fields["cc"], "bcc": fields["bcc"], "subject": fields["subject"], "body": body}


def _parse_hi(text: str) -> dict:
    text = normalize_spoken(text)
    body = ""
    bm = re.search(r"(?:(?<!\S)कि(?!\S)|लिखो|लिखें|बोलो|कहो)\s*(.*)$", text, re.S)
    if bm and bm.group(1).strip():
        body, text = bm.group(1).strip(), text[: bm.start()]
    to = ""
    tm = re.search(r"(\S+(?:\s+(?:और|,)\s+\S+)*)\s+को(?!\S)", text)
    if tm:
        to = tm.group(1)
    return {"to": to, "cc": "", "bcc": "", "subject": "", "body": body}


def _wants_mail(text: str) -> bool:
    if _DEVANAGARI.search(text):
        return bool(re.search(r"(ईमेल|मेल|email|mail)", text, re.I) and re.search(r"(भेज|लिख|कर\s?दो|करो)", text))
    return bool(_TRIGGER_EN.search(text))


def _number(text: str) -> Optional[int]:
    for w in re.findall(r"[\wऀ-ॿ]+", text.lower()):
        if w.isdigit():
            return int(w)
        if w in _NUMBERS:
            return _NUMBERS[w]
    return None


# ---------------------------------------------------------------- draft building


def _auto_subject(body: str) -> str:
    words = re.sub(r"\s+", " ", body).strip().split(" ")
    s = " ".join(words[:10]).strip(" .,;:!?")
    return s[:1].upper() + s[1:]


def _polish(body: str, to: list[dict], lang: str) -> str:
    body = body.strip()
    body = body[:1].upper() + body[1:]
    if body and body[-1].isalnum():
        body += "."
    out = body
    if len(to) == 1 and to[0]["name"]:
        out = f"{t(lang, 'mail_hi', name=to[0]['name'].split()[0])}\n\n{out}"
    if config.SENDER_NAME:
        out += f"\n\n{t(lang, 'mail_regards')}\n{config.SENDER_NAME}"
    return out


def _label(e: dict) -> str:
    return f"{e['name']} <{e['email']}>" if e["name"] else e["email"]


def gmail_url(d: dict) -> str:
    q = {"view": "cm", "fs": "1", "to": ",".join(e["email"] for e in d["to"]), "su": d["subject"], "body": d["body"]}
    if d["cc"]:
        q["cc"] = ",".join(e["email"] for e in d["cc"])
    if d["bcc"]:
        q["bcc"] = ",".join(e["email"] for e in d["bcc"])
    return "https://mail.google.com/mail/?" + urllib.parse.urlencode(q, quote_via=urllib.parse.quote)


def smtp_ready() -> bool:
    return bool(config.SMTP_USER and config.SMTP_PASSWORD)


def send_smtp(to: list[str], cc: list[str], bcc: list[str], subject: str, body: str) -> None:
    msg = EmailMessage()
    msg["From"], msg["To"], msg["Subject"] = config.SMTP_USER, ", ".join(to), subject
    if cc:
        msg["Cc"] = ", ".join(cc)
    msg.set_content(body)
    with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT, timeout=15) as s:
        s.starttls()
        s.login(config.SMTP_USER, config.SMTP_PASSWORD)
        s.send_message(msg, to_addrs=to + cc + bcc)


def _deliver(d: dict, lang: str) -> Result:
    if smtp_ready():
        try:
            send_smtp([e["email"] for e in d["to"]], [e["email"] for e in d["cc"]], [e["email"] for e in d["bcc"]], d["subject"], d["body"])
        except Exception as e:
            return Result(t(lang, "email_fail", err=str(e)[:200]))
        return Result(t(lang, "email_sent"))
    url = gmail_url(d)
    webbrowser.open(url)
    return Result(t(lang, "mail_opened"), {"type": "opened", "name": "Gmail", "url": url})


def send_edited(to: list[str], cc: list[str], bcc: list[str], subject: str, body: str, lang: str) -> dict:
    """Send (or open in Gmail) a draft after the user edited it by hand in the UI."""
    def clean(items: list[str]) -> list[str]:
        out = []
        for raw in items:
            for piece in re.split(r"[,;\n]+", raw):
                if piece.strip():
                    addr = find_email(piece)
                    if not addr:
                        raise ValueError(t(lang, "mail_bad_addr"))
                    if addr not in out:
                        out.append(addr)
        return out

    to, cc, bcc = clean(to), clean(cc), clean(bcc)
    if not to:
        raise ValueError(t(lang, "mail_ask_to"))
    for addr in to + cc + bcc:
        remember(addr)
    if smtp_ready():
        send_smtp(to, cc, bcc, subject, body)
        return {"reply": t(lang, "email_sent"), "url": None}
    d = {"to": [{"email": a} for a in to], "cc": [{"email": a} for a in cc], "bcc": [{"email": a} for a in bcc], "subject": subject, "body": body}
    return {"reply": t(lang, "mail_opened"), "url": gmail_url(d)}


# ---------------------------------------------------------------- conversation


def _quick(*pairs: tuple[str, str]) -> dict:
    """Tappable answers shown under the chat (the UI sends `send` as if it were typed)."""
    return {"type": "reply_options", "options": [{"label": a, "send": b} for a, b in pairs]}


def _pick_options(cands: list[dict]) -> dict:
    return _quick(*[(f"{i}  {c['email']}", str(i)) for i, c in enumerate(cands, 1)])


def _next(s, lang: str) -> Result:
    m = s.mail
    if not m["to"]:
        m["ask"] = "to"
        return Result(t(lang, "mail_ask_to"))
    # Settle every recipient first: several matches -> pick one; no match -> ask for the address.
    for key in ("to", "cc", "bcc"):
        for e in m[key] or []:
            if e["email"]:
                continue
            m["pick"] = e
            if len(e["cands"]) > 1:
                m["ask"] = "pick"
                lines = "; ".join(f"{i}. {c['email']}" for i, c in enumerate(e["cands"], 1))
                return Result(t(lang, "mail_pick", name=e["name"], n=len(e["cands"]), list=lines), _pick_options(e["cands"]))
            m["ask"] = "addr"
            return Result(t(lang, "mail_ask_addr", name=e["name"]))
    skip = _quick((t(lang, "mail_skip"), "skip"))
    for key, prompt in (("cc", "mail_ask_cc"), ("bcc", "mail_ask_bcc"), ("subject", "mail_ask_subject")):
        if m[key] is None:
            m["ask"] = key
            return Result(t(lang, prompt), skip)
    if not m["body"]:
        m["ask"] = "body"
        return Result(t(lang, "mail_ask_body", name=m["to"][0]["name"] or m["to"][0]["email"]))

    s.mail = None
    d = {
        "to": m["to"], "cc": m["cc"], "bcc": m["bcc"],
        "subject": m["subject"] or _auto_subject(m["body"]),
        "body": _polish(m["body"], m["to"], lang),
    }
    shown = {"to": [_label(e) for e in d["to"]], "cc": [_label(e) for e in d["cc"]], "bcc": [_label(e) for e in d["bcc"]],
             "to_emails": [e["email"] for e in d["to"]], "cc_emails": [e["email"] for e in d["cc"]], "bcc_emails": [e["email"] for e in d["bcc"]],
             "subject": d["subject"], "body": d["body"], "via": "smtp" if smtp_ready() else "gmail"}
    ask_key = "mail_confirm_send" if smtp_ready() else "mail_confirm_gmail"
    return Result(t(lang, ask_key, to=", ".join(shown["to"])), {"type": "mail_draft", "draft": shown}, on_confirm=lambda: _deliver(d, lang))


def _contact_commands(text: str, lang: str) -> Optional[Result]:
    low = text.strip().lower()
    if re.fullmatch(r"(?:show |list |open )?(?:my |all )?contacts|मेरे (?:कॉन्टैक्ट|संपर्क)(?: दिखाओ)?", low):
        book = load_contacts()
        if not book:
            return Result(t(lang, "contacts_none"))
        return Result("\n".join(f"{i}. " + (f"{c['name'].title()}: " if c.get("name") else "") + c["email"] for i, c in enumerate(book, 1)))
    m = re.match(r"^(?:save|add|store)\s+(?:a\s+)?contact\s+(?P<n>.+?)\s+(?:as|is|with|:|=)\s*(?P<a>.+)$", text.strip(), re.I) or re.match(
        r"^(?P<n>[\w .'-]+?)(?:'s|\s+ka|\s+का)?\s+(?:e-?mail|mail|ईमेल)(?:\s+(?:address|id))?\s*(?:is|=|:|है)\s*(?P<a>.+)$", text.strip(), re.I
    )
    if m:
        addr = find_email(m.group("a"))
        if addr:
            remember(addr, m.group("n"))
            return Result(t(lang, "contact_saved", name=m.group("n").strip().title(), email=addr))
    return None


def handle(s, text: str, lang: str) -> Optional[Result]:
    """Returns a Result if this message belongs to the email flow, else None."""
    text = text.strip()
    if s.mail and _CANCEL.match(text):
        s.mail = None
        return Result(t(lang, "cancelled"))

    r = _contact_commands(text, lang)
    if r:
        return r

    if _wants_mail(text):
        p = _parse_hi(text) if _DEVANAGARI.search(text) else _parse_en(text)
        s.mail = {
            "to": _entries(p["to"]),
            "cc": _entries(p["cc"]) if p["cc"].strip() else None,
            "bcc": _entries(p["bcc"]) if p["bcc"].strip() else None,
            "subject": p["subject"].strip() or None,
            "body": p["body"].strip(), "ask": None, "pick": None,
        }
        return _next(s, lang)

    if not s.mail:
        return None

    m = s.mail
    ask = m["ask"]
    skip = bool(_SKIP.match(text))
    has_email = bool(find_email(text))

    # The who/which questions expect a short answer. Anything longer means "forget the email".
    if ask in ("to", "cc", "bcc", "addr", "pick") and not has_email and not skip:
        multi = ask in ("to", "cc", "bcc") and re.search(r"\band\b|,|और", text)
        if (ask == "pick" and _number(text) is not None and len(text.split()) <= 4) or False:
            pass
        elif len(text.split()) > (4 if multi else 2) or (ask in ("addr", "pick") and m.get("miss") and _number(text) is None):
            s.mail = None
            return None

    if ask == "to":
        if skip:
            s.mail = None
            return Result(t(lang, "cancelled"))
        m["to"] = _entries(re.sub(r"^(?:to|for)\s+", "", text, flags=re.I))
    elif ask in ("cc", "bcc"):
        m[ask] = [] if skip else _entries(re.sub(r"^(?:cc|bcc|to)\s+", "", text, flags=re.I))
    elif ask == "subject":
        m["subject"] = "" if skip else re.sub(r"^(?:subject|about)\s+", "", text, flags=re.I)
    elif ask == "body":
        if skip:
            return Result(t(lang, "mail_need_body"))
        m["body"] = re.sub(r"^(?:saying|say|that|कि)\s+", "", text, flags=re.I)
    elif ask == "pick":
        e, n = m["pick"], _number(text)
        chosen = None
        if has_email:
            chosen = next((c for c in e["cands"] if c["email"] == find_email(text)), None)
        elif n and 1 <= n <= len(e["cands"]):
            chosen = e["cands"][n - 1]
        if not chosen:
            m["miss"] = True
            return Result(t(lang, "mail_pick_bad", n=len(e["cands"])), _pick_options(e["cands"]))
        e["email"], e["cands"] = chosen["email"], []
        e["name"] = (chosen.get("name") or "").title()  # no saved name -> no greeting
        m["miss"] = False
    elif ask == "addr":
        addr = find_email(text)
        if not addr:
            m["miss"] = True
            return Result(t(lang, "mail_bad_addr"))
        e = m["pick"]
        e["email"] = addr
        remember(addr, e["name"])
        m["miss"] = False
    return _next(s, lang)
