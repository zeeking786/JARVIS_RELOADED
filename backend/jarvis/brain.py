"""Claude client access and the Wikipedia fallback."""

import json
import urllib.parse
import urllib.request

from . import config

LANG_NAME = {"en": "English", "hi": "Hindi (Devanagari script)"}

_client = None


def claude_enabled() -> bool:
    return bool(config.ANTHROPIC_API_KEY)


def _get_client():
    global _client
    if _client is None:
        import anthropic

        _client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
    return _client


def ask_wikipedia(query: str, lang: str) -> str | None:
    base = f"https://{'hi' if lang == 'hi' else 'en'}.wikipedia.org"
    headers = {"User-Agent": "JarvisAssistant/1.0"}

    def get(url):
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=6) as r:
            return json.load(r)

    q = urllib.parse.urlencode(
        {"action": "query", "list": "search", "srsearch": query, "format": "json", "srlimit": 1}
    )
    hits = get(f"{base}/w/api.php?{q}")["query"]["search"]
    if not hits:
        return None
    title = urllib.parse.quote(hits[0]["title"].replace(" ", "_"))
    extract = get(f"{base}/api/rest_v1/page/summary/{title}").get("extract", "")
    sentences = extract.replace("।", ".").split(". ")
    return ". ".join(sentences[:10]).strip() or None
