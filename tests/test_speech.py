import re
import subprocess
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


def silent(backend, out_dir):
    """Same speech command, but synthesizing to a file/null instead of the speakers."""
    argv, use_stdin = backend
    name = re.split(r"[\\/]", argv[0])[-1].lower().removesuffix(".exe")

    if name == "say":
        return [argv[0], "-o", str(out_dir / "speech.aiff"), *argv[1:]], use_stdin
    if name in ("espeak-ng", "espeak"):
        return [argv[0], "-w", str(out_dir / "speech.wav"), *argv[1:]], use_stdin
    if name == "powershell":
        return [*argv[:-1], speech.windows_sapi_script(null_output=True)], use_stdin
    pytest.skip(f"{name} can't synthesize without playing audio")


# Run the platform's real speech engine (say / PowerShell / espeak-ng) where one
# is installed, e.g. on the CI runners, but silently: output goes to a file or
# a null device, never the speakers.
@pytest.mark.skipif(not speech.AVAILABLE, reason="no speech backend installed")
def test_real_backend_speaks_non_ascii_text(tmp_path):
    # Non-ASCII clue text used to fail with a Unicode decode error (#8).
    text = "Björk sang about the café in São Paulo, señor."
    argv, use_stdin = silent(speech.BACKEND, tmp_path)

    # Same invocation as speech.speak(), but keep stderr for diagnostics.
    result = subprocess.run(
        argv if use_stdin else [*argv, text],
        input=text.encode("utf-8") if use_stdin else None,
        capture_output=True,
        timeout=120,
    )
    assert result.returncode == 0, result.stderr.decode(errors="replace")

    # where the engine wrote audio to a file, it should contain speech
    for audio in tmp_path.iterdir():
        assert audio.stat().st_size > 1000


@pytest.mark.skipif(not speech.AVAILABLE, reason="no speech backend installed")
def test_real_backend_via_speak(tmp_path):
    proc = speech.speak("Who is Alex Trebek?", silent(speech.BACKEND, tmp_path))
    assert proc is not None
    assert proc.wait(timeout=120) == 0


def test_silent_variants_never_target_speakers(tmp_path):
    say = silent((["/usr/bin/say", "-f", "-"], True), tmp_path)[0]
    espeak = silent((["/usr/bin/espeak-ng", "--stdin"], True), tmp_path)[0]
    ps = silent((["C:\\PowerShell.EXE", "-NoProfile", "-Command", speech.windows_sapi_script()], True),
                tmp_path)[0]

    assert "-o" in say
    assert "-w" in espeak
    assert "SetOutputToNull" in ps[-1]
