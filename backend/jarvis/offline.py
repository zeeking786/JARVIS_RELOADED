"""Everything Jarvis can do without an AI key. Called from commands.route()."""

import random
import re
from typing import Optional

from . import documents, settings, templates, textutils, tools
from .commands import Result, _open_url
from .i18n import t
from .templates import L

CREATE = ["make", "create", "write", "generate", "prepare", "draft", "बनाओ", "बनाएं", "बनाइए", "बना दो", "लिखो", "तैयार"]
FORMAT_WORDS = {
    "docx": ["word", "docx", "वर्ड"], "xlsx": ["excel", "xlsx", "spreadsheet", "एक्सेल"], "csv": ["csv", "सीएसवी"],
    "pptx": ["powerpoint", "pptx", "ppt", "slides", "slide", "presentation", "पावरपॉइंट", "स्लाइड"],
    "md": ["markdown", " md"], "txt": ["text file", "txt", "plain text", "टेक्स्ट"],
}
DOC_WORDS = ["document", "doc", "file", "word", "excel", "spreadsheet", "slides", "presentation", "powerpoint",
             "दस्तावेज़", "डॉक्यूमेंट", "फाइल", "फ़ाइल", "स्लाइड", "वर्ड", "एक्सेल"]


def _any(text: str, subs) -> bool:
    return any(s in text for s in subs)


def _files_action(names: list[str]) -> dict:
    import urllib.parse

    return {"type": "files", "files": [{"name": n, "url": "/api/files/" + urllib.parse.quote(n)} for n in names]}


# ---------------------------------------------------------------- documents


def _pick(text: str, atts):
    low = text.lower()
    for a in reversed(atts):
        if a.name.lower() in low:
            return a
    for a in reversed(atts):
        if a.text:
            return a
    return atts[-1]


def _doc_commands(text: str, lang: str, atts) -> Optional[Result]:
    wants = (
        _any(text, ["summar", "सार", "संक्षेप", "keyword", "key word", "मुख्य शब्द", "word count", "how many words", "कितने शब्द",
                    "statistics", "read it", "read this", "read the file", "read the doc", "पढ़"])
        or re.search(r"\b(find|search|look for|locate)\b.*\b(in|inside|within)\b", text)
        or re.search(r"(convert|save|export|change|turn)\b.*\b(to|into|as)\b", text)
        or ("बदल" in text or "कन्वर्ट" in text)
        or re.search(r"(फाइल|फ़ाइल|दस्तावेज़|डॉक्यूमेंट)\s+(में|मे)\s+.+(खोजो|ढूंढो|ढूँढो)", text)
    )
    if not wants:
        return None
    att = _pick(text, atts)
    if att.kind == "image" or not att.text:
        return Result(L(lang, f"I can't read text from {att.name} without AI. Attach a PDF with a text layer, Word, Excel, PowerPoint or a text file.",
                        f"AI के बिना मैं {att.name} से पाठ नहीं पढ़ सकता। टेक्स्ट वाली PDF, Word, Excel, PowerPoint या टेक्स्ट फ़ाइल जोड़ें।"))
    body = att.text

    m = re.search(r"(?:find|search(?: for)?|look for|locate)\s+(.+?)\s+(?:in|inside|within)\s+(?:the\s+|this\s+|my\s+)?(?:file|document|doc|pdf|text|sheet)", text)
    m = m or re.search(r"(?:फाइल|फ़ाइल|दस्तावेज़|डॉक्यूमेंट)\s+(?:में|मे)\s+(.+?)\s+(?:खोजो|ढूंढो|ढूँढो|खोजें|ढूंढें)", text)
    if m:
        term = m.group(1).strip(" \"'")
        n, snippets = textutils.find(body, term)
        if not n:
            return Result(L(lang, f"“{term}” was not found in {att.name}.", f"“{term}” {att.name} में नहीं मिला।"))
        head = L(lang, f"Found “{term}” {n} time(s) in {att.name}:", f"“{term}” {att.name} में {n} बार मिला:")
        return Result(head + "\n" + "\n".join(f"• {s}" for s in snippets))

    m = re.search(r"(?:convert|save|export|change|turn)\b.*\b(?:to|into|as)\s+(?:a\s+|an\s+)?(.+)$", text) or (
        re.search(r"(.+)", text) if ("बदल" in text or "कन्वर्ट" in text) else None)
    if m:
        target = m.group(1)
        fmt = next((f for f, ws in FORMAT_WORDS.items() if _any(" " + target, ws)), None)
        if fmt:
            try:
                name = documents.convert(att, fmt)
            except ValueError as e:
                return Result(L(lang, f"I can't do that conversion: {e}", f"यह बदलाव नहीं हो सका: {e}"))
            return Result(L(lang, f"Converted to {fmt.upper()}: {name}", f"{fmt.upper()} में बदल दिया: {name}"), _files_action([name]))

    if _any(text, ["keyword", "key word", "मुख्य शब्द"]):
        kws = textutils.keywords(body)
        return Result(L(lang, "Key words: ", "मुख्य शब्द: ") + ", ".join(kws) if kws else L(lang, "No keywords found.", "कोई मुख्य शब्द नहीं मिला।"))
    if _any(text, ["word count", "how many words", "कितने शब्द", "statistics"]):
        s = textutils.stats(body)
        return Result(L(lang, f"{att.name}: {s['words']} words, {s['sentences']} sentences, about {s['minutes']} min to read.",
                        f"{att.name}: {s['words']} शब्द, {s['sentences']} वाक्य, पढ़ने में लगभग {s['minutes']} मिनट।"))
    if _any(text, ["summar", "सार", "संक्षेप"]):
        n = 3 if _any(text, ["short", "brief", "छोटा"]) else 5
        sents = textutils.summarize(body, n)
        if not sents:
            return Result(L(lang, "There is not enough text to summarise.", "सार बनाने के लिए पर्याप्त पाठ नहीं है।"))
        head = L(lang, f"Summary of {att.name} (key sentences picked from the text):", f"{att.name} का सार (पाठ से चुने गए मुख्य वाक्य):")
        return Result(head + "\n" + "\n".join(f"• {s}" for s in sents))
    if _any(text, ["read it", "read this", "read the file", "read the doc", "पढ़"]):
        excerpt = re.sub(r"\s+", " ", body).strip()[:1200]
        return Result(excerpt, {"type": "read"})
    return None


