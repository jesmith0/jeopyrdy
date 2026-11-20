"""Offline tests for j-archive parsing and game setup (#23)."""

import pytest
from jarchive_pages import all_clue_ids, clue_text, game_pages, response_text

import constants
import util

MEDIA_URL = "https://www.j-archive.com/media/2024-09-10_J_02.jpg"


def parse(**kwargs):
    return util.parse_game(*game_pages(**kwargs))


# --- parsing ---------------------------------------------------------------


def test_complete_game_parses_all_parts():
    game = parse(title="Show #9157 - Tuesday, September 10, 2024")

    assert game.is_complete
    assert len(game.clues) == len(game.responses) == 61
    assert len(game.categories) == 13
    assert game.info == ["SHOW #9157 - TUESDAY, SEPTEMBER 10, 2024"]
    assert game.categories[:2] == ["J CATEGORY 1", "J CATEGORY 2"]
    assert game.categories[-1] == "FINAL CATEGORY"


def test_hidden_response_cells_are_not_counted_as_clues():
    game = parse()
    responses = {response_text(cid) for cid in all_clue_ids()}
    assert not responses & set(game.clues)


def test_clues_and_responses_stay_aligned():
    game = parse()
    ids = all_clue_ids()
    assert game.clues == [clue_text(cid) for cid in ids]
    assert game.responses == [response_text(cid) for cid in ids]


def test_board_layout_matches_page_ids():
    game = parse()
    res = [None] * 61
    lib = util.gen_lib_object([game.categories, game.clues, game.responses, res])

    # lib[round][column][row]
    assert str(lib[0][2][3].clue) == clue_text("J_3_4")
    assert str(lib[0][2][3].response) == response_text("J_3_4")
    assert str(lib[0][2][3].category) == "J CATEGORY 3"
    assert str(lib[1][5][4].clue) == clue_text("DJ_6_5")
    assert str(lib[2][0][0].clue) == clue_text("FJ")
    assert str(lib[2][0][0].category) == "FINAL CATEGORY"


def test_markup_is_scrubbed():
    game = parse(
        clue_overrides={
            "J_1_1": "Tom &amp; Jerry<br />cartoons",
            "J_2_1": f'The film seen <a href="{MEDIA_URL}" target="_blank">here</a> shows these workers',
            "J_3_1": "<i>Hamlet</i> is set here",
        },
        response_overrides={
            # real responses page: contestant chatter before the response
            "J_1_1": "(Player A: What is a... tittle?)<br />(Player B: A chuckle?)<br /><br />"
            '<em class="correct_response">giggling</em>',
            "J_2_1": '<em class="correct_response"><i>The Raven</i></em>',
        },
    )

    assert game.clues[0] == "Tom & Jerry cartoons"
    assert game.clues[1] == "The film seen here shows these workers"
    assert game.clues[2] == "Hamlet is set here"
    assert game.responses[0] == "giggling"
    assert game.responses[1] == "The Raven"


def test_raw_clue_markup_keeps_media_links():
    game = parse(clue_overrides={"J_2_1": f'Seen <a href="{MEDIA_URL}" target="_blank">here</a>'})
    assert util.JARCHIVE_IMAGE.search(game.clue_html[1]).group(1) == MEDIA_URL


@pytest.mark.parametrize("unrevealed", [("J_4_5",), ("DJ_1_1", "DJ_6_5"), ("FJ",)])
def test_unrevealed_clues_make_game_incomplete(unrevealed):
    game = parse(unrevealed=unrevealed)
    assert not game.is_complete
    assert len(game.clues) == 61 - len(unrevealed)


def test_empty_page_is_incomplete():
    # nonexistent game ids return a page without a game
    game = util.parse_game(["<html><body>No game</body></html>"], [])
    assert not game.is_complete


# --- lib_setup retries -------------------------------------------------------


class FakeArchive:
    """Serves generated pages per game id; ids not listed raise a network error."""

    def __init__(self, games):
        self.games = games
        self.fetched = []

    def __call__(self, url):
        page, game_num = url.split("game_id=")
        self.fetched.append(int(game_num))
        if int(game_num) not in self.games:
            raise OSError("connection refused")
        clue_page, resp_page = self.games[int(game_num)]
        return clue_page if "showgameresponses" not in page else resp_page


@pytest.fixture
def archive(monkeypatch):
    def install(games, picks, forced=None):
        fake = FakeArchive(games)
        monkeypatch.setattr(util, "fetch_lines", fake)
        monkeypatch.setattr(constants, "FORCE_GAME", forced)
        picks = iter(picks)
        monkeypatch.setattr(util.random, "randint", lambda a, b: next(picks))
        resources = []
        monkeypatch.setattr(util, "fetch_resources", lambda game: resources.append(game) or [None] * 61)
        return fake, resources

    return install


def test_setup_skips_incomplete_and_unreachable_games(archive):
    fake, resources = archive(
        games={1: game_pages(unrevealed=("J_1_1",)), 3: game_pages(title="Show #3")},
        picks=[1, 2, 3],  # incomplete, network error, complete
    )

    lib, info = util.lib_setup()

    assert info == ["SHOW #3"]
    assert len(lib) == 3
    # images are only downloaded for the game that's actually used
    assert len(resources) == 1 and resources[0].info == ["SHOW #3"]


def test_setup_gives_up_instead_of_looping_forever(archive):
    archive(games={1: game_pages(unrevealed=("FJ",))}, picks=[1] * 100)

    with pytest.raises(util.LibraryError, match="3 attempts"):
        util.lib_setup(max_attempts=3)


def test_forced_incomplete_game_fails_fast(archive):
    # e.g. FORCE_GAME = 6500 (59 of 61 clues) used to hang setup forever
    fake, resources = archive(games={6500: game_pages(unrevealed=("J_1_1", "J_2_2"))}, picks=[], forced=6500)

    with pytest.raises(util.LibraryError, match="6500"):
        util.lib_setup()

    assert fake.fetched == [6500, 6500]  # one attempt: clue page + responses page
    assert resources == []


def test_resources_fetched_per_clue_with_wikipedia_fallback(monkeypatch):
    game = parse(clue_overrides={"J_2_1": f'Seen <a href="{MEDIA_URL}" target="_blank">here</a>'})
    monkeypatch.setattr(util, "get_resource", lambda html, n: "404" if MEDIA_URL in html else None)
    looked_up = []
    monkeypatch.setattr(util, "get_img_from_wiki", lambda query, n: looked_up.append((query, n)) or "wiki.jpg")

    res = util.fetch_resources(game)

    assert res[1] == "wiki.jpg"
    assert looked_up == [(response_text("J_2_1"), 1)]
    assert res.count(None) == 60
