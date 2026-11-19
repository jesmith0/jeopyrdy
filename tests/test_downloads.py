"""Clue image downloads, tested offline with a fake urlopen."""
import email.message
import io
import types
import urllib.error

import pytest

import constants
import util

# real clue_text snippets from j-archive game 6500
HTTPS_CLUE = ('A 40-foot Paris <a href="https://www.j-archive.com/media/2019-12-18_J_06.jpg" '
              'target="_blank">sculpture</a> is called Le Pouce')
HTTP_CLUE = ('Check out the 130-foot <a href="http://www.j-archive.com/media/2019-12-18_J_07.jpg" '
             'target="_blank">Rain Vortex</a> at Changi Airport')
PLAIN_CLUE = "This Canadian hosted Jeopardy! for 37 seasons"

JPEG = b"\xff\xd8\xff\xe0fake-jpeg"


class FakeWeb:
    """Stands in for urllib.request.urlopen; maps url -> (status, content_type, body)."""

    def __init__(self):
        self.pages = {}
        self.requests = []

    def __call__(self, request, timeout=None):
        self.requests.append(request)
        status, content_type, body = self.pages.get(request.full_url, (404, "text/html", b"not found"))
        if status != 200:
            raise urllib.error.HTTPError(request.full_url, status, "error", None, io.BytesIO(body))
        headers = email.message.Message()
        headers["Content-Type"] = content_type
        response = io.BytesIO(body)
        response.headers = headers
        return response


@pytest.fixture
def web(monkeypatch, tmp_path):
    fake = FakeWeb()
    monkeypatch.setattr(util.urllib.request, "urlopen", fake)
    monkeypatch.setattr(constants, "TEMP_PATH", str(tmp_path))
    return fake


@pytest.mark.parametrize("clue", [HTTPS_CLUE, HTTP_CLUE])
def test_jarchive_image_downloaded_over_http_and_https(web, clue):
    url = util.JARCHIVE_IMAGE.search(clue).group(1)
    web.pages[url] = (200, "image/jpeg", JPEG)

    path = util.get_resource(clue, 3)

    assert path.endswith("ja3.jpg")
    with open(path, "rb") as f:
        assert f.read() == JPEG


def test_clue_without_image_has_no_resource(web):
    assert util.get_resource(PLAIN_CLUE, 0) is None
    assert web.requests == []


def test_missing_jarchive_image_falls_back(web):
    # j-archive currently 404s all media; "404" tells the caller to try Wikipedia
    assert util.get_resource(HTTPS_CLUE, 0) == "404"


def test_html_error_page_is_not_saved_as_image(web, tmp_path):
    url = util.JARCHIVE_IMAGE.search(HTTPS_CLUE).group(1)
    web.pages[url] = (200, "text/html", b"<html>gone</html>")

    assert util.get_resource(HTTPS_CLUE, 0) == "404"
    assert list(tmp_path.iterdir()) == []


def test_downloads_send_user_agent_and_timeout(web, monkeypatch):
    seen = {}

    def spy(request, timeout=None):
        seen["ua"] = request.get_header("User-agent")
        seen["timeout"] = timeout
        return web(request, timeout)

    monkeypatch.setattr(util.urllib.request, "urlopen", spy)
    util.download("https://upload.wikimedia.org/x.jpg", "unused")

    assert seen["ua"] == constants.USER_AGENT
    assert seen["timeout"] == constants.HTTP_TIMEOUT


def test_wikipedia_fallback_picks_first_photo(web, monkeypatch):
    page = types.SimpleNamespace(images=[
        "https://upload.wikimedia.org/wikipedia/commons/a/aa/Icon.svg",
        "https://upload.wikimedia.org/wikipedia/en/c/cd/Hogan%27s_Heroes_logo.png",
        "https://upload.wikimedia.org/wikipedia/commons/b/bb/Cast.jpg",
    ])
    monkeypatch.setattr(util.wikipedia, "page", lambda query: page)
    web.pages[page.images[1]] = (200, "image/png", b"\x89PNG fake")

    path = util.get_img_from_wiki("Hogan's Heroes", 7)

    assert path.endswith("wiki7.png")  # keeps the real extension so pygame can load it


def test_wikipedia_forbidden_returns_none(web, monkeypatch):
    page = types.SimpleNamespace(images=["https://upload.wikimedia.org/x/Photo.jpg"])
    monkeypatch.setattr(util.wikipedia, "page", lambda query: page)
    web.pages[page.images[0]] = (403, "text/plain", b"forbidden")

    assert util.get_img_from_wiki("anything", 0) is None


def test_wikipedia_package_uses_our_user_agent():
    assert util.wikipedia.wikipedia.USER_AGENT == constants.USER_AGENT
