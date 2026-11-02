import pytest

from jarvis import commands, engine


@pytest.fixture(autouse=True)
def no_side_effects(monkeypatch):
    opened, ran = [], []
    monkeypatch.setattr(commands.webbrowser, "open", lambda u: opened.append(u))
    monkeypatch.setattr(engine.webbrowser, "open", lambda u: opened.append(u))
    monkeypatch.setattr(commands.subprocess, "Popen", lambda *a, **k: ran.append(a))
    monkeypatch.setattr(commands, "_first_video", lambda q: "abcdefghijk")
    monkeypatch.setattr(engine.brain, "claude_enabled", lambda: False)
    monkeypatch.setattr(engine.brain, "ask_wikipedia", lambda q, l: None)
    engine._sessions.clear()
    return opened, ran


def ask(text, lang="en", sid="t"):
    return engine.handle(sid, text, lang)


def test_open_youtube_en_and_hi(no_side_effects):
    opened, _ = no_side_effects
    assert ask("open youtube").action["name"] == "YouTube"
    assert ask("यूट्यूब खोलें", "hi").action["name"] == "YouTube"
    assert opened == ["https://www.youtube.com"] * 2


def test_play_song_opens_the_video_itself_so_it_starts(no_side_effects, monkeypatch):
    opened, _ = no_side_effects
    r = ask("play online believer")
    assert opened == ["https://www.youtube.com/watch?v=abcdefghijk"] and r.action["url"] == opened[0]
    monkeypatch.setattr(commands, "_first_video", lambda q: None)  # YouTube unreachable: show the search instead
    ask("play online believer")
    assert opened[-1].startswith("https://www.youtube.com/results?search_query=believer")


def test_youtube_search(no_side_effects):
    opened, _ = no_side_effects
    ask("youtube videos of comedy")
    assert opened[-1].endswith("comedy")


def test_shutdown_needs_confirmation(no_side_effects):
    _, ran = no_side_effects
    r = ask("shutdown")
    assert r.on_confirm and not ran
    ask("no")
    assert not ran
    ask("shutdown")
    ask("yes")
    assert ran and "shutdown" in ran[0][0][0]


def test_hindi_confirm(no_side_effects):
    _, ran = no_side_effects
    ask("सिस्टम बंद करो", "hi")
    ask("हाँ", "hi")
    assert ran


def test_math():
    assert "8" in ask("what is 5 plus 3").reply
    assert "12" in ask("what is 3 times 4").reply
    assert commands._try_math("__import__('os')") is None


def test_exit_and_time():
    assert ask("bye").action == {"type": "sleep"}
    assert "time" in ask("what is the time").reply.lower()


def test_fallback_goes_to_google(no_side_effects):
    opened, _ = no_side_effects
    r = ask("restaurants near me")
    assert opened and "google.com/search" in opened[0] and r.action["name"] == "Google"


def test_actions():
    assert ask("draw pie chart").action["kind"] == "pie"
    assert "Who should I send" in ask("send email").reply  # conversational email flow (mail.py)
    assert ask("click my picture").action["type"] == "camera"
    assert ask("play song").reply.startswith("Which song")
