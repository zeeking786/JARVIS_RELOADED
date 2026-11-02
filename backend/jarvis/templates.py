"""Fill-in-the-blanks documents. No AI: the user supplies the content, we supply the layout."""

import datetime
import html
import re
from dataclasses import dataclass, field
from typing import Callable


def L(lang: str, en: str, hi: str) -> str:
    return hi if lang == "hi" else en


@dataclass
class Field:
    key: str
    en: str
    hi: str
    multiline: bool = False
    options: list = field(default_factory=list)
    default: str = ""
    required: bool = True


@dataclass
class Template:
    id: str
    en: str
    hi: str
    keywords: list
    fields: list
    build: Callable  # (values: dict, lang: str) -> (filename, content)


def _today() -> str:
    return datetime.date.today().strftime("%d %B %Y")


def _slug(text: str, fallback="document") -> str:
    s = re.sub(r"[^\wऀ-ॿ]+", "-", text).strip("-")[:40]
    return s or fallback


def _lines(text: str) -> list[str]:
    return [l.strip(" -*•\t") for l in text.splitlines() if l.strip(" -*•\t")]


def _num(s: str):
    try:
        return float(s.replace(",", ""))
    except ValueError:
        return None


def _fmt(n: float) -> str:
    return str(int(n)) if float(n).is_integer() else f"{n:.2f}"


# ---------------------------------------------------------------- builders


def _leave(v, lang):
    if lang == "hi":
        c = (f"दिनांक: {_today()}\n\nसेवा में,\n{v['to']}\n\n**विषय: अवकाश हेतु आवेदन**\n\nमहोदय/महोदया,\n\n"
             f"सविनय निवेदन है कि मैं, {v['name']}, {v['reason']} के कारण {v['from_date']} से {v['to_date']} तक अवकाश लेना चाहता/चाहती हूँ। "
             f"कृपया मेरा अवकाश स्वीकृत करने की कृपा करें।\n\nधन्यवाद।\n\nभवदीय,\n{v['name']}")
    else:
        c = (f"Date: {_today()}\n\nTo,\n{v['to']}\n\n**Subject: Application for leave**\n\nRespected Sir/Madam,\n\n"
             f"I, {v['name']}, request leave from {v['from_date']} to {v['to_date']} due to {v['reason']}. "
             f"Kindly grant me leave for this period.\n\nThank you.\n\nYours sincerely,\n{v['name']}")
    return f"Leave-application-{_slug(v['name'])}.docx", c


def _resign(v, lang):
    if lang == "hi":
        c = (f"दिनांक: {_today()}\n\nसेवा में,\n{v['to']}\n\n**विषय: त्यागपत्र**\n\nमहोदय/महोदया,\n\n"
             f"मैं, {v['name']}, अपने पद से त्यागपत्र देता/देती हूँ। मेरा अंतिम कार्य दिवस {v['last_day']} होगा।"
             + (f" कारण: {v['reason']}।" if v.get("reason") else "")
             + "\n\nइस अवसर के लिए धन्यवाद। मैं कार्य हस्तांतरण में पूर्ण सहयोग करूँगा/करूँगी।\n\n"
             f"भवदीय,\n{v['name']}")
    else:
        c = (f"Date: {_today()}\n\nTo,\n{v['to']}\n\n**Subject: Resignation**\n\nDear Sir/Madam,\n\n"
             f"I, {v['name']}, hereby resign from my position. My last working day will be {v['last_day']}."
             + (f" Reason: {v['reason']}." if v.get("reason") else "")
             + "\n\nThank you for the opportunity. I will fully support the handover.\n\n"
             f"Yours sincerely,\n{v['name']}")
    return f"Resignation-{_slug(v['name'])}.docx", c


def _invoice(v, lang):
    rows, total = [], 0.0
    for line in _lines(v["items"]):
        p = [x.strip() for x in line.split(",")]
        if len(p) >= 3 and _num(p[-1]) is not None and _num(p[-2]) is not None:
            qty, price = _num(p[-2]), _num(p[-1])
            amount = qty * price
            total += amount
            rows.append(f'"{",".join(p[:-2])}",{_fmt(qty)},{_fmt(price)},{_fmt(amount)}')
    if not rows:
        raise ValueError(L(lang, "Items must look like: Pen, 10, 5 (name, quantity, price) — one per line.",
                           "आइटम इस तरह लिखें: पेन, 10, 5 (नाम, मात्रा, कीमत) — हर पंक्ति में एक।"))
    head = L(lang, "Item,Qty,Price,Amount", "आइटम,मात्रा,कीमत,राशि")
    lines = [f"{L(lang, 'Invoice', 'इनवॉइस')} {v['number']}", f"{L(lang, 'Client', 'ग्राहक')}: {v['client']}",
             f"{L(lang, 'Date', 'दिनांक')}: {_today()}", "", head, *rows, f"{L(lang, 'Total', 'कुल')},,,{_fmt(total)}"]
    return f"Invoice-{_slug(v['number'])}.xlsx", "\n".join(lines)


