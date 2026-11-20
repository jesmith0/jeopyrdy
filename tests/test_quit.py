"""The real main loop must exit on quit requests (#31).

Each test runs app/main.py's main() in a subprocess, so a broken quit path
shows up as a timeout instead of hanging the test run, and pygame.quit()
doesn't tear down the display the other tests share.
"""

import os
import signal
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

APP_DIR = Path(__file__).resolve().parent.parent / "app"

# Runs main() offline: a fake one-clue library instead of j-archive, and an
# optional quit event posted once the menu is up.
RUNNER = """
import sys
sys.path.insert(0, {app_dir!r})
import pygame
import constants
import util
import main

constants.TEMP_PATH = {temp_dir!r}

def fake_lib_setup():
    print("READY", flush=True)
    if {post_event!r} == "quit":
        pygame.event.post(pygame.event.Event(pygame.QUIT))
    elif {post_event!r} == "escape":
        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))
    elif {post_event!r} == "library_error":
        raise util.LibraryError("no complete game found in 10 attempts")
    return [None, ["SHOW #1 - TEST"]]

util.lib_setup = fake_lib_setup
util.get_buzzers = lambda: None
main.run()
print("EXITED", flush=True)
"""

TIMEOUT = 60


def start(post_event=None, temp_dir=None):
    env = dict(os.environ, SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy")
    # never touch the real app/res/temp from tests
    temp_dir = str(temp_dir or tempfile.mkdtemp())
    code = RUNNER.format(app_dir=str(APP_DIR), post_event=post_event, temp_dir=temp_dir)
    return subprocess.Popen(
        [sys.executable, "-c", code], env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    )


def finish(proc):
    try:
        out, _ = proc.communicate(timeout=TIMEOUT)
    except subprocess.TimeoutExpired:
        proc.kill()
        out, _ = proc.communicate()
        pytest.fail(f"game did not quit within {TIMEOUT}s:\n{out}")
    return out


def wait_until_ready(proc):
    for line in proc.stdout:
        if line.strip() == "READY":
            return
    pytest.fail("game exited before reaching the menu:\n" + finish(proc))


@pytest.mark.parametrize("event", ["quit", "escape"])
def test_quit_event_and_escape_exit_main_loop(event):
    out = finish(start(post_event=event))
    assert "EXITED" in out


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX signals")
@pytest.mark.parametrize("sig", [signal.SIGINT, signal.SIGTERM])
def test_ctrl_c_and_sigterm_exit_main_loop(sig):
    proc = start()
    wait_until_ready(proc)
    proc.send_signal(sig)

    out = finish(proc)
    assert "EXITED" in out
    assert "Traceback" not in out


def test_library_failure_exits_with_message_not_traceback():
    proc = start(post_event="library_error")
    out = finish(proc)

    assert proc.returncode == 1
    assert "Could not load a game from j-archive: no complete game found" in out
    assert "Traceback" not in out


def leave_downloads(temp_dir):
    for name in ("ja0.jpg", "wiki3.png", "wiki12.jpeg"):
        (temp_dir / name).write_bytes(b"image")


@pytest.mark.parametrize("event", ["quit", "library_error"])
def test_exit_deletes_downloaded_images(tmp_path, event):
    leave_downloads(tmp_path)
    finish(start(post_event=event, temp_dir=tmp_path))
    assert list(tmp_path.iterdir()) == []


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX signals")
def test_ctrl_c_deletes_downloaded_images(tmp_path):
    leave_downloads(tmp_path)
    proc = start(temp_dir=tmp_path)
    wait_until_ready(proc)
    proc.send_signal(signal.SIGINT)
    finish(proc)
    assert list(tmp_path.iterdir()) == []
