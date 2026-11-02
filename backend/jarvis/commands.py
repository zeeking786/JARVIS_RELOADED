"""Command routing. Each rule is (matcher, handler); the first match wins."""

import ast
import datetime
import operator
import os
import re
import socket
import subprocess
import sys
import urllib.parse
import uuid
import webbrowser
from dataclasses import dataclass
from typing import Callable, Optional

from . import config
from .i18n import t

IS_WINDOWS = sys.platform == "win32"


@dataclass
class Result:
    reply: str
    action: Optional[dict] = None
    # If set, the engine asks the user to say yes/no and calls this on "yes".
    on_confirm: Optional[Callable[[], "Result"]] = None


# ---------------------------------------------------------------- helpers


def _has(text: str, words) -> bool:
    for w in words:
        if w.isascii():
            if re.search(rf"\b{re.escape(w)}\b", text):
                return True
        elif w in text:
            return True
    return False


def _open_url(url: str) -> None:
    webbrowser.open(url)


def _search_url(base: str, q: str) -> str:
    return base + urllib.parse.quote_plus(q)


def _strip(text: str, words) -> str:
    for w in sorted(words, key=len, reverse=True):
        text = re.sub(rf"\b{re.escape(w)}\b" if w.isascii() else re.escape(w), " ", text)
    return re.sub(r"\s+", " ", text).strip()


# ---------------------------------------------------------------- tables

OPEN_WORDS = ["open", "launch", "start", "खोल", "ओपन", "खुला", "खुले", "चालू"]

SITES = {
    "YouTube": ("https://www.youtube.com", ["youtube", "यूट्यूब", "यू ट्यूब"]),
    "Google": ("https://www.google.com", ["google", "गूगल"]),
    "Gmail": ("https://mail.google.com", ["gmail", "जीमेल", "email inbox"]),
    "TutorialsPoint": ("https://www.tutorialspoint.com", ["tutorialspoint", "tutorials point", "ट्यूटोरियल"]),
    "GeeksforGeeks": ("https://www.geeksforgeeks.org", ["geeksforgeeks", "geeks for geeks", "गीक्स", "जीजेफोर्गेस"]),
    "Javatpoint": ("https://www.javatpoint.com", ["javatpoint", "java t point", "जावाटपॉइंट", "ज्वॉइंटपॉइंट"]),
}

# name -> (launch argv for `cmd /c start "" ...`, keywords)
APPS = {
    "Notepad": (["notepad.exe"], ["notepad", "नोटपैड", "नोटपेड"]),
    "Command Prompt": (["cmd.exe"], ["cmd", "command prompt", "सीएमडी", "कमांड प्रॉम्प्ट"]),
    "Chrome": (["chrome"], ["chrome", "क्रोम"]),
    "Calculator": (["calc.exe"], ["calculator", "कैलकुलेटर"]),
}

# ---------------------------------------------------------------- math

_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}


