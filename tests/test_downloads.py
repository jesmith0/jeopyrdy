"""Clue image downloads, tested offline with a fake urlopen."""

import email.message
import io
import urllib.error
import urllib.parse

import pytest

import constants
import util

# real clue_text snippets from j-archive game 6500
HTTPS_CLUE = (
    'A 40-foot Paris <a href="https://www.j-archive.com/media/2019-12-18_J_06.jpg" '
    'target="_blank">sculpture</a> is called Le Pouce'
)
HTTP_CLUE = (
    'Check out the 130-foot <a href="http://www.j-archive.com/media/2019-12-18_J_07.jpg" '
    'target="_blank">Rain Vortex</a> at Changi Airport'
)
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


# --- Wikipedia fallback via the MediaWiki API --------------------------------
# Response shapes captured from en.wikipedia.org/w/api.php (formatversion=2).

UTM = "?utm_source=en.wikipedia.org&utm_campaign=api&utm_content=thumbnail"
MOORE_THUMB = (
    "https://thumb.wikimedia.org/wikipedia/commons/thumb/4/4d/Julianne_Moore.jpg/500px-Julianne_Moore.jpg" + UTM
)
REINDEER_THUMB = "https://thumb.wikimedia.org/wikipedia/commons/thumb/9/96/Reinbukken.jpg/500px-Reinbukken.jpg" + UTM
RIDERS_THUMB = "https://thumb.wikimedia.org/wikipedia/commons/thumb/c/cd/RoughRiders.jpeg/500px-RoughRiders.jpeg" + UTM
LOGO_THUMB = "https://thumb.wikimedia.org/wikipedia/commons/thumb/a/aa/Logo.svg/500px-Logo.svg.png" + UTM


def page(title, thumb=None, **extra):
    p = {"ns": 0, "title": title, **extra}
    if thumb:
        p["thumbnail"] = {"source": thumb, "width": 500, "height": 600}
    return p


TITLES = {
    "Julianne Moore": [page("Julianne Moore", MOORE_THUMB, pageid=243685)],
    # redirect: caribou -> Reindeer
    "caribou": [page("Reindeer", REINDEER_THUMB, pageid=143912)],
    "Guard": [page("Guard", pageid=181708, pageprops={"disambiguation": ""})],
    "the Rough Riders": [page("The Rough Riders", missing=True)],
    "Imageless Topic": [page("Imageless Topic", pageid=1)],
    "Some Logo": [page("Some Logo", LOGO_THUMB, pageid=2)],
}
SEARCHES = {
    "the Rough Riders": [
        page("Rough Riders (disambiguation)", index=1, pageprops={"disambiguation": ""}),
        page("Ottawa Rough Riders", index=2),
        page("Rough Riders", RIDERS_THUMB, index=3),
    ],
    "Guard": [page("Security guard", MOORE_THUMB, index=1)],
}


@pytest.fixture
def wiki_api(web, monkeypatch):
    """Fake MediaWiki API on top of the fake web; records each query."""
    queries = []

    def fake_fetch_json(url):
        params = dict(urllib.parse.parse_qsl(urllib.parse.urlsplit(url).query))
        queries.append(params)
        assert url.startswith(util.WIKI_API)
        assert params["prop"] == "pageimages|pageprops" and params["redirects"] == "1"
        if "titles" in params:
            pages = TITLES.get(params["titles"], [page(params["titles"], missing=True)])
        else:
            # search results arrive unordered; rank is in "index"
            pages = list(reversed(SEARCHES.get(params["gsrsearch"], [])))
        return {"batchcomplete": True, "query": {"pages": pages}}

    monkeypatch.setattr(util, "fetch_json", fake_fetch_json)
    for thumb in (MOORE_THUMB, REINDEER_THUMB, RIDERS_THUMB):
        web.pages[thumb] = (200, "image/jpeg", JPEG)
    web.pages[LOGO_THUMB] = (200, "image/png", b"\x89PNG fake")
    return queries


def test_exact_title_uses_lead_image(wiki_api):
    path = util.get_img_from_wiki("Julianne Moore", 3)

    assert path.endswith("wiki3.jpg")
    assert [q.get("titles") for q in wiki_api] == ["Julianne Moore"]  # no search needed
    assert wiki_api[0]["pithumbsize"] == str(util.WIKI_THUMB_SIZE)


def test_redirect_followed(wiki_api):
    assert util.wiki_image_url("caribou") == REINDEER_THUMB


def test_missing_page_falls_back_to_first_search_result_with_image(wiki_api):
    # skips the disambiguation page and the result without an image
    assert util.wiki_image_url("the Rough Riders") == RIDERS_THUMB
    assert util.get_img_from_wiki("the Rough Riders", 0).endswith("wiki0.jpeg")


def test_disambiguation_page_falls_back_to_search(wiki_api):
    assert util.wiki_image_url("Guard") == MOORE_THUMB


def test_existing_page_without_image_does_not_search(wiki_api):
    # a search could land on a different topic's picture
    assert util.get_img_from_wiki("Imageless Topic", 0) is None
    assert len(wiki_api) == 1


def test_nothing_found_returns_none(wiki_api):
    assert util.get_img_from_wiki("Xqzzyplorf", 0) is None


def test_svg_thumbnails_are_png(wiki_api):
    assert util.get_img_from_wiki("Some Logo", 5).endswith("wiki5.png")


def test_api_failure_returns_none(web, monkeypatch):
    def broken(request, timeout=None):
        raise OSError("network down")

    monkeypatch.setattr(util.urllib.request, "urlopen", broken)
    assert util.fetch_json(util.WIKI_API + "?action=query") == {}
    assert util.get_img_from_wiki("Julianne Moore", 0) is None


def test_fetch_json_sends_user_agent(monkeypatch):
    seen = {}

    def fake_urlopen(request, timeout=None):
        seen["ua"] = request.get_header("User-agent")
        return io.BytesIO(b'{"query": {"pages": []}}')

    monkeypatch.setattr(util.urllib.request, "urlopen", fake_urlopen)
    assert util.fetch_json(util.WIKI_API) == {"query": {"pages": []}}
    assert seen["ua"] == constants.USER_AGENT


def test_wikipedia_image_forbidden_returns_none(wiki_api, web):
    web.pages[MOORE_THUMB] = (403, "text/plain", b"forbidden")
    assert util.get_img_from_wiki("Julianne Moore", 0) is None
