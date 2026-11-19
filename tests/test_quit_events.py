"""Regression test: window close / Ctrl+C / SIGTERM (pygame.QUIT) must exit main()."""
import pygame

import main as game_main


class _FakeMenu:
    def __init__(self, *args, **kwargs):
        pass

    def set_game_date(self, *args):
        pass

    def update(self, *args):
        return (True, None, False, False, False)

    def update_buzzers(self, *args):
        pass

    def get_new_game(self):
        return False


def test_quit_event_exits_main_loop(monkeypatch):
    calls = {"get": 0, "quit": 0}

    def fake_get(*args, **kwargs):
        calls["get"] += 1
        # Guard so a regression fails fast instead of hanging the suite.
        if calls["get"] > 5:
            raise RuntimeError("main loop did not exit on pygame.QUIT")
        if calls["get"] == 1:
            return [pygame.event.Event(pygame.QUIT)]
        return []

    monkeypatch.setattr(pygame.event, "get", fake_get)
    monkeypatch.setattr(pygame, "quit", lambda: calls.__setitem__("quit", calls["quit"] + 1))
    monkeypatch.setattr(game_main.util, "get_buzzers", lambda: [])
    monkeypatch.setattr(game_main.util, "lib_setup", lambda: (object(), ("2026-01-01",)))
    monkeypatch.setattr(game_main.util, "dtf", lambda: None)
    monkeypatch.setattr(game_main.m, "Menu", _FakeMenu)

    game_main.main()

    assert calls["quit"] == 1
