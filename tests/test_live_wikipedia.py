"""Checks against the real MediaWiki API. Skipped unless JEOPYRDY_LIVE_TESTS=1.

Run weekly by .github/workflows/live.yml alongside the j-archive checks; the
offline tests in test_downloads.py assume the response shapes checked here.
"""

import os
import urllib.parse

import pytest

import constants
import util

pytestmark = pytest.mark.skipif(
    os.environ.get("JEOPYRDY_LIVE_TESTS") != "1", reason="set JEOPYRDY_LIVE_TESTS=1 to run against Wikipedia"
)


def test_lead_image_thumbnail_for_exact_title():
    url = util.wiki_image_url("Julianne Moore")
    assert url and urllib.parse.urlsplit(url).path.lower().endswith((".jpg", ".jpeg"))


def test_redirect_and_search_fallbacks():
    assert util.wiki_image_url("caribou")  # redirects to Reindeer
    assert util.wiki_image_url("the Rough Riders")  # no such page; found by search


def test_thumbnail_downloads_with_our_user_agent(tmp_path, monkeypatch):
    monkeypatch.setattr(constants, "TEMP_PATH", str(tmp_path))
    path = util.get_img_from_wiki("Julianne Moore", 0)
    assert path and os.path.getsize(path) > 1000
