"""Play songs from the user's own music folder.

"play believer": if no music folder is saved yet, Jarvis asks for it once, saves it in data/settings.json and then
plays the song from there. Later requests go straight to the folder. If the song is not in the folder (or the user
chose "use YouTube"), it falls back to YouTube like before.
"""

import os
import re
from typing import Optional

from . import commands, settings
from .commands import Result
from .i18n import t
from .mail import _number

AUDIO = {".mp3", ".m4a", ".wav", ".flac", ".ogg", ".aac", ".wma", ".opus"}
MAX_SCAN = 30000  # files looked at per search
MAX_OPTIONS = 5

_PLAY_EN = re.compile(r"^(?:please\s+)?play\s+(?:the\s+)?(?:(?:song|music|track)\s+)?(?P<q>.+)$", re.I)
_PLAY_HI = re.compile(r"(?:गाना|गाने|गीत|संगीत)\s+(?:बजा|चला)")
_ONLINE = re.compile(r"^(?:play\s+)?(?:online|youtube)\b", re.I)
_SET_DIR = re.compile(
    r"^(?:please\s+)?(?:set|change|update)\s+(?:my\s+)?(?:music|songs?)\s+(?:folder|path|directory)(?:\s+(?:to|as|is))?\s*(?P<p>.*)$"
    r"|^(?:my\s+)?(?:music|songs?)\s+(?:is|are)\s+(?:in|at)\s+(?P<p2>.+)$"
    r"|^(?:मेरा|मेरे)\s+(?:गाने|संगीत)\s+(?P<p3>.+?)\s+(?:में|मे)\s+(?:हैं|है)$"
    r"|^म्यूज़?िक\s+फ़?ोल्डर\s+(?:सेट|बदल)\w*(?:\s+\w+)?$",
    re.I,
)
_SHOW_DIR = re.compile(r"^(?:where is|what is|show)\s+(?:my\s+)?(?:music|songs?)\s+(?:folder|path|directory)$|^मेरा\s+(?:म्यूज़िक|संगीत)\s+फोल्डर\s+कहाँ\s+है$", re.I)
_USE_YT = re.compile(r"^(?:use|play from)\s+(?:youtube|online)\s+(?:for\s+)?(?:songs?|music)?$|^(?:songs?|music)\s+(?:from|on)\s+(?:youtube|online)$", re.I)
_CANCEL = re.compile(r"^\W*(cancel|stop|never ?mind|forget it|रद्द|छोड़ो|रहने दो|कैंसिल)\W*$", re.I)
_SKIP = re.compile(r"^\W*(skip|no|none|don'?t have|i don'?t have any|स्किप|नहीं)\W*$", re.I)


# ---------------------------------------------------------------- folder handling


def spoken_path(text: str) -> str:
    """'d colon backslash my music' -> 'd:\\my music'. Typed paths pass through unchanged."""
    p = text.strip().strip("\"'“”")
    if re.search(r"\bcolon\b|\b(?:back ?slash|slash)\b", p, re.I):
        p = re.sub(r"\s*\bcolon\b\s*", ":", p, flags=re.I)
        p = re.sub(r"\s*\b(?:back ?slash|slash)\b\s*", "\\\\", p, flags=re.I)
    return os.path.expandvars(os.path.expanduser(p)).rstrip(" .")


def _looks_like_path(text: str) -> bool:
    return bool(re.search(r"[A-Za-z]:|\\|/|~|%\w+%|\bcolon\b|\bslash\b", text))


def _scan(folder: str):
    n = 0
    for root, _dirs, files in os.walk(folder):
        for f in files:
            n += 1
            if n > MAX_SCAN:
                return
            if os.path.splitext(f)[1].lower() in AUDIO:
                yield os.path.join(root, f)


def _words(s: str) -> list[str]:
    return re.findall(r"[\wऀ-ॿ]+", s.lower())


def find(folder: str, query: str) -> list[str]:
    """Songs whose file name contains every word of the query, best (shortest name) first."""
    want = _words(query)
    if not want:
        return []
    hits = []
    for path in _scan(folder):
        name = _words(os.path.splitext(os.path.basename(path))[0])
        if all(any(w == n or w in n for n in name) for w in want):
            hits.append((len(" ".join(name)), path))
    hits.sort()
    return [p for _, p in hits]