# ---------------------------------------------------------------- timers, tasks, notes


def _timer(text: str, lang: str) -> Optional[Result]:
    if not _any(text, ["timer", "remind me", "alarm", "टाइमर", "याद दिला", "अलार्म"]):
        return None
    seconds, m = tools.parse_duration(text)
    if not seconds:
        return Result(L(lang, "For how long? Say, for example: set a timer for 5 minutes.", "कितनी देर के लिए? जैसे: 5 मिनट का टाइमर लगाओ।"))
    label = ""
    if lang != "hi":
        t = re.search(r"\b(?:to|that|about)\s+(.+)$", text[m.end():] or text)
        label = t.group(1).strip() if t else ""
    else:
        rest = (text[: m.start()] + " " + text[m.end():])
        for w in ["में", "का", "टाइमर", "लगाओ", "लगा", "याद दिलाओ", "याद दिला", "अलार्म", "मुझे", "के लिए", "सेट करो", "करो"]:
            rest = rest.replace(w, " ")
        label = re.sub(r"\s+", " ", rest).strip()
    dur = tools.human_duration(seconds, lang)
    reply = (L(lang, f"Okay, I will remind you to {label} in {dur}.", f"ठीक है, {dur} में आपको {label} याद दिलाऊँगा।") if label
             else L(lang, f"Timer set for {dur}.", f"{dur} का टाइमर लग गया।"))
    return Result(reply, {"type": "timer", "seconds": seconds, "label": label or L(lang, "Timer finished", "टाइमर पूरा हुआ")})