def _eval(node):
    if isinstance(node, ast.Expression):
        return _eval(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        return -_eval(node.operand)
    if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
        a, b = _eval(node.left), _eval(node.right)
        if isinstance(node.op, ast.Pow) and abs(b) > 100:
            raise ValueError("exponent too large")
        return _OPS[type(node.op)](a, b)
    raise ValueError("unsupported")


_MATH_WORDS = [
    (r"\bmultiplied by\b|\btimes\b|\binto\b|गुणा", "*"),
    (r"\bdivided by\b|\bby\b|भाग", "/"),
    (r"\bplus\b|\band\b|जोड़|जोड़ें", "+"),
    (r"\bminus\b|घटा|घटाओ", "-"),
    (r"\bpower\b|\^", "**"),
    (r"\bx\b", "*"),
]


def _try_math(text: str):
    expr = re.sub(r"\b(what is|what's|calculate|solve|कितना है|क्या है|बताओ)\b|[?=]", " ", text)
    for pat, rep in _MATH_WORDS:
        expr = re.sub(pat, f" {rep} ", expr)
    expr = expr.replace(",", "").strip()
    if not re.search(r"\d", expr) or not re.fullmatch(r"[\d\s.+\-*/()%]+", expr):
        return None
    try:
        val = _eval(ast.parse(expr, mode="eval"))
    except Exception:
        return None
    return int(val) if isinstance(val, float) and val.is_integer() else round(val, 6)


# ---------------------------------------------------------------- handlers


_WISHES = [
    ("good morning", "greet_morning"), ("good afternoon", "greet_afternoon"), ("good evening", "greet_evening"),
    ("good night", "greet_night"), ("सुप्रभात", "greet_morning"), ("शुभ प्रभात", "greet_morning"),
    ("शुभ संध्या", "greet_evening"), ("शुभ रात्रि", "greet_night"),
]


def _greeting(lang):
    h = datetime.datetime.now().hour
    key = "greet_morning" if h < 12 else "greet_afternoon" if h < 18 else "greet_evening"
    return t(lang, key)


def _launch_app(name, argv, lang) -> Result:
    if not IS_WINDOWS:
        return Result(t(lang, "unavailable"))
    subprocess.Popen(["cmd", "/c", "start", "", *argv], shell=False)
    return Result(t(lang, "opening", name=name), {"type": "opened", "name": name})


def _open_site(name, url, lang) -> Result:
    _open_url(url)
    return Result(t(lang, "opening", name=name), {"type": "opened", "name": name, "url": url})


def _shutdown(lang) -> Result:
    if not IS_WINDOWS:
        return Result(t(lang, "unavailable"))
    subprocess.Popen(["shutdown", "/s", "/t", "30"])
    return Result(t(lang, "shutdown_ok"), {"type": "sleep"})


def _cancel_shutdown(lang) -> Result:
    if IS_WINDOWS:
        subprocess.Popen(["shutdown", "/a"])
    return Result(t(lang, "shutdown_cancel"))


def _ip() -> str:
    # Connecting a UDP socket sends nothing; it just picks the outbound interface.
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except OSError:
        return socket.gethostbyname(socket.gethostname())
    finally:
        s.close()


def _mac() -> str:
    raw = f"{uuid.getnode():012x}"
    return ":".join(raw[i : i + 2] for i in range(0, 12, 2))


def _play_song(query: str, lang) -> Result:
    if not query:
        return Result(t(lang, "which_song"))
    search = _search_url("https://www.youtube.com/results?search_query=", query + " song")
    # A search page never starts a video, so open the first result itself. If YouTube can't be reached, show the search.
    video = _first_video(query + " song")
    url = f"https://www.youtube.com/watch?v={video}" if video else search
    _open_url(url)
    return Result(t(lang, "playing", q=query), {"type": "opened", "name": query, "url": url})


def _first_video(query: str) -> Optional[str]:
    """Id of the first video YouTube finds for the query, without any API key. None when it can't be read."""
    import urllib.request

    req = urllib.request.Request(
        _search_url("https://www.youtube.com/results?search_query=", query),
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120 Safari/537.36", "Accept-Language": "en-US,en;q=0.9",
                 "Cookie": "CONSENT=YES+1; SOCS=CAI"},
    )
    try:
        with urllib.request.urlopen(req, timeout=6) as r:
            page = r.read(1_500_000).decode("utf-8", "ignore")
    except Exception:
        return None
    m = re.search(r'"videoRenderer":\{"videoId":"([\w-]{11})"', page)
    return m.group(1) if m else None


# ---------------------------------------------------------------- router

EXIT = ["exit", "bye", "goodbye", "sleep", "go offline", "बाहर जाएं", "अलविदा", "सो जाओ", "ऑफलाइन", "ऑफ़लाइन", "बाय"]
SHUTDOWN = ["shutdown", "shut down", "turn off the computer", "बंद करना", "बंद करो", "सिस्टम बंद", "शटडाउन"]
CANCEL_SHUTDOWN = ["cancel shutdown", "abort shutdown", "शटडाउन रद्द"]
SONG_HI = ["गाना बजा", "गीत बजा", "संगीत बजा", "गाना चला", "गाने चला"]
FILLER_HI = ["यूट्यूब", "का", "के", "की", "वीडियो", "चित्र", "तस्वीर", "बजाओ", "बजा", "गाना", "गीत", "संगीत", "चलाओ", "ऑनलाइन"]


