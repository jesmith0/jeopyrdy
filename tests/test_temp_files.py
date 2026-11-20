"""Downloaded clue images are cleaned up (#19)."""

import pytest

import constants
import util


@pytest.fixture
def temp_dir(monkeypatch, tmp_path):
    monkeypatch.setattr(constants, "TEMP_PATH", str(tmp_path))
    return tmp_path


def test_deletes_downloaded_images_only(temp_dir):
    ours = ["ja0.jpg", "ja12.jpg", "wiki3.png", "wiki40.jpeg", "wiki9.gif", "WIKI1.JPG"]
    others = ["notes.txt", ".gitkeep", "jam.jpg", "wiki.jpg", "wiki3.png.bak", "temp0.jpg"]
    for name in ours + others:
        (temp_dir / name).write_bytes(b"x")
    (temp_dir / "wiki5.jpg").mkdir()  # a directory with a matching name is left alone

    assert util.clear_temp_files() == len(ours)
    assert sorted(p.name for p in temp_dir.iterdir()) == sorted(others + ["wiki5.jpg"])


def test_downloads_use_names_cleanup_recognises():
    # keeps clear_temp_files in sync with the names get_resource/get_img_from_wiki write
    for name in ("ja0.jpg", "wiki60.jpg", "wiki34.png", "wiki48.jpeg"):
        assert util.TEMP_FILE.match(name)


def test_missing_temp_dir_is_fine(monkeypatch, tmp_path):
    monkeypatch.setattr(constants, "TEMP_PATH", str(tmp_path / "gone"))
    assert util.clear_temp_files() == 0


def test_empty_temp_dir(temp_dir):
    assert util.clear_temp_files() == 0
