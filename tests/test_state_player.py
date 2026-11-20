import pytest

import constants
import player
import state

ALL_STATES = [
    constants.MAIN_STATE, constants.BET_STATE, constants.BUZZED_STATE, constants.SHOW_CLUE_STATE,
    constants.SHOW_RESP_STATE, constants.FINAL_BET_STATE, constants.FINAL_CHECK_STATE, constants.END_STATE,
]


@pytest.mark.parametrize("cur_state", ALL_STATES)
def test_every_state_has_a_label(cur_state):
    s = state.State(sfx_on=False)
    s.cur_state = cur_state
    label = str(s)  # used to raise NameError (undefined CHECK_STATE) for later states
    assert label.endswith("STATE") and "UNKNOWN" not in label


def test_state_labels_are_unique():
    assert len({state.STATE_NAMES[s] for s in ALL_STATES}) == len(ALL_STATES)


def test_unknown_state_label_does_not_raise():
    s = state.State(sfx_on=False)
    s.cur_state = 99
    assert str(s) == "UNKNOWN STATE (99)"


@pytest.mark.parametrize(("score", "expected_bet"), [(0, 1000), (400, 1000), (2500, 2500)])
def test_regular_setup_bet_uses_max_bet(score, expected_bet):
    p = player.Player(0, 3)
    p.add_to_score(score)

    p.setup_bet()  # used to store the get_max_bet method itself

    assert p.cur_bet == expected_bet
    assert p.is_betting


def test_final_setup_bet_unchanged():
    p = player.Player(0, 3)
    p.add_to_score(1200)
    p.setup_bet(final=True)
    assert p.cur_bet == 1200 and p.is_betting

    broke = player.Player(1, 4)
    broke.setup_bet(final=True)
    assert broke.cur_bet == 0 and broke.bet_set