def route(text: str, lang: str, attachments=()) -> Optional[Result]:
    text = re.sub(r"[.!?,।]+$", "", text.strip().lower())
    if not text:
        return None

    if _has(text, CANCEL_SHUTDOWN):
        return _cancel_shutdown(lang)
    if _has(text, EXIT) and not _has(text, SHUTDOWN):
        return Result(t(lang, "bye"), {"type": "sleep"})
    if _has(text, SHUTDOWN):
        return Result(t(lang, "confirm_shutdown"), on_confirm=lambda: _shutdown(lang))

    from . import offline  # imported here: offline imports Result from this module

    r = offline.route(text, lang, attachments)
    if r:
        return r

    if _has(text, ["ip address", "my ip", "आईपी"]):
        return Result(t(lang, "ip", ip=_ip()))
    if _has(text, ["mac address", "my mac", "मैक पता", "मैक एड्रेस"]):
        return Result(t(lang, "mac", mac=_mac()))
    if _has(text, ["date", "तारीख", "आज की तारीख"]):
        return Result(t(lang, "date", date=datetime.date.today().strftime("%A, %d %B %Y")))
    if _has(text, ["time", "समय", "टाइम"]):
        return Result(t(lang, "time", time=datetime.datetime.now().strftime("%I:%M %p")))

    if _has(text, ["send email", "send mail", "send an email", "ईमेल भेज", "मेल भेज"]):
        return Result(t(lang, "email"), {"type": "compose_email"})
    if _has(text, ["click my picture", "take a picture", "take my photo", "take a photo", "selfie", "तस्वीर ले", "फोटो ले", "फ़ोटो ले"]):
        return Result(t(lang, "camera"), {"type": "camera"})
    if _has(text, ["pie chart", "पाई चार्ट"]):
        return Result(t(lang, "pie"), {"type": "chart", "kind": "pie", "title": "Daily activity",
                                       "data": {"Eat": 3, "Sleep": 7, "Work": 8, "Play": 6}})
    if _has(text, ["bar graph", "bar chart", "बार ग्राफ", "ड्रॉ बार"]):
        return Result(t(lang, "bar"), {"type": "chart", "kind": "bar", "title": "Sample data",
                                       "data": {"1": 2, "2": 4, "3": 1}})
    if _has(text, ["pentagon", "make a pattern", "make shape", "आकार बनाओ"]):
        return Result(t(lang, "shape"), {"type": "spiral"})

    m = re.search(r"youtube (?:videos? )?(?:of|for|about) (.+)", text)
    if m or ("यूट्यूब" in text and "वीडियो" in text):
        q = m.group(1) if m else _strip(text, FILLER_HI)
        url = _search_url("https://www.youtube.com/results?search_query=", q)
        _open_url(url)
        return Result(t(lang, "searching", q=q), {"type": "opened", "name": q, "url": url})

    m = re.search(r"(?:images?|pictures?|photos?) of (.+)", text) or re.search(r"(.+?) (?:का|के|की) (?:चित्र|तस्वीर|फोटो)", text)
    if m:
        q = m.group(1).strip()
        url = _search_url("https://www.google.com/search?tbm=isch&q=", q)
        _open_url(url)
        return Result(t(lang, "searching", q=q), {"type": "opened", "name": q, "url": url})

    m = re.match(r"play (?:the )?(?:online )?(?:song )?(.*)", text)
    if m:
        q = m.group(1).strip()
        return _play_song("" if q in ("song", "music", "a song") else q, lang)
    if _has(text, SONG_HI):
        return _play_song(_strip(text, FILLER_HI), lang)

    if _has(text, OPEN_WORDS):
        for name, (argv, kws) in APPS.items():
            if _has(text, kws):
                return _launch_app(name, argv, lang)
        for name, (url, kws) in SITES.items():
            if _has(text, kws):
                return _open_site(name, url, lang)

    if _has(text, ["how are you", "आप कैसे हैं", "कैसे हो"]):
        return Result(t(lang, "how_are_you"))
    if _has(text, ["your name", "who are you", "तुम्हारा नाम", "आपका नाम"]):
        return Result(t(lang, "name"))
    if len(text.split()) <= 5:
        for phrase, key in _WISHES:
            if phrase in text:
                return Result(f"{t(lang, key)} {t(lang, 'greet_help')}")
    if _has(text, ["hello", "hi", "hey", "नमस्ते", "हैलो"]) and len(text.split()) <= 3:
        return Result(_greeting(lang))

    ans = _try_math(text)
    if ans is not None:
        return Result(t(lang, "math", ans=ans))

    return None
