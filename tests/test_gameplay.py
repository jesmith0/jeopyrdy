"""Play whole games headlessly by feeding keyboard events to the Game object.

Uses a synthetic clue library (no network) and replaces what a person would
otherwise have to check by playing: state transitions, scoring, round changes,
Daily Doubles, Final Jeopardy and the end screen.
"""

import types

import pygame
import pytest

import constants
import game as g
import state
import util

# keyboard map from util.gamify_input: [buzz/select, up, right, left, down]
# In the response screen, "left" marks correct and "right" marks incorrect.
P1 = {"buzz": 50, "up": 119, "right": 100, "left": 97, "down": 115}
P2 = {"buzz": 53, "up": 116, "right": 104, "left": 102, "down": 103}


def make_library():
    cats = [f"CATEGORY {i}" for i in range(13)]  # 6 + 6 + final
    clues = [f"Clue number {i}" for i in range(61)]  # 30 + 30 + final
    resps = [f"What is answer {i}?" for i in range(61)]
    res = [None] * 61
    return util.gen_lib_object([cats, clues, resps, res])


class Driver:
    def __init__(self, game):
        self.game = game

    def press(self, key):
        event = types.SimpleNamespace(type=pygame.KEYDOWN, key=key)
        self.game.update(util.gamify_input(event), event)

    def end_final_music(self):
        # what main.py does when the final jeopardy channel posts END_FJ_EVENT
        self.game.state.fj_timeout = True

    def settle(self, ms=0):
        """Advance one frame with no input (clears a state's init flag), then let time pass."""
        self.game.update()
        self.game.tick_game_clock(ms)

    @property
    def state(self):
        return self.game.state.cur_state

    def move_cursor_to(self, col, row, keys=P1):
        while self.game.cursor_loc[0] != col:
            self.press(keys["right"])
        while self.game.cursor_loc[1] != row:
            self.press(keys["down"])

    def answer(self, col, row, buzzer=P1, correct=True, chooser=P1, then=constants.MAIN_STATE):
        self.move_cursor_to(col, row, chooser)
        self.press(chooser["buzz"])
        assert self.state == constants.SHOW_CLUE_STATE

        self.press(buzzer["buzz"])
        assert self.state == constants.BUZZED_STATE

        # buzzed player must wait DELAY ms before confirming
        self.settle(constants.DELAY)
        self.press(buzzer["buzz"])
        assert self.state == constants.SHOW_RESP_STATE

        self.press(buzzer["left"] if correct else buzzer["right"])
        assert self.state == then


@pytest.fixture
def driver(monkeypatch):
    # timeouts sleep for a second for dramatic effect; skip that in tests
    monkeypatch.setattr(state.time, "sleep", lambda _: None)

    game = g.Game(
        pygame.display.get_surface(), make_library(), [1, 2, -1, -1], sfx_on=False, speech_on=False, input_type=False
    )

    # daily doubles are random; clear them so tests place their own
    for rnd in game.LIB[:2]:
        for category in rnd:
            for block in category:
                block.clue.dailydouble = False

    return Driver(game)


def test_correct_and_incorrect_answers_score(driver):
    p1, p2 = driver.game.players[:2]

    driver.answer(0, 2, buzzer=P1, correct=True)
    assert p1.score == 300

    # P1 keeps control after answering correctly
    driver.answer(1, 0, buzzer=P2, correct=False)
    assert p2.score == -100
    assert driver.game.state.active_player == 0

    driver.answer(2, 4, buzzer=P2, correct=True)
    assert p2.score == -100 + 500
    assert driver.game.state.active_player == 1  # P2 now chooses

    assert driver.game.LIB[0][0][2].clue_completed()


def test_daily_double_wager(driver):
    driver.game.LIB[0][3][1].clue.dailydouble = True
    p1 = driver.game.players[0]

    driver.move_cursor_to(3, 1)
    driver.press(P1["buzz"])
    assert driver.state == constants.BET_STATE
    assert p1.cur_bet == 1000  # max bet with a score under 1000

    driver.press(P1["down"])
    driver.press(P1["down"])
    assert p1.cur_bet == 800

    driver.press(P1["buzz"])
    assert driver.state == constants.BUZZED_STATE

    driver.settle(constants.DELAY)
    driver.press(P1["buzz"])
    assert driver.state == constants.SHOW_RESP_STATE

    driver.press(P1["left"])
    assert driver.state == constants.MAIN_STATE
    assert p1.score == 800


def test_full_game_through_final_jeopardy(driver):
    p1, p2 = driver.game.players[:2]

    for expected_round in (0, 1):
        assert driver.game.cur_round == expected_round
        for col in range(6):
            for row in range(5):
                last_clue = expected_round == 1 and (col, row) == (5, 4)
                # clearing the second board goes straight to final jeopardy
                then = constants.FINAL_BET_STATE if last_clue else constants.MAIN_STATE
                driver.answer(col, row, buzzer=P1, then=then)

    # both boards cleared: 6 x (100..500) + 6 x (200..1000)
    assert p1.score == 9000 + 18000
    assert driver.game.cur_round == 2
    assert driver.state == constants.FINAL_BET_STATE

    # P2 has no points, so only P1 wagers; P1 lowers the bet then locks it in
    assert p2.bet_set
    driver.press(P1["down"])
    driver.press(P1["buzz"])
    assert p1.cur_bet == 26900
    assert driver.state == constants.SHOW_CLUE_STATE

    # final jeopardy music ending is what moves the game on
    driver.settle()
    driver.end_final_music()
    driver.settle()
    assert driver.state == constants.FINAL_CHECK_STATE

    driver.press(P1["left"])  # correct
    assert driver.state == constants.END_STATE
    assert p1.score == 27000 + 26900

    driver.settle()
    assert driver.game.game_over
    assert not driver.game.return_to_menu()

    driver.press(P1["buzz"])
    assert driver.game.return_to_menu()


def test_wrong_final_jeopardy_answer_loses_wager(driver):
    p1 = driver.game.players[0]
    driver.answer(0, 4, buzzer=P1)  # 500 points

    driver.game.force_update_round()
    driver.game.cur_round = 2
    driver.settle()
    assert driver.state == constants.FINAL_BET_STATE

    driver.press(P1["buzz"])  # wager everything
    driver.settle()
    driver.end_final_music()
    driver.settle()
    assert driver.state == constants.FINAL_CHECK_STATE

    driver.press(P1["right"])  # incorrect
    assert p1.score == 0
    assert driver.state == constants.END_STATE


def test_clue_times_out_when_nobody_buzzes(driver):
    p1, p2 = driver.game.players[:2]

    driver.move_cursor_to(0, 0)
    driver.press(P1["buzz"])
    assert driver.state == constants.SHOW_CLUE_STATE

    driver.settle(constants.CLUE_TIMEOUT)
    driver.settle()
    assert driver.state == constants.SHOW_RESP_STATE
    assert driver.game.state.clue_timeout

    # marking right/wrong is ignored after a timeout; the chooser continues
    driver.press(P1["left"])
    assert driver.state == constants.SHOW_RESP_STATE
    driver.press(P1["buzz"])
    assert driver.state == constants.MAIN_STATE
    assert (p1.score, p2.score) == (0, 0)
    assert driver.game.LIB[0][0][0].clue_completed()