def _tasks_notes(text: str, lang: str) -> Optional[Result]:
    m = re.search(r"^(?:add|new|create)\s+(?:a\s+)?task[:\s]+(.+)", text) or re.search(r"^add\s+(.+?)\s+to\s+(?:my\s+)?(?:to-?do|task)s?(?:\s+list)?$", text) \
        or re.search(r"^(?:नया\s+)?(?:काम|टास्क)\s+(?:जोड़ो|जोड़ें|जोड़)\s+(.+)", text)
    if m:
        n = tools.add_task(m.group(1))
        return Result(L(lang, f"Task added. You have {n} task(s).", f"काम जोड़ दिया। अब {n} काम हैं।"))
    m = re.search(r"^(?:done|complete|finish|finished|mark)\s+(?:task\s+)?(?:number\s+|no\.?\s*)?(\d+)", text) or re.search(r"task\s+(\d+)\s+(?:done|completed)", text) \
        or re.search(r"(\d+)\s*(?:नंबर\s*)?(?:का\s*)?(?:काम|टास्क)\s*(?:पूरा|हो गया)", text)
    if m:
        done = tools.complete_task(int(m.group(1)))
        if done is None:
            return Result(L(lang, "There is no task with that number.", "इस नंबर का कोई काम नहीं है।"))
        return Result(L(lang, f"Marked done: {done}", f"पूरा हुआ: {done}"))
    if re.search(r"clear\s+(?:all\s+)?(?:my\s+)?tasks?", text) or re.search(r"(?:सभी|सारे)\s+(?:काम|टास्क)\s+(?:हटाओ|मिटाओ)", text):
        tools.clear_tasks()
        return Result(L(lang, "All tasks cleared.", "सभी काम हटा दिए।"))
    if re.search(r"\b(?:my|show|list|read)\s+(?:my\s+)?(?:tasks?|to-?do(?:s|\s+list)?)\b", text) or re.search(r"मेरे\s+(?:काम|टास्क)|(?:काम|टास्क)\s+(?:दिखाओ|बताओ|पढ़ो)", text):
        items = tools.list_tasks()
        return Result("\n".join(items) if items else L(lang, "You have no tasks.", "आपका कोई काम नहीं है।"))

    m = re.search(r"^(?:take a note|make a note|note down|note|remember(?: that)?)(?:\s*[:\-]\s*|\s+)(.+)", text) \
        or re.search(r"^(?:नोट\s+(?:करो|कर लो|लिखो)|याद\s+रखो(?:\s+कि)?)\s*[:\-]?\s*(.+)", text)
    if m:
        n = tools.add_note(m.group(1))
        return Result(L(lang, f"Noted. You have {n} note(s).", f"नोट कर लिया। अब {n} नोट हैं।"))
    if re.search(r"clear\s+(?:all\s+)?(?:my\s+)?notes?", text) or re.search(r"(?:सभी|सारे)\s+नोट्?स?\s+(?:हटाओ|मिटाओ)", text):
        tools.clear_notes()
        return Result(L(lang, "All notes cleared.", "सभी नोट हटा दिए।"))
    if re.search(r"(?:show|read|list)\s+(?:my\s+)?notes?|\bmy notes\b|what are my notes", text) or re.search(r"मेरे\s+नोट्स|नोट्स\s+(?:दिखाओ|पढ़ो|बताओ)", text):
        items = tools.list_notes()
        return Result("\n".join(items) if items else L(lang, "You have no notes.", "आपका कोई नोट नहीं है।"))
    return None


# ---------------------------------------------------------------- info


def _units(text: str, lang: str) -> Optional[Result]:
    c = tools.convert_units(text)
    if not c:
        return None
    if c[0] == "unit":
        _, val, a, b, out = c
        return Result(f"{tools.fmt_number(val)} {a} = {tools.fmt_number(out)} {b}")
    _, val, src, dst = c
    try:
        out = tools.convert_currency(val, src, dst)
    except Exception:
        return Result(L(lang, "I could not fetch exchange rates. Check your internet connection.", "विनिमय दर नहीं मिल सकी। इंटरनेट जाँचें।"))
    return Result(f"{tools.fmt_number(val)} {src} = {tools.fmt_number(out)} {dst}")


_WEATHER_FILLER = ["what is the", "what's the", "how is the", "how's the", "weather", "forecast", "temperature", "today", "now", "like",
                   "in", "of", "for", "at", "the", "मौसम", "पूर्वानुमान", "का", "में", "की", "कैसा", "है", "आज", "बताओ", "बताइए", "अभी", "कैसी"]


def _weather(text: str, lang: str) -> Optional[Result]:
    if not _any(text, ["weather", "मौसम", "forecast"]):
        return None
    city = text
    for w in sorted(_WEATHER_FILLER, key=len, reverse=True):
        city = re.sub(rf"\b{re.escape(w)}\b" if w.isascii() else rf"(?<![\wऀ-ॿ]){re.escape(w)}(?![\wऀ-ॿ])", " ", city)
    city = re.sub(r"\s+", " ", city).strip()
    if not city:
        return Result(L(lang, "Which city? Say, for example: weather in Varanasi.", "कौन सा शहर? जैसे: वाराणसी का मौसम।"))
    try:
        return Result(tools.weather(city, lang))
    except LookupError:
        return Result(L(lang, f"I could not find a place called {city}.", f"{city} नाम की जगह नहीं मिली।"))
    except Exception:
        return Result(L(lang, "I could not fetch the weather. Check your internet connection.", "मौसम नहीं मिल सका। इंटरनेट जाँचें।"))


_RENAME = [
    re.compile(r"^(?:please )?(?:change|set|update) (?:your|ur) name to (.+)$"),
    re.compile(r"^(?:please )?(?:call yourself|rename yourself(?: to)?|your (?:new )?name is|from now on your name is|i (?:will|want to|am going to) call you) (.+)$"),
    re.compile(r"^(?:अपना|आपका|तुम्हारा) नाम (.+?) (?:रख(?:ो|ना|ें|लो| लो)|कर(?:ो| लो|दो| दो)|है)$"),
]


