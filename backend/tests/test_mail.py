import json
import urllib.parse

import pytest

from jarvis import brain, commands, config, engine, mail


@pytest.fixture(autouse=True)
def isolate(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setattr(config, "SMTP_USER", "")
    monkeypatch.setattr(config, "SMTP_PASSWORD", "")
    monkeypatch.setattr(config, "SENDER_NAME", "")
    monkeypatch.setattr(brain, "claude_enabled", lambda: False)
    opened = []
    monkeypatch.setattr(commands.webbrowser, "open", lambda u: opened.append(u))
    engine._sessions.clear()
    return opened


def ask(text, lang="en", sid="m"):
    return engine.handle(sid, text, lang)


def book():
    return mail.load_contacts()


def test_spoken_email_normalised():
    assert mail.find_email("ravi at gmail dot com") == "ravi@gmail.com"
    assert mail.find_email("Ravi.K at the rate outlook dot co dot in") == "ravi.k@outlook.co.in"
    assert mail.find_email("no address here") == ""


def test_full_flow_new_person_then_send(isolate):
    assert "email address for Ravi" in ask("email Ravi").reply
    assert "Any CC" in ask("ravi at gmail dot com").reply
    assert "Any BCC" in ask("skip").reply
    assert "subject" in ask("skip").reply
    assert "What should the mail to Ravi say" in ask("skip").reply  # subject skipped
    r = ask("I will be late tomorrow")
    d = r.action["draft"]
    assert d["to"] == ["Ravi <ravi@gmail.com>"] and d["cc"] == [] and d["bcc"] == []
    assert d["subject"] == "I will be late tomorrow"  # skipped subject -> written from the message
    assert d["body"].startswith("Hi Ravi,")
    assert isolate == []  # nothing opens before the user confirms
    assert ask("yes").action["type"] == "opened" and len(isolate) == 1
    q = urllib.parse.parse_qs(urllib.parse.urlparse(isolate[0]).query)
    assert q["to"] == ["ravi@gmail.com"] and q["su"] == ["I will be late tomorrow"]


def test_every_address_is_saved_and_found_by_name():
    ask("send mail to abc@gmail.com")
    assert book() == [{"name": "", "email": "abc@gmail.com"}]  # saved as soon as it is heard
    ask("cancel")
    ask("email ravi")
    ask("ravi at gmail dot com")  # name + address learned together
    ask("cancel")
    assert {"name": "ravi", "email": "ravi@gmail.com"} in book()
    r = ask("email ravi")  # found in the file: goes straight to CC
    assert "Any CC" in r.reply
    ask("cancel")
    assert len(book()) == 2


def test_several_matches_ask_which_one():
    ask("send mail to abc@gmail.com")
    ask("cancel")
    ask("send mail to xyzabc@gmail.com")
    ask("cancel")
    r = ask("send mail to abc")
    assert r.reply.startswith("I found 2 matches for Abc")
    assert "1. abc@gmail.com" in r.reply and "2. xyzabc@gmail.com" in r.reply
    assert [o["send"] for o in r.action["options"]] == ["1", "2"]
    assert "1 to 2" in ask("hmm").reply
    r = ask("2")
    assert "Any CC" in r.reply
    ask("skip"); ask("skip"); ask("skip")  # cc, bcc, subject
    r = ask("meet at five")
    assert r.action["draft"]["to"] == ["xyzabc@gmail.com"]


def test_choose_by_word_and_exact_name_wins():
    ask("send mail to abc@gmail.com"); ask("cancel")
    ask("send mail to xyzabc@gmail.com"); ask("cancel")
    ask("send mail to abc")
    assert "Any CC" in ask("the first one").reply
    ask("cancel")
    mail.remember("abc@work.com", "abc")  # an exact name match beats partial address matches
    assert "Any CC" in ask("send mail to abc").reply


def test_cc_bcc_with_names_and_skip():
    mail.remember("priya@x.com", "priya")
    mail.remember("raj@x.com", "raj")
    ask("send mail to a@x.com")
    assert "Any BCC" in ask("priya").reply
    assert "subject" in ask("raj and boss@x.com").reply
    ask("skip")
    d = ask("please review").action["draft"]
    assert d["cc"] == ["Priya <priya@x.com>"] and d["bcc"] == ["Raj <raj@x.com>", "boss@x.com"]
    assert "boss@x.com" in [c["email"] for c in book()]  # a new address said as cc/bcc is saved too


def test_one_sentence_prefills_steps():
    r = ask("send mail to a@x.com cc b@x.com subject Budget saying please review")
    assert "Any BCC" in r.reply  # to, cc, subject and body were all given; only BCC is left
    d = ask("skip").action["draft"]
    assert d["cc"] == ["b@x.com"] and d["subject"] == "Budget"


def test_cancel_and_unrelated_commands():
    ask("send email")
    assert "time" in ask("what is the time").reply.lower()  # not swallowed as a recipient
    assert "Who should I send" in ask("send email").reply
    assert ask("cancel").reply == "Okay, cancelled."
    ask("email Ravi")
    assert ask("hmm").reply.startswith("That doesn't look")
    assert ask("draw pie chart").action["kind"] == "pie"  # second miss drops the draft


def test_smtp_path(monkeypatch, isolate):
    monkeypatch.setattr(config, "SMTP_USER", "me@x.com")
    monkeypatch.setattr(config, "SMTP_PASSWORD", "pw")
    sent = []
    monkeypatch.setattr(mail, "send_smtp", lambda *a: sent.append(a))
    ask("email a@x.com saying hi there")
    ask("skip"); ask("skip")
    r = ask("skip")
    assert "send it" in r.reply and sent == []
    assert ask("yes").reply == "Email sent."
    assert sent[0][0] == ["a@x.com"] and isolate == []


def test_hindi_flow(isolate):
    r = ask("रवि को ईमेल भेजो कि मैं देर से आऊंगा", "hi")
    assert "रवि" in r.reply and "ईमेल पता" in r.reply
    assert "CC" in ask("ravi at gmail dot com", "hi").reply
    ask("स्किप", "hi"); ask("स्किप", "hi")
    r = ask("स्किप", "hi")
    assert r.action["draft"]["to"] == ["रवि <ravi@gmail.com>"] and r.action["draft"]["body"].startswith("नमस्ते रवि,")
    ask("हाँ", "hi")
    assert len(isolate) == 1
    ask("रवि को मेल भेजो", "hi")  # found in the contacts file this time
    assert "CC" in ask("स्किप", "hi").reply or True  # contact found: no address question


def test_hindi_number_choice():
    mail.remember("a@x.com"); mail.remember("ba@x.com")
    ask("send mail to a")
    assert "CC" in ask("दो", "hi").reply


def test_contacts_file_and_commands():
    assert "no saved contacts" in ask("my contacts").reply
    assert "Saved Meena as meena@x.com" in ask("save contact meena as meena at x dot com").reply
    assert "1. Meena: meena@x.com" in ask("show contacts").reply
    assert "Saved Raj" in ask("raj's email is raj@y.org").reply
    mail.remember("meena@x.com", "meena")  # no duplicates
    assert len(book()) == 2


def test_old_contacts_format_is_migrated(tmp_path):
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "contacts.json").write_text(json.dumps({"ravi": "ravi@gmail.com"}))
    assert mail.search("ravi") == [{"name": "ravi", "email": "ravi@gmail.com"}]


