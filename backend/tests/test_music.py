import json
import os

import pytest

from jarvis import brain, commands, config, engine, music, settings


@pytest.fixture(autouse=True)
def isolate(tmp_path, monkeypatch):
    played, opened = [], []
    monkeypatch.setattr(config, "DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setattr(config, "MUSIC_DIR", "")
    monkeypatch.setattr(brain, "claude_enabled", lambda: False)
    monkeypatch.setattr(commands.webbrowser, "open", lambda u: opened.append(u))
    monkeypatch.setattr(engine.webbrowser, "open", lambda u: opened.append(u))
    monkeypatch.setattr(music, "_open_file", lambda p: played.append(p))
    monkeypatch.setattr(commands, "_first_video", lambda q: "abcdefghijk")
    engine._sessions.clear()
    return played, opened


@pytest.fixture
def songs(tmp_path):
    root = tmp_path / "Music"
    (root / "Rock").mkdir(parents=True)
    for rel in ["Believer.mp3", "Rock/Believer Live.mp3", "Shape of You.mp3", "Rock/Shape of Water.m4a", "notes.txt"]:
        (root / rel).write_bytes(b"x")
    return str(root)


def ask(text, lang="en", sid="m"):
    return engine.handle(sid, text, lang)


def test_asks_for_the_folder_once_saves_it_and_plays(isolate, songs):
    played, opened = isolate
    r = ask("play believer")
    assert "Where are your songs" in r.reply and not played and not opened
    r = ask(songs)
    assert r.reply.startswith(f"Saved {os.path.abspath(songs)} as your music folder.") and "Playing Believer" in r.reply
    assert played == [os.path.join(songs, "Believer.mp3")]
    assert json.load(open(os.path.join(config.DATA_DIR, "settings.json")))["music_dir"] == os.path.abspath(songs)

    engine._sessions.clear()  # a new visit: no question any more
    assert "Playing Shape of You" in ask("play shape of you").reply
    assert played[-1] == os.path.join(songs, "Shape of You.mp3") and not opened


def test_wrong_folder_is_refused_and_asked_again(isolate, songs, tmp_path):
    played, _ = isolate
    ask("play song believer")
    assert "can't find the folder" in ask(str(tmp_path / "nope")).reply
    assert "Playing Believer" in ask(songs).reply and len(played) == 1
    assert "can't find the folder" in ask("set music folder to " + str(tmp_path / "also-nope")).reply
    assert "can't find the folder" in ask("relative\\path").reply  # only absolute folders count


def test_skip_uses_youtube_and_remembers_it(isolate, songs):
    played, opened = isolate
    ask("play believer")
    ask("skip")
    assert opened == ["https://www.youtube.com/watch?v=abcdefghijk"] and not played
    n = len(opened)
    assert "Where are your songs" not in ask("play shape of you").reply and len(opened) == n + 1
    assert "Saved" in ask("set music folder to " + songs).reply  # switches back to the folder
    ask("play shape of you")
    assert played == [os.path.join(songs, "Shape of You.mp3")]


def test_song_not_in_the_folder_falls_back_to_youtube(isolate, songs):
    played, opened = isolate
    ask("set music folder to " + songs)
    r = ask("play thunderstruck")
    assert "couldn't find thunderstruck in your music folder" in r.reply and "Playing thunderstruck" in r.reply
    assert not played and "youtube.com" in opened[-1]


def test_several_matches_ask_for_a_number(isolate, songs):
    played, _ = isolate
    ask("set music folder to " + songs)
    r = ask("play shape")
    assert "2 matching songs" in r.reply and "1. Shape of You" in r.reply and "2. Shape of Water" in r.reply
    assert "number from 1 to 2" in ask("seven").reply
    assert "Playing Shape of Water" in ask("2").reply
    assert played == [os.path.join(songs, "Rock", "Shape of Water.m4a")]


def test_exact_name_wins_over_longer_names(isolate, songs):
    played, _ = isolate
    ask("set music folder to " + songs)
    ask("play believer")  # "Believer" and "Believer Live" both match: the exact name plays at once
    assert played == [os.path.join(songs, "Believer.mp3")]


def test_a_new_command_abandons_the_question(isolate, songs):
    played, _ = isolate
    ask("play believer")
    assert "time is" in ask("what is the time").reply.lower()
    assert ask("play song").reply.startswith("Which song")  # no leftover state, and no name means ask which
    assert not played


def test_cancel_and_show_and_hindi(isolate, songs):
    assert ask("play believer").reply.startswith("Where")
    assert ask("cancel").reply == "Okay, cancelled."
    assert "No music folder is saved" in ask("where is my music folder").reply
    r = ask("गाना बजाओ believer", "hi")
    assert "गाने कहाँ हैं" in r.reply
    assert "सेव कर दिया" in ask(songs, "hi").reply
    assert music._query_from("गाना बजाओ believer") == "believer"  # no stray "ओ" left from "बजाओ"
    assert songs.lower().replace("/", "\\") in ask("where is my music folder").reply.lower().replace("/", "\\")


def test_env_music_dir_is_the_default(isolate, songs, monkeypatch):
    played, _ = isolate
    monkeypatch.setattr(config, "MUSIC_DIR", songs)
    ask("play shape of you")
    assert played == [os.path.join(songs, "Shape of You.mp3")]


def test_spoken_path_and_search_rules(songs):
    assert music.spoken_path("d colon backslash my music backslash rock") == "d:\\my music\\rock"
    assert music.spoken_path('"D:\\Music"') == "D:\\Music"
    assert [os.path.basename(p) for p in music.find(songs, "shape of")] == ["Shape of You.mp3", "Shape of Water.m4a"]
    assert music.find(songs, "notes") == []  # only audio files
    assert music.find(songs, "") == []


def test_saving_the_music_folder_keeps_the_assistant_name(songs):
    settings.set_name("Friday")
    settings.set_music(songs, False)
    assert settings.get_name() == "Friday" and settings.get_music() == (songs, False)
    settings.set_name("Nova")
    assert settings.get_music() == (songs, False)
