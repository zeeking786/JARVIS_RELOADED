import io

import docx
import openpyxl
import pytest
from fastapi.testclient import TestClient

import main
from jarvis import brain, commands, config, documents, engine, offline, textutils, tools


@pytest.fixture(autouse=True)
def isolate(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "OUTPUT_DIR", str(tmp_path / "out"))
    monkeypatch.setattr(config, "DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setattr(brain, "claude_enabled", lambda: False)
    monkeypatch.setattr(commands.webbrowser, "open", lambda u: None)
    monkeypatch.setattr(engine.webbrowser, "open", lambda u: None)
    engine._sessions.clear()


def ask(text, lang="en", sid="o"):
    return engine.handle(sid, text, lang)


def attach(name, data, sid="o"):
    engine.add_attachment(sid, documents.load(name, data))


TEXT = (
    "Solar power is energy from the sun. Solar panels turn sunlight into electricity. "
    "Many homes now use solar panels to reduce electricity bills. The cost of solar power has fallen sharply. "
    "Wind energy is another clean source. Governments support solar power with subsidies. "
    "Batteries store solar energy for night use."
)


# ---------------------------------------------------------------- text tools


def test_summary_keywords_stats_find():
    s = textutils.summarize(TEXT, 2)
    assert len(s) == 2 and all(x in TEXT for x in s)
    assert "solar" in textutils.keywords(TEXT)[:3]
    assert textutils.stats(TEXT)["words"] > 40
    n, snips = textutils.find(TEXT, "SUBSIDIES")
    assert n == 1 and "subsidies" in snips[0]


def test_hindi_words_keep_matras():
    assert textutils.words("विश्वविद्यालय परियोजना") == ["विश्वविद्यालय", "परियोजना"]


def test_document_commands_on_attachment():
    attach("solar.txt", TEXT.encode())
    assert "Summary of solar.txt" in ask("summarise this file").reply
    assert "solar" in ask("what are the keywords").reply.lower()
    assert "words" in ask("word count").reply
    assert "subsidies" in ask("find subsidies in the document").reply
    assert "not found" in ask("find unicorn in the document").reply
    r = ask("read it")
    assert r.action == {"type": "read"} and r.reply.startswith("Solar power")
    r = ask("convert it to word")
    assert r.action["files"][0]["name"] == "solar.docx"
    assert docx.Document(f"{config.OUTPUT_DIR}/solar.docx").paragraphs[0].text.startswith("Solar power")
    assert "summarise" in ask("hmm what now please explain slowly").reply


def test_csv_to_xlsx_and_back():
    attach("data.csv", b"name,qty\npen,3\n")
    name = ask("convert to excel").action["files"][0]["name"]
    assert openpyxl.load_workbook(f"{config.OUTPUT_DIR}/{name}").active["B2"].value == 3
    attach("sheet.xlsx", open(f"{config.OUTPUT_DIR}/{name}", "rb").read())
    out = ask("convert sheet.xlsx to csv").action["files"][0]["name"]
    assert "pen,3" in open(f"{config.OUTPUT_DIR}/{out}", encoding="utf-8-sig").read()


def test_pdf_text_layer_and_image_message():
    from pypdf import PdfWriter

    buf = io.BytesIO()
    w = PdfWriter()
    w.add_blank_page(200, 200)
    w.write(buf)
    assert documents.load("blank.pdf", buf.getvalue()).kind == "pdf"
    attach("pic.png", b"\x89PNG....")
    assert "without AI" in ask("summarise").reply


# ---------------------------------------------------------------- templates


def test_template_forms_and_build():
    r = ask("write a leave application")
    assert r.action["type"] == "form" and r.action["template"] == "leave"
    assert ask("छुट्टी का आवेदन बनाओ", "hi").action["template"] == "leave"
    assert ask("create a word file").action["fields"][2]["default"] == "docx"
    assert ask("make an excel sheet").action["fields"][2]["default"] == "xlsx"

    c = TestClient(main.app)
    vals = dict(to="The Principal", name="Ravi", from_date="1 May", to_date="3 May", reason="fever")
    r = c.post("/api/make", json={"template": "leave", "values": vals, "lang": "en"}).json()
    name = r["files"][0]["name"]
    text = "\n".join(p.text for p in docx.Document(f"{config.OUTPUT_DIR}/{name}").paragraphs)
    assert "Ravi" in text and "fever" in text
    r = c.post("/api/make", json={"template": "leave", "values": vals, "lang": "hi"}).json()
    assert "अवकाश" in "\n".join(p.text for p in docx.Document(f"{config.OUTPUT_DIR}/{r['files'][0]['name']}").paragraphs)


def test_invoice_totals_and_validation():
    c = TestClient(main.app)
    r = c.post("/api/make", json={"template": "invoice", "values": {"number": "7", "client": "ACME", "items": "Pen, 10, 5\nBook, 2, 100"}})
    ws = openpyxl.load_workbook(f"{config.OUTPUT_DIR}/{r.json()['files'][0]['name']}").active
    assert [c_.value for c_ in ws[ws.max_row]][0] == "Total" and ws.cell(ws.max_row, 4).value == 250
    assert c.post("/api/make", json={"template": "invoice", "values": {"number": "7", "client": "x", "items": "nonsense"}}).status_code == 400
    assert c.post("/api/make", json={"template": "leave", "values": {}}).status_code == 400
    assert c.post("/api/make", json={"template": "nope", "values": {}}).status_code == 400


def test_blank_document_formats():
    c = TestClient(main.app)
    for fmt in ("docx", "txt", "md", "xlsx", "csv", "pptx", "html"):
        r = c.post("/api/make", json={"template": "blank", "values": {"title": "My Doc", "body": "a,b\n1,2", "format": fmt}})
        assert r.status_code == 200 and r.json()["files"][0]["name"] == f"My-Doc.{fmt}"


# ---------------------------------------------------------------- tools


def test_timers():
    r = ask("set a timer for 5 minutes")
    assert r.action == {"type": "timer", "seconds": 300, "label": "Timer finished"}
    r = ask("remind me in 2 hours to call mom")
    assert r.action["seconds"] == 7200 and r.action["label"] == "call mom"
    r = ask("10 मिनट का टाइमर लगाओ", "hi")
    assert r.action["seconds"] == 600
    assert "For how long" in ask("set a timer").reply


def test_tasks_and_notes_persist():
    ask("add task buy milk")
    ask("add call bank to my to-do list")
    assert "1. [ ] buy milk" in ask("show my tasks").reply
    assert "Marked done" in ask("done 1").reply
    assert "[x] buy milk" in ask("my tasks").reply
    assert "no task" in ask("done 9").reply
    ask("clear tasks")
    assert "no tasks" in ask("my tasks").reply
    ask("note: meeting at 5")
    ask("नोट करो दूध लाना", "hi")
    notes = ask("show my notes").reply
    assert "meeting at 5" in notes and "दूध लाना" in notes
    ask("clear notes")
    assert "no notes" in ask("my notes").reply


def test_units_and_currency(monkeypatch):
    assert ask("convert 5 km to miles").reply.startswith("5 km = 3.11 miles")
    assert "212" in ask("100 celsius to fahrenheit").reply
    assert "2.2" in ask("convert 1 kg to pounds").reply
    monkeypatch.setattr(tools, "_fetch_json", lambda url: {"rates": {"INR": 80.0}})
    assert ask("convert 10 usd to inr").reply == "10 USD = 800 INR"
    assert ask("5 dollars in rupees").reply == "5 USD = 400 INR"
    monkeypatch.setattr(tools, "_fetch_json", lambda url: (_ for _ in ()).throw(OSError()))
    assert "exchange rates" in ask("convert 10 usd to inr").reply


def test_weather(monkeypatch):
    def fake(url):
        if "geocoding" in url:
            return {"results": [{"latitude": 25, "longitude": 83, "name": "Varanasi", "country": "India"}]}
        return {"current": {"temperature_2m": 31.2, "relative_humidity_2m": 40, "weather_code": 2, "wind_speed_10m": 8.1}}

    monkeypatch.setattr(tools, "_fetch_json", fake)
    assert ask("what is the weather in Varanasi").reply == "Varanasi, India: 31°C, partly cloudy, humidity 40%, wind 8 km/h."
    assert "आंशिक बादल" in ask("वाराणसी का मौसम", "hi").reply
    assert "Which city" in ask("weather").reply


def test_fun_and_web(no_open=None):
    assert ask("tell me a joke").reply
    assert ask("flip a coin").reply in ("Heads.", "Tails.")
    assert "between" not in ask("random number between 5 and 5").reply and "5" in ask("random number between 5 and 5").reply
    r = ask("open github.com")
    assert r.action["url"] == "https://github.com"
    assert ask("search for python tutorials").action["name"] == "python tutorials"


def test_no_hijack_of_existing_commands():
    assert "time" in ask("what is the time").reply.lower()
    assert ask("open notepad").action["name"] == "Notepad" if commands.IS_WINDOWS else True
    assert ask("draw pie chart").action["kind"] == "pie"
    assert "8" in ask("what is 5 plus 3").reply


def test_document_studio_commands():
    for text in ("open document studio", "write a report with images", "create a proposal with pictures and tables",
                 "make a document including screenshots", "open the editor"):
        r = ask(text)
        assert r.action == {"type": "studio"} and "document studio" in r.reply, text
    assert ask("डॉक्यूमेंट स्टूडियो खोलो", "hi").action == {"type": "studio"}
    assert ask("write a leave letter").action["type"] == "form"  # templates are unchanged
    assert ask("create a word file").action["type"] == "form"
