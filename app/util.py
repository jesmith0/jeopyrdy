import constants
import library
import os
import platform
import player
import pygame
import random
import re
import urllib.parse
import urllib.request
import wikipedia

# GLOBAL VARIABLES
image_count = 0

# image link inside a j-archive clue (served over http or https)
JARCHIVE_IMAGE = re.compile(r'<a href="(https?://[^"]+\.jpg)"', re.IGNORECASE)

# image types pygame can load that Wikipedia pages commonly use
WIKI_IMAGE_EXTS = (".jpg", ".jpeg", ".png")

wikipedia.set_user_agent(constants.USER_AGENT)


# CONVERT PYGAME EVENT TO USABLE GAME INPUT
def gamify_input(event):
    buzz_map = [[0, 4, 3, 2, 1], [5, 9, 8, 7, 6], [10, 14, 13, 12, 11], [15, 19, 18, 17, 16]]
    key_map = [[50, 119, 100, 97, 115], [53, 116, 104, 102, 103], [56, 105, 108, 106, 107], [45, 91, 13, 59, 39]]

    ret = []
    arr = []

    if event.type == pygame.KEYDOWN:
        map = key_map
        button = event.key
    elif event.type == pygame.JOYBUTTONDOWN or event.type == pygame.JOYBUTTONUP:
        map = buzz_map
        button = event.button

    for set in map:

        if button in set:
            for value in set:

                if button == value:
                    arr.append(1)
                else:
                    arr.append(0)

            ret.append(arr)

        else:
            ret.append([0, 0, 0, 0, 0])

    return ret


# REMOVE UNNECESSARY HTML
def scrub_text(text):
    # remove static tags
    new_text = text.replace('&amp;', '&')
    new_text = new_text.replace('<br />', ' ')
    new_text = new_text.replace('<br/>', ' ')
    new_text = new_text.replace('<i>', '')
    new_text = new_text.replace('</i>', '')
    new_text = new_text.replace('<u>', '')
    new_text = new_text.replace('</u>', '')
    new_text = new_text.replace('<del>', '')
    new_text = new_text.replace('</del>', '')
    new_text = new_text.replace('</em>', '')
    new_text = new_text.replace('</a>', '')

    # remove emphasis tag
    if not new_text.find('<em') == -1:
        new_text = new_text[:new_text.find('<em')] + new_text[new_text.find('>') + 2:]

    # for each hyperlink tag
    while not new_text.find('<a') == -1:
        # removes every hyperlink reference tag from text
        new_text = new_text[:new_text.find('<a')] + new_text[new_text.find('">') + 2:]

    return new_text


def get_img_from_wiki(query, num):
    try:
        print(query)
        page = wiki_page(query)

    except wikipedia.exceptions.DisambiguationError as de:

        try:
            # use first suggestion
            page = wiki_page((str(de).split('\n'))[1])
        except Exception as e:
            print(e)
            print("some other error")
            return None

    except wikipedia.exceptions.PageError as pe:
        print(pe)
        return None

    # first photo-like image on the page (skips svg icons and logos)
    for image in page.images:
        # image urls carry tracking query strings (?utm_source=...)
        ext = os.path.splitext(urllib.parse.urlsplit(image).path)[1].lower()
        if ext in WIKI_IMAGE_EXTS:
            return download(image, os.path.join(constants.TEMP_PATH, "wiki" + str(num) + ext))

    return None


# LOOK UP A WIKIPEDIA PAGE BY TITLE
# The package's auto-suggest "corrects" exact titles ("Julianne Moore" ->
# "julianne more"), so only fall back to it when the exact title isn't found.
def wiki_page(query):
    try:
        return wikipedia.page(query, auto_suggest=False)
    except wikipedia.exceptions.PageError:
        return wikipedia.page(query, auto_suggest=True)


# PULL MEDIA RESOURCES FROM J-ARCHIVE
# Returns a local image path, None if the clue has no image, or "404" if it has
# one that couldn't be downloaded (the caller then falls back to Wikipedia).
def get_resource(text, num):
    match = JARCHIVE_IMAGE.search(text)
    if not match:
        return None

    url = match.group(1)
    return download(url, os.path.join(constants.TEMP_PATH, "ja" + str(num) + ".jpg")) or "404"