def _budget(v, lang):
    rows, total = [], 0.0
    for line in _lines(v["items"]):
        p = [x.strip() for x in line.rsplit(",", 1)]
        if len(p) == 2 and _num(p[1]) is not None:
            total += _num(p[1])
            rows.append(f'"{p[0]}",{_fmt(_num(p[1]))}')
    if not rows:
        raise ValueError(L(lang, "Items must look like: Rent, 12000 — one per line.", "आइटम इस तरह लिखें: किराया, 12000 — हर पंक्ति में एक।"))
    lines = [v["title"], "", L(lang, "Category,Amount", "श्रेणी,राशि"), *rows, f"{L(lang, 'Total', 'कुल')},{_fmt(total)}"]
    return f"Budget-{_slug(v['title'])}.xlsx", "\n".join(lines)


def _minutes(v, lang):
    h = lambda en, hi: f"## {L(lang, en, hi)}"
    c = (f"# {v['title']}\n\n**{L(lang, 'Date', 'दिनांक')}:** {v['date']}\n**{L(lang, 'Attendees', 'उपस्थित')}:** {v['attendees']}\n\n"
         f"{h('Agenda', 'एजेंडा')}\n" + "\n".join(f"- {x}" for x in _lines(v["agenda"]))
         + f"\n\n{h('Decisions and actions', 'निर्णय और कार्य')}\n" + "\n".join(f"- {x}" for x in _lines(v["decisions"])))
    return f"Minutes-{_slug(v['title'])}.docx", c


def _todo(v, lang):
    c = f"# {v['title']}\n\n" + "\n".join(f"- ☐ {x}" for x in _lines(v["items"]))
    return f"Checklist-{_slug(v['title'])}.docx", c


def _resume(v, lang):
    h = lambda en, hi: f"## {L(lang, en, hi)}"
    parts = [f"# {v['name']}", f"{v['email']} | {v['phone']}", "",
             h("Objective", "उद्देश्य"), v["objective"], "",
             h("Education", "शिक्षा"), *[f"- {x}" for x in _lines(v["education"])], "",
             h("Skills", "कौशल"), *[f"- {x.strip()}" for x in v["skills"].split(",") if x.strip()]]
    if v.get("experience", "").strip():
        parts += ["", h("Experience", "अनुभव"), *[f"- {x}" for x in _lines(v["experience"])]]
    return f"Resume-{_slug(v['name'])}.docx", "\n".join(parts)


BLANK_FORMATS = ["docx", "txt", "md", "xlsx", "csv", "pptx", "html"]


def _blank(v, lang):
    fmt = v.get("format") if v.get("format") in BLANK_FORMATS else "docx"
    title, body = v["title"].strip(), v.get("body", "")
    if fmt in ("docx", "md"):
        content = f"# {title}\n\n{body}"
    elif fmt == "txt":
        content = f"{title}\n\n{body}"
    elif fmt == "html":
        paras = "".join(f"<p>{html.escape(p)}</p>" for p in body.split("\n\n") if p.strip())
        content = f"<!doctype html><meta charset='utf-8'><title>{html.escape(title)}</title><h1>{html.escape(title)}</h1>{paras}"
    elif fmt == "pptx":
        content = body if re.search(r"^#", body, re.M) else f"# {title}\n{body}"
    else:  # xlsx, csv: body is CSV text
        content = body
    return f"{_slug(title)}.{fmt}", content


