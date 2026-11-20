"""State labels and wager setup outside the usual final-round caller."""
import pytest

import constants
import player
import state


@pytest.mark.parametrize(("value", "label"), [
    (constants.MAIN_STATE, "MAIN STATE"),
    (constants.BET_STATE, "BET STATE"),
    (constants.BUZZED_STATE, "BUZZED STATE"),
    (constants.SHOW_CLUE_STATE, "SHOW CLUE STATE"),
    (constants.SHOW_RESP_STATE, "SHOW RESPONSE STATE"),
    (constants.FINAL_BET_STATE, "FINAL BET STATE"),
    (constants.FINAL_CHECK_STATE, "FINAL CHECK STATE"),
    (constants.END_STATE, "END STATE"),
    (-1, "UNKNOWN STATE"),
])
def test_state_labels(value, label):
    current = state.State(sfx_on=False)
    current.cur_state = value
    assert str(current) == label


@pytest.mark.parametrize(("score", "maximum"), [
    (-100, 1000), (0, 1000), (500, 1000), (1000, 1000), (3000, 3000),
])
def test_regular_bet_starts_at_numeric_maximum(score, maximum):
    contestant = player.Player(0, 3)
    contestant.score = score
    contestant.setup_bet()
    assert contestant.cur_bet == maximum
    assert contestant.is_betting is True
    assert contestant.bet_set is False
    # Exercise arithmetic and rendering too, rather than only checking the type.
    contestant.dec_bet()
    assert contestant.cur_bet == maximum - 100


@pytest.mark.parametrize("score", [-100, 0, 3000])
def test_final_bet_retains_score_and_eligibility(score):
    contestant = player.Player(0, 3)
    contestant.score = score
    contestant.setup_bet(final=True)
    assert contestant.cur_bet == score
    assert contestant.is_betting == (score > 0)
    assert contestant.bet_set == (score <= 0)
