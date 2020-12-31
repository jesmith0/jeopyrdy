import constants
import library
import os
import platform
import player
import pygame
import random
import re
import urllib
import urllib2
import wikipedia

# GLOBAL VARIABLES
image_count = 0


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
    path = os.path.join(os.getcwd(), constants.TEMP_PATH)

    try:
        print query
        page = wikipedia.page(query)

    except wikipedia.exceptions.DisambiguationError as de:

        try:
            # use first suggestion
            page = wikipedia.page((str(de).split('\n'))[1])
        except:
            print "some other error"
            return None

    except wikipedia.exceptions.PageError as pe:
        print pe.message
        return None

    matches = []
    jpg = re.compile('.*\.jpg')

    for image in page.images:

        result = jpg.match(image)
        if result: matches.append(image)

    if matches:
        try:
            res = urllib.urlretrieve(matches[0], path + "wiki" + str(num) + ".jpg")
            print res[0]
            return res[0]
        except:
            print "### JEOPARDY ERROR ###"
            print query
            print matches
            print "COULD NOT RETRIEVE IMAGE FROM WIKIPEDIA"

    else:
        return None


# PULL MEDIA RESOURCES FROM J-ARCHIVE
def get_resource(text, num):
    path = os.path.join(os.getcwd(), constants.TEMP_PATH)
    url = ''

    img_prog = re.compile('.*<a href=".*\.jpg".*')
    result = img_prog.match(text)

    # check if IMAGE resource tag is present (all j-archive images are jpg)
    if result:

        # pull url from clue
        split = text.split('>')
        for item in split:
            trim = re.search('http:\/\/.*\.jpg', item)
            try:
                url = trim.group(0)
                break
            except:
                continue

        # url is now ready to be retrieved

        try:
            # retrieve url data
            res = urllib.urlretrieve(url, path + "ja" + str(num) + ".jpg")

            # ensure content type is image, else resource is not available
            if 'Content-Type: text/html' in str(res[1]): return '404'

            print res[0]

            # return image
            return res[0]

        except Exception as e:
            print e
            print "ERROR OPENING " + str(url)

            # indicate that resource tag present, but no resource obtained
            return "404"

    # if no resource tag present
    else:
        return None


# PULL GAME DATA FROM J-ARCHIVE
def parse_jarchive():
    cat = []
    clue = []
    resp = []
    res = []
    info = []

    res_count = 0

    # RANDOMLY GENERATE USEABLE GAME NUMBER
    if constants.FORCE_GAME:
        game_num = str(constants.FORCE_GAME)
    else:
        game_num = str(random.randint(1, constants.MAX_GAME))

    print game_num

    # REDUCE WEBPAGE TO RELEVANT LINES (also sets display window caption)
    # retrieves categories and clues
    for line in urllib2.urlopen(constants.WEB_ADDR_CLUE + game_num).readlines():
        if 'class="clue_text">' in line:
            clue.append(line)
            res.append(None)
        elif 'class="category_name">' in line:
            cat.append(line)
        elif 'id="game_title">' in line:
            info.append(line[line.find('id="game_title"><h1>') + 20:line.find('</h1>')].upper())

    # retrieves responses
    for line in urllib2.urlopen(constants.WEB_ADDR_RESP + game_num).readlines():
        if 'class="correct_response">' in line: resp.append(line)

    ### FORMAT LIBRARY INFO ###

    # POPULATE CLUES TO LIBRARY
    for i in range(len(clue)):

        unscrubed_clue = clue[i][clue[i].find('class="clue_text">') + 18:clue[i].find('</td>')]
        clue[i] = scrub_text(unscrubed_clue)

        # attempt to grab resource from j-archive
        res[i] = get_resource(unscrubed_clue, res_count)

        # increment resource count if one is supposed to exist
        if res[i]: res_count += 1

    # POPULATE CATEGORIES TO LIBRARY
    for i in range(len(cat)):
        cat[i] = scrub_text(cat[i][cat[i].find('class="category_name">') + 22:cat[i].find('</td>')])

    # POPULATE RESPONSE TO LIBRARY
    for i in range(len(resp)):

        resp[i] = scrub_text(resp[i][resp[i].find('class="correct_response">') + 25:resp[i].find('</em>')])

        # grab image from Wikipedia if 404ed
        if res[i] == '404': res[i] = get_img_from_wiki(resp[i], i)

    # RETURN LIBRARY
    return [cat, clue, resp, res, info]


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
def lib_setup():
    # primitive solution to ensure no unseen clues
    parse_valid = False

    while not parse_valid:
        parsed_data = parse_jarchive()
        if len(parsed_data[1]) == 61: parse_valid = True

    print "LIBRARY (setup):\tOK"

    return [gen_lib_object(parsed_data), parsed_data[-1]]


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
        except:
            num = -1


# CREATE PYGAME JOYSTICK OBJECT OF USB BUZZERS
def get_buzzers():
    pygame.joystick.quit()
    pygame.joystick.init()

    # TODO: Check for possible memory leak

    buzzer = None

    for i in range(0, pygame.joystick.get_count()):

        if pygame.joystick.Joystick(i).get_name() == 'Buzz':
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
    split_list = [list[:len(list) / 2], list[len(list) / 2:-1]]

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