F = Field
TEMPLATES = {
    t.id: t
    for t in [
        Template("leave", "Leave application", "छुट्टी का आवेदन",
                 ["leave letter", "leave application", "छुट्टी", "अवकाश"],
                 [F("to", "To (e.g. Principal, Manager)", "किसे (जैसे प्रधानाचार्य, मैनेजर)"), F("name", "Your name", "आपका नाम"),
                  F("from_date", "From date", "कब से"), F("to_date", "To date", "कब तक"), F("reason", "Reason", "कारण")], _leave),
        Template("resignation", "Resignation letter", "त्यागपत्र",
                 ["resignation", "resign letter", "इस्तीफा", "त्यागपत्र"],
                 [F("to", "To (e.g. Manager)", "किसे (जैसे मैनेजर)"), F("name", "Your name", "आपका नाम"),
                  F("last_day", "Last working day", "अंतिम कार्य दिवस"), F("reason", "Reason (optional)", "कारण (वैकल्पिक)", required=False)], _resign),
        Template("invoice", "Invoice (Excel)", "इनवॉइस (Excel)", ["invoice", "इनवॉइस", "बिल"],
                 [F("number", "Invoice number", "इनवॉइस नंबर"), F("client", "Client name", "ग्राहक का नाम"),
                  F("items", "Items: name, quantity, price (one per line)", "आइटम: नाम, मात्रा, कीमत (हर पंक्ति में एक)", multiline=True)], _invoice),
        Template("budget", "Budget (Excel)", "बजट (Excel)", ["budget", "बजट"],
                 [F("title", "Title", "शीर्षक", default="Monthly budget"),
                  F("items", "Items: category, amount (one per line)", "आइटम: श्रेणी, राशि (हर पंक्ति में एक)", multiline=True)], _budget),
        Template("minutes", "Meeting minutes", "मीटिंग की कार्यवाही", ["meeting minutes", "minutes of meeting", "मीटिंग", "कार्यवाही"],
                 [F("title", "Meeting title", "मीटिंग का शीर्षक"), F("date", "Date", "दिनांक", default="{today}"),
                  F("attendees", "Attendees", "उपस्थित लोग"), F("agenda", "Agenda (one per line)", "एजेंडा (हर पंक्ति में एक)", multiline=True),
                  F("decisions", "Decisions / actions (one per line)", "निर्णय / कार्य (हर पंक्ति में एक)", multiline=True)], _minutes),
        Template("todo", "Checklist", "चेकलिस्ट", ["checklist", "check list", "to-do list", "todo list", "चेकलिस्ट"],
                 [F("title", "Title", "शीर्षक"), F("items", "Items (one per line)", "आइटम (हर पंक्ति में एक)", multiline=True)], _todo),
        Template("resume", "Resume", "रिज्यूमे", ["resume", "cv", "biodata", "रिज्यूमे", "बायोडाटा"],
                 [F("name", "Full name", "पूरा नाम"), F("email", "Email", "ईमेल"), F("phone", "Phone", "फोन"),
                  F("objective", "Objective", "उद्देश्य", multiline=True), F("education", "Education (one per line)", "शिक्षा (हर पंक्ति में एक)", multiline=True),
                  F("skills", "Skills (comma separated)", "कौशल (कॉमा से अलग)"),
                  F("experience", "Experience (one per line, optional)", "अनुभव (वैकल्पिक)", multiline=True, required=False)], _resume),
        Template("blank", "Document", "दस्तावेज़", [],
                 [F("title", "Title", "शीर्षक"), F("body", "Content (CSV rows for Excel; '# Title' lines for slides)", "सामग्री (Excel के लिए CSV; स्लाइड के लिए '# शीर्षक')", multiline=True),
                  F("format", "Format", "फ़ॉर्मेट", options=BLANK_FORMATS, default="docx")], _blank),
    ]
}


def form_for(template_id: str, lang: str, default_format: str = "") -> dict:
    t = TEMPLATES[template_id]
    fields = []
    for f in t.fields:
        d = _today() if f.default == "{today}" else f.default
        if f.key == "format" and default_format:
            d = default_format
        fields.append({"key": f.key, "label": L(lang, f.en, f.hi), "multiline": f.multiline,
                       "options": f.options, "default": d, "required": f.required})
    return {"type": "form", "template": template_id, "title": L(lang, t.en, t.hi), "fields": fields}


def build(template_id: str, values: dict, lang: str) -> tuple[str, str]:
    """Returns (filename, content). Raises ValueError for bad input."""
    t = TEMPLATES.get(template_id)
    if t is None:
        raise ValueError("Unknown template")
    clean = {}
    for f in t.fields:
        val = str(values.get(f.key, "")).strip()[:5000]
        if f.required and not val:
            raise ValueError(L(lang, f"Please fill in: {f.en}", f"कृपया भरें: {f.hi}"))
        clean[f.key] = val
    return t.build(clean, lang)


def match_template(text: str) -> str | None:
    for t in TEMPLATES.values():
        if any((k in text) if not k.isascii() else re.search(rf"\b{re.escape(k)}\b", text) for k in t.keywords):
            return t.id
    return None
