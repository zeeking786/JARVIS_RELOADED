"""Offline text analysis (no AI): summary, keywords, statistics, search."""

import re
from collections import Counter

_STOP_EN = set(
    "a an the and or but if then else of to in on at by for with from as is are was were be been being it its this that "
    "these those i you he she we they them his her our their my your not no so do does did done have has had will would "
    "can could should may might than too very also into about over under up down out off just more most such there here "
    "what which who whom when where why how all any each other some".split()
)
_STOP_HI = set("का की के में से है हैं था थी थे को पर और या भी तो यह वह ये वो एक कि जो कर करना किया गया गई गए हो होता होती होते लिए साथ द्वारा".split())
STOP = _STOP_EN | _STOP_HI

_WORD = re.compile(r"[\wऀ-ॿ]+")


def words(text: str) -> list[str]:
    return [w.lower() for w in _WORD.findall(text)]


def sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?।])\s+|\n+", text)
    return [p.strip() for p in parts if len(words(p)) >= 3]


def _content_words(text: str) -> list[str]:
    return [w for w in words(text) if w not in STOP and len(w) > 2 and not w.isdigit()]


content_words = _content_words


def summarize(text: str, n: int = 5) -> list[str]:
    sents = sentences(text)
    if len(sents) <= n:
        return sents
    freq = Counter(_content_words(text))
    scored = []
    for i, s in enumerate(sents):
        ws = _content_words(s)
        if not ws or len(s) > 500:
            continue
        scored.append((sum(freq[w] for w in ws) / len(ws) ** 0.7, i))
    top = sorted(sorted(scored, reverse=True)[:n], key=lambda x: x[1])
    return [sents[i] for _, i in top]


def keywords(text: str, n: int = 8) -> list[str]:
    return [w for w, _ in Counter(_content_words(text)).most_common(n)]


def stats(text: str) -> dict:
    w = words(text)
    return {
        "words": len(w),
        "sentences": len(sentences(text)),
        "characters": len(text),
        "minutes": max(1, round(len(w) / 200)) if w else 0,
    }


def find(text: str, term: str, context: int = 70, limit: int = 5) -> tuple[int, list[str]]:
    """Returns (total matches, up to `limit` snippets)."""
    pattern = re.compile(re.escape(term), re.I)
    matches = list(pattern.finditer(text))
    snippets = []
    for m in matches[:limit]:
        a, b = max(0, m.start() - context), min(len(text), m.end() + context)
        snippets.append("…" + re.sub(r"\s+", " ", text[a:b]).strip() + "…")
    return len(matches), snippets
