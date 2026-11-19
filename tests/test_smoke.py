import types

import pygame

import constants
import gen
import library
import menu
import player
import util


def test_all_modules_import():
    import game  # noqa: F401
    import main  # noqa: F401
    import state  # noqa: F401


def test_scrub_text_removes_markup():
    raw = 'Tom &amp; Jerry<br />are <i>cartoon</i> <a href="http://x/y.jpg">stars</a>'
    assert util.scrub_text(raw) == "Tom & Jerry are cartoon stars"


def test_gamify_list_splits_rounds_and_final():
    items = list(range(61))  # 30 + 30 clues + final jeopardy
    rounds = util.gamify_list(items)

    assert len(rounds) == 3
    assert [len(cat) for cat in rounds[0]] == [5] * 6
    assert [len(cat) for cat in rounds[1]] == [5] * 6
    assert rounds[0][0] == [0, 6, 12, 18, 24]
    assert rounds[2] == [[60]]


def test_gamify_input_maps_keyboard_to_player_buttons():
    event = types.SimpleNamespace(type=pygame.KEYDOWN, key=119)  # P1 "w"
    assert util.gamify_input(event) == [
        [0, 1, 0, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
    ]


def test_board_surfaces_build():
    assert gen.board_surface().get_size() == constants.BOARD_SIZE
    assert len(gen.value_surfaces()) == 2
    assert library.Category("POTENT POTABLES").board_surface is not None


def test_player_scoring():
    p = player.Player(0, 3)
    p.add_to_score(400)
    p.sub_from_score(100)
    assert p.score == 300


def test_menu_character_grid_uses_integer_positions():
    m = menu.Menu(pygame.display.get_surface(), pygame.mixer.Channel(0), None)
    assert m.charsel_dimension == [6, 0]
    assert m._Menu__get_pos_from_num(7) == [1, 1]
