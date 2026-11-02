"""The assistant's name (changeable) and wake-word matching ("Hey Jarvis ...", "... Jarvis")."""

import json
import os
import re
import threading

from . import config

DEFAULT_NAME = "Jarvis"
_lock = threading.Lock()
_VALID = re.compile(r"^[\wऀ-ॿ][\wऀ-ॿ .'-]{0,19}$")

# Speech recognition often spells the default name differently.
_ALIASES = {"jarvis": ["jarvis", "jarvish", "jarves", "jervis", "jarvas", "जार्विस", "जारविस", "जरविस", "जार्विश"]}
_FILLERS = {"hey", "hi", "hello", "ok", "okay", "yo", "ay", "हे", "हेलो", "हैलो", "ओके", "अरे", "सुनो"}
_TRAILING = {"please", "pls", "प्लीज़", "प्लीज"}


def _path() -> str:
    os.makedirs(config.DATA_DIR, exist_ok=True)
    return os.path.join(config.DATA_DIR, "settings.json")


def _load() -> dict:
    try:
        with open(_path(), encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def _update(**changes) -> None:
    """Read-modify-write, so one setting never wipes another."""
    with _lock:
        data = _load()
        data.update(changes)
        with open(_path(), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=1)


def get_name() -> str:
    name = _load().get("name", "")
    return name if isinstance(name, str) and _VALID.match(name) else DEFAULT_NAME


def set_name(name: str) -> str:
    name = re.sub(r"\s+", " ", name).strip(" .,!?;:\"'“”")
    if not _VALID.match(name):
        raise ValueError("Pick a short name (up to 20 letters or digits).")
    _update(name=name)
    return name


def get_music() -> tuple[str, bool]:
    """(music folder, use YouTube instead). The folder falls back to MUSIC_DIR from .env."""
    d = _load()
    folder = d.get("music_dir", "")
    return (folder if isinstance(folder, str) and folder else config.MUSIC_DIR), bool(d.get("music_online"))


def set_music(folder: str = "", online: bool = False) -> None:
    _update(music_dir=folder, music_online=online)


def _lev(a: str, b: str) -> int:
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def _norm(w: str) -> str:
    return re.sub(r"[^\wऀ-ॿ]", "", w.lower())


def _is_name_token(tok: str, want: str) -> bool:
    tok = _norm(tok)
    if not tok:
        return False
    if tok in _ALIASES.get(want, [want]):
        return True
    return len(want) >= 5 and len(tok) >= 4 and _lev(tok, want) <= 1


def split_wake(text: str, name: str = "") -> tuple[bool, str]:
    """('Hey Jarvis, good morning') -> (True, 'good morning'); ('send an email Jarvis') -> (True, 'send an email').

    The name only counts at the very start (after "hey"/"ok") or the very end (before "please")."""
    name_toks = [_norm(w) for w in (name or get_name()).split()]
    name_toks = [w for w in name_toks if w]
    words = text.split()
    k = len(name_toks)
    if not words or not k:
        return False, text

    def hit(seg: list[str]) -> bool:
        return len(seg) == k and all(_is_name_token(a, b) for a, b in zip(seg, name_toks))

    i = 0
    while i < len(words) and _norm(words[i]) in _FILLERS:
        i += 1
    if hit(words[i:i + k]):
        return True, " ".join(words[i + k:]).lstrip(" ,.:;-!").strip()

    j = len(words)
    while j > 0 and _norm(words[j - 1]) in _TRAILING:
        j -= 1
    if j - k >= 0 and hit(words[j - k:j]):
        start = j - k
        while start > 0 and _norm(words[start - 1]) in _FILLERS:
            start -= 1
        return True, " ".join(words[:start]).rstrip(" ,.:;-!").strip()
    return False, text
