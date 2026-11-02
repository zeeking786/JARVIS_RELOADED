"""Key-free utilities: notes, tasks, timers, weather, unit and currency conversion, fun."""

import datetime
import json
import os
import random
import re
import threading
import urllib.parse
import urllib.request

from . import config

_lock = threading.Lock()


# ---------------------------------------------------------------- storage


def _path(name: str) -> str:
    os.makedirs(config.DATA_DIR, exist_ok=True)
    return os.path.join(config.DATA_DIR, name + ".json")


def _load(name: str) -> list:
    try:
        with open(_path(name), encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except (OSError, ValueError):
        return []


def _save(name: str, data: list) -> None:
    with open(_path(name), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)


def add_note(text: str) -> int:
    with _lock:
        notes = _load("notes")
        notes.append({"text": text.strip()[:2000], "at": datetime.datetime.now().strftime("%d %b %H:%M")})
        _save("notes", notes)
        return len(notes)


def list_notes() -> list[str]:
    return [f"{i}. {n['text']} ({n['at']})" for i, n in enumerate(_load("notes"), 1)]


def clear_notes() -> None:
    with _lock:
        _save("notes", [])


def add_task(text: str) -> int:
    with _lock:
        tasks = _load("tasks")
        tasks.append({"text": text.strip()[:500], "done": False})
        _save("tasks", tasks)
        return len(tasks)


def list_tasks() -> list[str]:
    return [f"{i}. [{'x' if t['done'] else ' '}] {t['text']}" for i, t in enumerate(_load("tasks"), 1)]


def complete_task(n: int) -> str | None:
    with _lock:
        tasks = _load("tasks")
        if not 1 <= n <= len(tasks):
            return None
        tasks[n - 1]["done"] = True
        _save("tasks", tasks)
        return tasks[n - 1]["text"]


def clear_tasks() -> None:
    with _lock:
        _save("tasks", [])


# ---------------------------------------------------------------- timers

_UNIT_SECONDS = {
    "second": 1, "seconds": 1, "sec": 1, "secs": 1, "सेकंड": 1, "सेकण्ड": 1,
    "minute": 60, "minutes": 60, "min": 60, "mins": 60, "मिनट": 60,
    "hour": 3600, "hours": 3600, "hr": 3600, "hrs": 3600, "घंटे": 3600, "घंटा": 3600, "घण्टे": 3600, "घण्टा": 3600,
}
DURATION_RE = re.compile(r"(\d+(?:\.\d+)?)\s*(seconds?|secs?|minutes?|mins?|hours?|hrs?|सेकंड|सेकण्ड|मिनट|घंटे|घंटा|घण्टे|घण्टा)")


def parse_duration(text: str):
    """Returns (seconds, match) or (None, None)."""
    m = DURATION_RE.search(text)
    if not m:
        return None, None
    seconds = int(float(m.group(1)) * _UNIT_SECONDS[m.group(2)])
    return (seconds, m) if 0 < seconds <= 24 * 3600 else (None, None)


def human_duration(seconds: int, lang: str) -> str:
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    parts = []
    names = (("hour", "घंटे"), ("minute", "मिनट"), ("second", "सेकंड")) if lang == "hi" else (("hour", "hour"), ("minute", "minute"), ("second", "second"))
    for val, (en, hi) in zip((h, m, s), names):
        if val:
            parts.append(f"{val} {hi if lang == 'hi' else en + ('s' if val != 1 else '')}")
    return " ".join(parts)


# ---------------------------------------------------------------- conversion

_LENGTH = {"m": 1, "meter": 1, "meters": 1, "metre": 1, "metres": 1, "km": 1000, "kilometer": 1000, "kilometers": 1000,
           "kilometre": 1000, "kilometres": 1000, "cm": 0.01, "centimeter": 0.01, "centimeters": 0.01, "mm": 0.001,
           "mile": 1609.344, "miles": 1609.344, "foot": 0.3048, "feet": 0.3048, "ft": 0.3048, "inch": 0.0254,
           "inches": 0.0254, "yard": 0.9144, "yards": 0.9144}
_MASS = {"kg": 1, "kilogram": 1, "kilograms": 1, "kilo": 1, "kilos": 1, "g": 0.001, "gram": 0.001, "grams": 0.001,
         "mg": 1e-6, "pound": 0.45359237, "pounds": 0.45359237, "lb": 0.45359237, "lbs": 0.45359237,
         "ounce": 0.0283495, "ounces": 0.0283495, "oz": 0.0283495, "ton": 1000, "tons": 1000, "tonne": 1000, "tonnes": 1000}
_VOLUME = {"l": 1, "liter": 1, "liters": 1, "litre": 1, "litres": 1, "ml": 0.001, "gallon": 3.78541, "gallons": 3.78541,
           "cup": 0.236588, "cups": 0.236588}
_TEMP = {"c": "c", "celsius": "c", "centigrade": "c", "f": "f", "fahrenheit": "f", "k": "k", "kelvin": "k"}
_FAMILIES = (_LENGTH, _MASS, _VOLUME)

_CUR_CODES = {"usd", "inr", "eur", "gbp", "jpy", "aud", "cad", "chf", "cny", "aed", "sgd", "nzd", "zar", "sar", "krw", "thb"}
_CUR_NAMES = {"dollar": "usd", "dollars": "usd", "rupee": "inr", "rupees": "inr", "euro": "eur", "euros": "eur",
              "yen": "jpy", "dirham": "aed", "dirhams": "aed", "pound": "gbp", "pounds": "gbp", "yuan": "cny"}

CONVERT_RE = re.compile(r"(?:convert\s+)?(-?\d+(?:\.\d+)?)\s*°?\s*([a-z/]+)\s+(?:to|in|into)\s+([a-z/]+)")


def _currency(tok: str, other: str):
    if tok in _CUR_CODES:
        return tok.upper()
    if tok in _CUR_NAMES and (tok not in ("pound", "pounds") or other in _CUR_CODES or other in _CUR_NAMES):
        return _CUR_NAMES[tok].upper()
    return None


def _fetch_json(url: str):
    if not url.startswith("https://"):
        raise ValueError("only https addresses are allowed")
    req = urllib.request.Request(url, headers={"User-Agent": "JarvisAssistant/1.0"})
    with urllib.request.urlopen(req, timeout=8) as r:
        return json.load(r)


def convert_units(text: str):
    """Returns ('unit'|'currency'|None, value, from, to) or None. Currency conversion is done by the caller."""
    m = CONVERT_RE.search(text.lower())
    if not m:
        return None
    val, a, b = float(m.group(1)), m.group(2), m.group(3)
    ca, cb = _currency(a, b), _currency(b, a)
    if ca and cb:
        return ("currency", val, ca, cb)
    if a in _TEMP and b in _TEMP:
        c = val if _TEMP[a] == "c" else (val - 32) * 5 / 9 if _TEMP[a] == "f" else val - 273.15
        out = c if _TEMP[b] == "c" else c * 9 / 5 + 32 if _TEMP[b] == "f" else c + 273.15
        return ("unit", val, a, b, out)
    for fam in _FAMILIES:
        if a in fam and b in fam:
            return ("unit", val, a, b, val * fam[a] / fam[b])
    return None


def convert_currency(amount: float, src: str, dst: str) -> float:
    data = _fetch_json(f"https://api.frankfurter.dev/v1/latest?base={src}&symbols={dst}")
    return amount * data["rates"][dst]


def fmt_number(x: float) -> str:
    return f"{x:,.2f}".rstrip("0").rstrip(".") if abs(x) < 1e12 else f"{x:.3g}"


# ---------------------------------------------------------------- weather

_WMO = [
    ((0,), ("clear sky", "साफ आसमान")), ((1, 2, 3), ("partly cloudy", "आंशिक बादल")), ((45, 48), ("foggy", "कोहरा")),
    ((51, 53, 55, 56, 57), ("drizzle", "बूंदाबांदी")), ((61, 63, 65, 66, 67), ("rain", "बारिश")),
    ((71, 73, 75, 77), ("snow", "बर्फबारी")), ((80, 81, 82), ("rain showers", "बौछारें")), ((95, 96, 99), ("thunderstorm", "आंधी-तूफान")),
]


def weather(city: str, lang: str) -> str:
    q = urllib.parse.urlencode({"name": city, "count": 1, "language": "hi" if lang == "hi" else "en"})
    hits = _fetch_json(f"https://geocoding-api.open-meteo.com/v1/search?{q}").get("results") or []
    if not hits:
        raise LookupError(city)
    g = hits[0]
    q = urllib.parse.urlencode({
        "latitude": g["latitude"], "longitude": g["longitude"], "timezone": "auto",
        "current": "temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m",
    })
    cur = _fetch_json(f"https://api.open-meteo.com/v1/forecast?{q}")["current"]
    code = cur.get("weather_code", 0)
    desc = next((d[1 if lang == "hi" else 0] for codes, d in _WMO if code in codes), "")
    place = ", ".join(x for x in (g.get("name"), g.get("country")) if x)
    if lang == "hi":
        return f"{place}: {round(cur['temperature_2m'])}°C, {desc}, नमी {cur['relative_humidity_2m']}%, हवा {round(cur['wind_speed_10m'])} किमी/घंटा।"
    return f"{place}: {round(cur['temperature_2m'])}°C, {desc}, humidity {cur['relative_humidity_2m']}%, wind {round(cur['wind_speed_10m'])} km/h."


# ---------------------------------------------------------------- fun

JOKES = {
    "en": [
        "Why do programmers prefer dark mode? Because light attracts bugs.",
        "I told my computer I needed a break. It said no problem and went to sleep.",
        "Why did the developer go broke? He used up all his cache.",
        "There are only 10 kinds of people: those who understand binary and those who don't.",
        "A SQL query walks into a bar, walks up to two tables and asks: can I join you?",
    ],
    "hi": [
        "टीचर: बताओ सबसे तेज़ क्या चलता है? छात्र: मोबाइल का डेटा, खत्म भी तेज़ होता है।",
        "पत्नी: सुनो, मैं कैसी लग रही हूँ? पति: वाईफाई की तरह, पास हो तो बहुत अच्छी।",
        "बेटा: पापा, परीक्षा में नंबर कम आए। पापा: कोई बात नहीं, अगली बार कम पढ़ना, नंबर अपने आप बढ़ जाएँगे।",
        "डॉक्टर: आपको आराम चाहिए। मरीज़: वो तो ऑफिस में बॉस के आने पर ही मिलता है।",
    ],
}


def joke(lang: str) -> str:
    return random.choice(JOKES["hi" if lang == "hi" else "en"])
