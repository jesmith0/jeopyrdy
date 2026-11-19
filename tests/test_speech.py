import sys

import pytest

import speech


@pytest.fixture
def only_commands(monkeypatch):
    """Pretend only the given commands are installed."""
    def install(*names):
        monkeypatch.setattr(speech.shutil, "which",
                            lambda cmd: "/usr/bin/" + cmd if cmd in names else None)
    return install


def test_no_backend_when_nothing_installed(only_commands):
    only_commands()
    for platform in ("darwin", "linux", "win32"):
        assert speech.find_backend(platform) is None


def test_speak_without_backend_returns_none(only_commands, monkeypatch):
    monkeypatch.setattr(speech, "BACKEND", None)
    assert speech.speak("This is a clue") is None


@pytest.mark.parametrize(("platform", "installed", "expected"), [
    ("darwin", ["say"], "say"),
    ("win32", ["powershell"], "powershell"),
    ("linux", ["espeak-ng", "espeak", "spd-say"], "espeak-ng"),
    ("linux", ["espeak", "spd-say"], "espeak"),
    ("linux", ["spd-say"], "spd-say"),
])
def test_backend_selection(only_commands, platform, installed, expected):
    only_commands(*installed)
    argv, _ = speech.find_backend(platform)
    assert argv[0] == "/usr/bin/" + expected


def test_spd_say_waits_for_speech_to_finish(only_commands):
    only_commands("spd-say")
    argv, use_stdin = speech.find_backend("linux")
    assert "--wait" in argv and not use_stdin


def test_speak_sends_text_over_stdin():
    backend = ([sys.executable, "-c", "import sys; sys.exit(sys.stdin.read() != 'What is -40 degrees?')"], True)
    proc = speech.speak("What is\n-40   degrees?", backend)
    assert proc.wait(timeout=10) == 0


def test_speak_survives_missing_command():
    assert speech.speak("hello", (["/nonexistent/say"], False)) is None


# Runs the platform's real speech command (say / PowerShell / espeak-ng) where
# one is installed, e.g. on the macOS, Windows and Linux CI runners.
@pytest.mark.skipif(not speech.AVAILABLE, reason="no speech backend installed")
def test_real_backend_speaks_non_ascii_text():
    # Non-ASCII clue text used to fail with a Unicode decode error (#8).
    proc = speech.speak("Björk sang about the café in São Paulo, señor.")
    assert proc is not None
    assert proc.wait(timeout=120) == 0