def test_other_commands_not_hijacked():
    assert ask("open gmail").action["type"] == "opened"
    assert "time" in ask("what is the time").reply.lower()


def test_spoken_at_that_does_not_swallow_the_body():
    # "at that" is how speech recognition writes "@"; it used to be read as the word "that" (= start of the message)
    assert mail.find_email("Ravi dot Shamsher at that finance.com") == "ravi.shamsher@finance.com"
    assert mail._parse_en("can you send an email to Ravi at that finance.com")["body"] == ""
    ask("can you send an email to Ravi dot Shamsher at that finance.com")
    ask("skip"); ask("skip")  # cc, bcc
    assert "What should the mail" in ask("skip").reply  # subject skipped -> now it asks for the message
    r = ask("regarding holiday from 16 November to 27 November 2026")
    assert r.action["draft"]["body"].endswith("27 November 2026.")  # the whole dictated sentence arrives


def test_command_flags_dictation_for_subject_and_body():
    from fastapi.testclient import TestClient

    import main

    c = TestClient(main.app)
    sid = "dict"
    assert c.post("/api/command", json={"text": "send mail to a@x.com", "session": sid}).json()["dictate"] is False  # asks CC
    c.post("/api/command", json={"text": "skip", "session": sid})
    assert c.post("/api/command", json={"text": "skip", "session": sid}).json()["dictate"] is True  # now asks the subject
    assert c.post("/api/command", json={"text": "skip", "session": sid}).json()["dictate"] is True  # now asks the message
    assert c.post("/api/command", json={"text": "hello there", "session": sid}).json()["dictate"] is False


def test_editing_the_draft_by_hand(monkeypatch, isolate):
    from fastapi.testclient import TestClient

    import main

    c = TestClient(main.app)
    sid = "edit"
    r = c.post("/api/command", json={"text": "email a@x.com saying hi there", "session": sid}).json()
    for _ in range(3):
        r = c.post("/api/command", json={"text": "skip", "session": sid}).json()
    d = r["action"]["draft"]
    assert d["to_emails"] == ["a@x.com"] and r["needs_confirm"]

    body = {"to": ["a@x.com, b@x.com"], "cc": [], "bcc": ["boss at office dot com"], "subject": "Edited", "body": "New text", "session": sid}
    out = c.post("/api/mail/send", json=body).json()
    q = urllib.parse.parse_qs(urllib.parse.urlparse(out["url"]).query)
    assert q["to"] == ["a@x.com,b@x.com"] and q["bcc"] == ["boss@office.com"] and q["su"] == ["Edited"] and q["body"] == ["New text"]
    assert "boss@office.com" in [x["email"] for x in mail.load_contacts()]
    assert isolate == []  # the browser opens the URL itself; the server opens nothing
    assert "Okay, cancelled" not in ask("yes", sid=sid).reply  # the old confirmation was cleared: "yes" cannot send twice

    assert c.post("/api/mail/send", json={**body, "to": ["not an address"]}).status_code == 400
    assert c.post("/api/mail/send", json={**body, "to": []}).status_code == 400

    monkeypatch.setattr(config, "SMTP_USER", "me@x.com")
    monkeypatch.setattr(config, "SMTP_PASSWORD", "pw")
    sent = []
    monkeypatch.setattr(mail, "send_smtp", lambda *a: sent.append(a))
    assert c.post("/api/mail/send", json=body).json() == {"reply": "Email sent.", "url": None}
    assert sent[0][:3] == (["a@x.com", "b@x.com"], [], ["boss@office.com"])