def _open_file(path: str) -> None:
    """Starts the file in the default player. Tests replace this."""
    if commands.IS_WINDOWS:
        os.startfile(path)  # type: ignore[attr-defined]
    else:
        import subprocess
        import sys

        subprocess.Popen(["open" if sys.platform == "darwin" else "xdg-open", path])


def _play(path: str, lang: str) -> Result:
    _open_file(path)
    title = os.path.splitext(os.path.basename(path))[0]
    return Result(t(lang, "playing", q=title), {"type": "opened", "name": title})


def _youtube(query: str, lang: str) -> Result:
    return commands._play_song(query, lang)


# ---------------------------------------------------------------- flow


def _play_query(s, query: str, lang: str) -> Result:
    folder, online = settings.get_music()
    if online:
        return _youtube(query, lang)
    if not folder:
        s.music = {"ask": "dir", "query": query}
        return Result(t(lang, "music_ask_dir"))
    if not os.path.isdir(folder):
        s.music = {"ask": "dir", "query": query}
        return Result(t(lang, "music_dir_gone", path=folder))
    hits = find(folder, query)
    if not hits:
        r = _youtube(query, lang)
        return Result(t(lang, "music_not_found", q=query) + " " + r.reply, r.action)
    if len(hits) == 1 or os.path.splitext(os.path.basename(hits[0]))[0].lower() == query.lower():
        return _play(hits[0], lang)
    options = hits[:MAX_OPTIONS]
    s.music = {"ask": "pick", "options": options}
    listing = ", ".join(f"{i}. {os.path.splitext(os.path.basename(p))[0]}" for i, p in enumerate(options, 1))
    return Result(t(lang, "music_pick", n=len(hits), list=listing))


def _save_dir(s, raw: str, lang: str) -> Result:
    folder = spoken_path(raw)
    if not (os.path.isabs(folder) and os.path.isdir(folder)):
        return Result(t(lang, "music_dir_bad", path=folder))
    settings.set_music(os.path.abspath(folder), False)
    saved = t(lang, "music_saved", path=os.path.abspath(folder))
    query = (s.music or {}).get("query", "")
    s.music = None
    if not query:
        return Result(saved)
    r = _play_query(s, query, lang)
    return Result(saved + " " + r.reply, r.action)


def _query_from(text: str) -> str:
    m = _PLAY_EN.match(text.strip().rstrip(".!?"))
    if m and not _ONLINE.match(m.group("q")):
        q = m.group("q").strip()
        return "" if q.lower() in ("song", "music", "a song", "some music", "something") else q
    if _PLAY_HI.search(text):
        return commands._strip(text.lower(), commands.FILLER_HI)
    return ""


def handle(s, text: str, lang: str) -> Optional[Result]:
    """Returns a Result if this message belongs to the music flow, else None."""
    text = text.strip()
    state = getattr(s, "music", None)

    if state:
        if _CANCEL.match(text):
            s.music = None
            return Result(t(lang, "cancelled"))
        if state["ask"] == "dir":
            if _SKIP.match(text) or _ONLINE.match(text) or _USE_YT.match(text):
                settings.set_music("", True)
                query = state.get("query", "")
                s.music = None
                return Result(t(lang, "music_online_on")) if not query else _youtube(query, lang)
            if _looks_like_path(text):
                return _save_dir(s, text, lang)
        elif state["ask"] == "pick":
            n = _number(text)
            if n is not None and 1 <= n <= len(state["options"]) and len(text.split()) <= 4:
                s.music = None
                return _play(state["options"][n - 1], lang)
            if n is not None and len(text.split()) <= 4:
                return Result(t(lang, "music_pick_bad", n=len(state["options"])))
        s.music = None  # anything else is a new command

    low = text.lower().rstrip(".!?")
    if _USE_YT.match(low):
        settings.set_music("", True)
        return Result(t(lang, "music_online_on"))
    if _SHOW_DIR.match(low):
        folder, online = settings.get_music()
        if online:
            return Result(t(lang, "music_online_on"))
        return Result(t(lang, "music_dir_show", path=folder) if folder else t(lang, "music_dir_none"))
    m = _SET_DIR.match(text)
    if m:
        raw = next((g for g in m.groups() if g), "").strip()
        s.music = {"ask": "dir", "query": ""}
        return _save_dir(s, raw, lang) if raw else Result(t(lang, "music_ask_dir"))

    q = _query_from(text)
    if q:
        return _play_query(s, q, lang)
    return None