def _rename(text: str, lang: str) -> Optional[Result]:
    for rx in _RENAME:
        m = rx.match(text.strip().rstrip(".!"))
        if m:
            try:
                name = settings.set_name(m.group(1).title())
            except ValueError:
                return Result(t(lang, "rename_bad"))
            return Result(t(lang, "renamed", new=name), {"type": "rename", "name": name})
    return None


_STUDIO = re.compile(
    r"\b(?:document|doc|writing) (?:studio|editor)\b|\bopen (?:the |my )?editor\b"
    r"|\b(?:write|create|make|prepare|draft|build)\b.*\b(?:document|report|proposal|essay|article|brochure|manual|handbook|resume|newsletter)\b.*\b(?:with|including|add(?:ing)?)\b.*\b(?:images?|pictures?|photos?|screenshots?|tables?|headings?|logos?)\b"
    r"|(?:डॉक्यूमेंट|दस्तावेज़)\s*(?:स्टूडियो|एडिटर)|(?:तस्वीर|फोटो|इमेज)\w*\s+(?:वाला|वाली|के साथ)\s+(?:दस्तावेज़|डॉक्यूमेंट|रिपोर्ट)"
)


def _studio(text: str, lang: str) -> Optional[Result]:
    if _STUDIO.search(text):
        return Result(t(lang, "studio_open"), {"type": "studio"})
    return None


def _fun(text: str, lang: str) -> Optional[Result]:
    if _any(text, ["joke", "चुटकुला", "जोक"]):
        return Result(tools.joke(lang))
    if _any(text, ["flip a coin", "toss a coin", "सिक्का उछाल"]):
        return Result(L(lang, random.choice(["Heads.", "Tails."]), random.choice(["चित।", "पट।"])))
    if _any(text, ["roll a dice", "roll a die", "roll the dice", "पासा"]):
        return Result(L(lang, f"You rolled a {random.randint(1, 6)}.", f"पासे पर {random.randint(1, 6)} आया।"))
    m = re.search(r"random number(?: between (\d+) and (\d+))?", text)
    if m:
        lo, hi = (int(m.group(1)), int(m.group(2))) if m.group(1) else (1, 100)
        return Result(L(lang, f"Your number is {random.randint(min(lo, hi), max(lo, hi))}.", f"आपकी संख्या है {random.randint(min(lo, hi), max(lo, hi))}।"))
    return None


# ---------------------------------------------------------------- making documents


def _make(text: str, lang: str) -> Optional[Result]:
    if not _any(text, CREATE):
        return None
    tid = templates.match_template(text)
    if tid:
        return Result(L(lang, f"Fill in the details for your {templates.TEMPLATES[tid].en.lower()}.", f"{templates.TEMPLATES[tid].hi} के विवरण भरें।"),
                      templates.form_for(tid, lang))
    if _any(text, DOC_WORDS):
        fmt = next((f for f, ws in FORMAT_WORDS.items() if _any(" " + text, ws)), "docx")
        return Result(L(lang, "Type the title and content, and I will make the file.", "शीर्षक और सामग्री लिखिए, मैं फ़ाइल बना दूँगा।"),
                      templates.form_for("blank", lang, fmt))
    return None


def _web(text: str, lang: str) -> Optional[Result]:
    m = re.search(r"(?:open|go to|visit)\s+(?:https?://)?(?:www\.)?([a-z0-9-]+(?:\.[a-z0-9-]+)*\.(?:com|in|org|net|io|edu|gov|co|ai|dev|app|info))\b", text)
    if m:
        url = "https://" + m.group(1)
        _open_url(url)
        return Result(L(lang, f"Opening {m.group(1)}.", f"{m.group(1)} खोल रहा हूँ।"), {"type": "opened", "name": m.group(1), "url": url})
    m = re.search(r"^(?:search(?: for)?|google|look up)\s+(.+)", text) or re.search(r"^(?:गूगल पर\s+)?(.+?)\s+(?:सर्च करो|खोजो|ढूंढो)$", text)
    if m:
        import urllib.parse

        q = m.group(1).strip()
        url = "https://www.google.com/search?q=" + urllib.parse.quote_plus(q)
        _open_url(url)
        return Result(L(lang, f"Searching for {q}.", f"{q} खोज रहा हूँ।"), {"type": "opened", "name": q, "url": url})
    return None


def route(text: str, lang: str, attachments=()) -> Optional[Result]:
    """text is already lower-cased and stripped by commands.route()."""
    steps = [_rename, _studio, _timer, _tasks_notes, _units, _weather, _fun]
    for step in steps:
        r = step(text, lang)
        if r:
            return r
    if attachments:
        r = _doc_commands(text, lang, list(attachments))
        if r:
            return r
    return _make(text, lang) or _web(text, lang)
