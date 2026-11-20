"""Checks against the real j-archive site. Skipped unless JEOPYRDY_LIVE_TESTS=1.

Run weekly by .github/workflows/live.yml so changes to j-archive's markup show
up as a failed scheduled run instead of a game that silently stops loading.
The offline parser tests (test_parser.py) assume the markup checked here.
"""

import os

import pytest

import constants
import util

pytestmark = pytest.mark.skipif(
    os.environ.get("JEOPYRDY_LIVE_TESTS") != "1", reason="set JEOPYRDY_LIVE_TESTS=1 to run against j-archive.com"
)


def fetch(game_num):
    return util.parse_game(
        util.fetch_lines(constants.WEB_ADDR_CLUE + str(game_num)),
        util.fetch_lines(constants.WEB_ADDR_RESP + str(game_num)),
    )


def test_complete_game_still_parses():
    game = fetch(9000)  # Show #9157, September 10, 2024

    assert game.is_complete, (len(game.clues), len(game.responses), len(game.categories))
    assert game.info[0].startswith("SHOW #9157")
    # clues and responses still line up
    assert game.clues[0].startswith("The film seen here")
    assert game.responses[0] == "blacksmith"
    # image clues still carry media links
    assert any(util.JARCHIVE_IMAGE.search(html) for html in game.clue_html)


def test_game_with_unrevealed_clues_is_detected():
    game = fetch(4705)  # Show #794: 56 of 61 clues revealed
    assert not game.is_complete
    assert len(game.clues) == len(game.responses) == 56
