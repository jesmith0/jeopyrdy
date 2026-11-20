"""Cross-platform text-to-speech via whichever system speech command is installed.

Each backend is (argv, use_stdin). Text goes over stdin where the command
supports it so clue text can never be mistaken for a command-line option.
"""

import logging
import shutil
import subprocess
import sys

log = logging.getLogger(__name__)


def windows_sapi_script(null_output=False):
    """PowerShell script that speaks stdin via System.Speech.

    null_output synthesizes without an audio device (used by tests on CI runners).
    """
    return (
        "[Console]::InputEncoding = [System.Text.Encoding]::UTF8; "
        "Add-Type -AssemblyName System.Speech; "
        "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
        + ("$s.SetOutputToNull(); " if null_output else "")
        + "$s.Speak([Console]::In.ReadToEnd())"
    )


def _candidates(platform):
    if platform == "darwin":
        return [(["say", "-f", "-"], True)]
    if platform == "win32":
        return [(["powershell", "-NoProfile", "-Command", windows_sapi_script()], True)]
    return [
        (["espeak-ng", "--stdin"], True),
        (["espeak", "--stdin"], True),
        # spd-say returns immediately unless told to wait, which would break
        # the game's "still speaking" check.
        (["spd-say", "--wait"], False),
    ]


def find_backend(platform=None):
    """Return the first available (argv, use_stdin) backend, or None."""
    for argv, use_stdin in _candidates(platform or sys.platform):
        path = shutil.which(argv[0])
        if path:
            return [path, *argv[1:]], use_stdin
    return None


BACKEND = find_backend()
AVAILABLE = BACKEND is not None


def speak(text, backend=None):
    """Start speaking text in the background. Returns the Popen, or None if speech is unavailable."""
    backend = backend or BACKEND
    if not backend:
        return None

    argv, use_stdin = backend
    text = " ".join(str(text).split())

    try:
        if use_stdin:
            proc = subprocess.Popen(argv, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            proc.stdin.write(text.encode("utf-8"))
            proc.stdin.close()
        else:
            proc = subprocess.Popen([*argv, text.lstrip("-")], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except OSError as e:
        log.warning("text-to-speech failed: %s", e)
        return None

    return proc