# DOWNLOAD AN IMAGE TO dest; RETURNS dest, OR None IF IT FAILED OR WASN'T AN IMAGE
def download(url, dest):
    request = urllib.request.Request(url, headers={"User-Agent": constants.USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=constants.HTTP_TIMEOUT) as response:
            if not response.headers.get_content_type().startswith("image/"):
                print("NOT AN IMAGE: " + url)
                return None
            data = response.read()
    except (OSError, ValueError) as e:  # URLError/HTTPError/timeouts are OSErrors
        print(e)
        print("ERROR OPENING " + url)
        return None

    with open(dest, "wb") as f:
        f.write(data)
    print(dest)
    return dest


# FETCH A WEB PAGE AS A LIST OF DECODED TEXT LINES
def fetch_lines(url):
    request = urllib.request.Request(url, headers={"User-Agent": constants.USER_AGENT})
    with urllib.request.urlopen(request, timeout=constants.HTTP_TIMEOUT) as page:
        return [raw.decode("utf-8", "replace") for raw in page.readlines()]


# PARSED J-ARCHIVE GAME (text only; images are fetched separately)
class ParsedGame:

    CLUES = 61  # 30 jeopardy + 30 double jeopardy + final
    CATEGORIES = 13  # 6 + 6 + final

    def __init__(self, categories, clues, clue_html, responses, info):
        self.categories = categories
        self.clues = clues  # scrubbed clue text
        self.clue_html = clue_html  # raw clue markup (holds media links)
        self.responses = responses
        self.info = info

    # every clue was revealed on air; otherwise the board can't be laid out
    @property
    def is_complete(self):
        return (len(self.clues) == len(self.responses) == self.CLUES
                and len(self.categories) == self.CATEGORIES)


class LibraryError(Exception):
    pass


# PARSE J-ARCHIVE GAME PAGES (lists of lines) INTO A ParsedGame
def parse_game(clue_lines, resp_lines):
    categories = []
    clue_html = []
    responses = []
    info = []

    # clue page: categories, clues and the title. Hidden response cells are
    # also class "clue_text" but carry a style attribute, so the exact
    # 'class="clue_text">' match skips them.
    for line in clue_lines:
        if 'class="clue_text">' in line:
            clue_html.append(line[line.find('class="clue_text">') + 18:line.find('</td>')])
        elif 'class="category_name">' in line:
            categories.append(scrub_text(line[line.find('class="category_name">') + 22:line.find('</td>')]))
        elif 'id="game_title">' in line:
            info.append(line[line.find('id="game_title"><h1>') + 20:line.find('</h1>')].upper())

    # responses page
    for line in resp_lines:
        if 'class="correct_response">' in line:
            responses.append(scrub_text(line[line.find('class="correct_response">') + 25:line.find('</em>')]))

    clues = [scrub_text(html) for html in clue_html]
    return ParsedGame(categories, clues, clue_html, responses, info)


# PULL GAME DATA FROM J-ARCHIVE
def parse_jarchive(game_num):
    print(game_num)
    return parse_game(fetch_lines(constants.WEB_ADDR_CLUE + str(game_num)),
                      fetch_lines(constants.WEB_ADDR_RESP + str(game_num)))


# DOWNLOAD CLUE IMAGES (j-archive, falling back to a Wikipedia image of the response)
def fetch_resources(game):
    res = []
    res_count = 0

    for i, html in enumerate(game.clue_html):
        res.append(get_resource(html, res_count))

        # increment resource count if one is supposed to exist
        if res[i]: res_count += 1

        # grab image from Wikipedia if 404ed
        if res[i] == '404': res[i] = get_img_from_wiki(game.responses[i], i)

    return res


# GENERATE LIBRARY OBJECT FROM PULLED DATA
def gen_lib_object(parsed):
    cat = gamify_list(parsed[0])
    clue = gamify_list(parsed[1])
    resp = gamify_list(parsed[2])
    res = gamify_list(parsed[3])

    lib = []

    # each round is its own list of block objects
    for i in range(len(clue)):

        lib.append([])

        for j in range(len(clue[i])):
            lib[-1].append([])
            for k in range(len(clue[i][j])):
                lib[-1][-1].append(library.Block(library.Category(cat[i][j][0]), library.Clue(clue[i][j][k]),
                                                 library.Response(resp[i][j][k]), library.Resource(res[i][j][k])))

    return lib


# SETUP LIBRARY OBJECT
# Tries random games until one is complete (some games have clues that were
# never revealed on air). Gives up after max_attempts instead of looping
# forever, and fails fast if a forced game is incomplete.
MAX_SETUP_ATTEMPTS = 10


def lib_setup(max_attempts=MAX_SETUP_ATTEMPTS):
    for _ in range(max_attempts):
        game_num = constants.FORCE_GAME or random.randint(1, constants.MAX_GAME)

        try:
            game = parse_jarchive(game_num)
        except OSError as e:  # network errors, timeouts
            print("COULD NOT FETCH GAME " + str(game_num) + ": " + str(e))
            continue

        if game.is_complete:
            # only download images once the game is known to be usable
            res = fetch_resources(game)
            print("LIBRARY (setup):\tOK")
            return [gen_lib_object([game.categories, game.clues, game.responses, res]), game.info]

        print("GAME " + str(game_num) + " INCOMPLETE: " + str(len(game.clues)) + " clues, "
              + str(len(game.responses)) + " responses, " + str(len(game.categories)) + " categories")

        if constants.FORCE_GAME:
            raise LibraryError("forced game " + str(game_num) + " is incomplete or unavailable")

    raise LibraryError("no complete game found in " + str(max_attempts) + " attempts")


# DELETE TEMPORARY FILES (MEDIA RESOURCES)
def dtf():
    if 'Windows' in platform.system():
        path = 'temp\\'
    else:
        path = 'temp/'

    num = 0
    while num >= 0:
        try:
            os.remove(path + 'temp' + str(num) + '.jpg')
            num += 1
        except Exception as e:
            print(e)
            num = -1


# CREATE PYGAME JOYSTICK OBJECT OF USB BUZZERS
def get_buzzers():
    pygame.joystick.quit()
    pygame.joystick.init()

    # TODO: Check for possible memory leak

    buzzer = None

    for i in range(0, pygame.joystick.get_count()):
        if 'Buzz' in pygame.joystick.Joystick(i).get_name():
            buzzer = pygame.joystick.Joystick(i)
            buzzer.init()

    return buzzer


# INITIALIZE PLAYER OBJECTS (CHOOSE CHARACTERS)
def init_player_objects(active_players):
    players = []
    used_nums = []

    # generate initial random number
    num = random.randint(1, constants.NUM_SPRITES)

    # add chosen characters to used list
    for ap_val in active_players: used_nums.append(ap_val)

    # determine characters
    for ap_val in active_players:

        # player index
        i = len(players)

        # player is inactive
        if ap_val == -1:
            p = player.Player(i, -1)

        # choose random character
        elif ap_val == 0:

            while num in used_nums: num = random.randint(1, constants.NUM_SPRITES)

            p = player.Player(i, num)

            used_nums.append(num)

        # player chose character
        else:
            p = player.Player(i, ap_val)

        # append player to list
        players.append(p)

    return players


# GAMIFY LIST FOR SIMPLER USE THROUGHOUT GAME
# TODO: Check if unused
def gamify_list(list):
    gamified_list = [[], []]
    split_list = [list[:len(list) // 2], list[len(list) // 2:-1]]

    i = 0
    for round in split_list:

        for x in range(6): gamified_list[i].append([])

        j = 0
        for item in round:
            gamified_list[i][j].append(item)

            if j == 5:
                j = 0
            else:
                j += 1

        i += 1

    # add final jeopardy item
    gamified_list.append([[list[-1]]])

    return gamified_list


# CODE FROM: http://www.nerdparadise.com/tech/python/pygame/blitopacity/ ###
# CREATE SURFACE WITH GIVEN OPACITY
def blit_alpha(target, source, location, opacity):
    x = location[0]
    y = location[1]
    temp = pygame.Surface((source.get_width(), source.get_height())).convert()
    temp.blit(target, (-x, -y))
    temp.blit(source, (0, 0))
    temp.set_alpha(opacity)
    target.blit(temp, location)
##############################################################################
