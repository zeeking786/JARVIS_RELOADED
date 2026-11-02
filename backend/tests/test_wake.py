import pytest

from jarvis import brain, commands, config, engine, settings


@pytest.fixture(autouse=True)
def isolate(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setattr(brain, "claude_enabled", lambda: False)
    monkeypatch.setattr(commands.webbrowser, "open", lambda u: None)
    engine._sessions.clear()


def ask(text, lang="en"):
    return engine.handle("w", text, lang)


def test_wake_word_at_start_and_end():
    assert settings.split_wake("Hey Jarvis, good morning") == (True, "good morning")
    assert settings.split_wake("jarvis send an email") == (True, "send an email")
    assert settings.split_wake("Send an email Jarvis") == (True, "Send an email")
    assert settings.split_wake("ok jarvis what is the time please") == (True, "what is the time please")
    assert settings.split_wake("what is the time Jarvis please") == (True, "what is the time")
    assert settings.split_wake("Jarvis") == (True, "")
    assert settings.split_wake("हे जार्विस समय बताओ") == (True, "समय बताओ")
    assert settings.split_wake("jarvish open youtube") == (True, "open youtube")  # misheard spelling


def test_name_in_the_middle_or_absent_is_not_a_wake_word():
    assert settings.split_wake("tell jarvis about it later")[0] is False
    assert settings.split_wake("open youtube")[0] is False
    assert settings.split_wake("hello")[0] is False


def test_commands_work_through_the_wake_word():
    assert ask("Hey Jarvis good morning").reply == "Good morning! How can I help you?"
    assert ask("good night").reply.startswith("Good night!")
    assert ask("सुप्रभात", "hi").reply == "शुभ प्रभात! मैं आपकी क्या मदद करूँ?"
    assert "time is" in ask("what is the time Jarvis").reply.lower()
    assert ask("Jarvis").reply == "Yes? I'm listening."
    assert "Who should I send" in ask("send an email jarvis").reply


def test_rename_and_use_new_name():
    r = ask("change your name to friday")
    assert r.action == {"type": "rename", "name": "Friday"} and "Friday" in r.reply
    assert settings.get_name() == "Friday"
    assert "I am Friday" in ask("what is your name").reply
    assert "Friday" in ask("who are you").reply
    assert "morning" in ask("Hey Friday good morning").reply.lower()  # also good while the real hour is later
    assert ask("Fryday").reply == "Yes? I'm listening."  # one letter off still wakes a 6-letter name
    assert settings.split_wake("hey jarvis open youtube")[0] is False  # old name no longer wakes


def test_rename_variants_and_validation():
    assert ask("call yourself Nova").action["name"] == "Nova"
    assert ask("your name is jarvis prime").action["name"] == "Jarvis Prime"
    assert settings.split_wake("hey jarvis prime play music") == (True, "play music")
    assert ask("अपना नाम फ्राइडे रखो", "hi").action["name"] == "फ्राइडे"
    assert ask("change your name to " + "x" * 30).action is None  # too long
    assert settings.get_name() == "फ्राइडे"


def test_name_endpoint():
    from fastapi.testclient import TestClient

    import main

    c = TestClient(main.app)
    assert c.get("/api/health").json()["name"] == "Jarvis"
    assert c.post("/api/name", json={"name": "  Atlas "}).json() == {"name": "Atlas"}
    assert c.get("/api/health").json()["name"] == "Atlas"
    assert c.post("/api/name", json={"name": "<script>"}).status_code == 400
