import platform, pygame

# game information
################
MAX_GAME = 6861
NUM_SPRITES = 11
NUM_PLAYERS = 4
FORCE_GAME = 6861
################

# addressing
################
if "Windows" in platform.system():
	IMAGE_PATH = "..\\res\\images\\"
	FONT_PATH = "..\\res\\fonts\\"
	MUSIC_PATH = "..\\res\\music\\"
	TEMP_PATH = "..\\res\\temp\\"
else:
	IMAGE_PATH = "../res/images/"
	FONT_PATH = "../res/fonts/"
	MUSIC_PATH = "../res/music/"
	TEMP_PATH = "../res/temp/"
	
WEB_ADDR_CLUE = "http://www.j-archive.com/showgame.php?game_id="
WEB_ADDR_RESP = "http://j-archive.com/showgameresponses.php?game_id="
################

# default resolutions
################
pygame.init()
display_info = pygame.display.Info()
# DISPLAY_RES = (display_info.current_w, display_info.current_h)
DISPLAY_RES = (1360, 768)
BOARD_SIZE = (900, 600)
CHAR_SIZE = (180, 200)
################

# colour values
################
DARK_BLUE = 15, 30, 120
BLUE = 0, 80, 140
RED = 240, 0, 0
BLACK = 0, 0, 0
WHITE = 255, 255, 255
YELLOW = 200, 150, 30
ORANGE = 255, 100, 0
GREEN = 0, 128, 0
COLOR_KEY = 0, 255, 0
################

# states
################
MUSIC_ON = True
SFX_ON = True
################

# point value defaults
################
POINT_VALUES = [[100, 200, 300, 400, 500], [200, 400, 600, 800, 1000]]
################

# user events
################
END_FJ_EVENT = pygame.USEREVENT + 1
################

# static image surfaces
################
CHARACTERS_IMAGE = pygame.image.load(IMAGE_PATH + "chars.png")
ALEX_IMAGE = pygame.image.load(IMAGE_PATH + "alex.png")
LOGO_IMAGE = pygame.image.load(IMAGE_PATH + "logo.png")
DDBG_IMAGE = pygame.image.load(IMAGE_PATH + "ddbackground.png")
FJBG_IMAGE = pygame.image.load(IMAGE_PATH + "fjbackground.png")
MAINBG_IMAGE = pygame.image.load(IMAGE_PATH + "mainbackground.png")
PYGAME_IMAGE = pygame.image.load(IMAGE_PATH + "pygame.png")
ICON_IMAGE = pygame.image.load(IMAGE_PATH + "icon.png")
TOASTY_IMAGE = pygame.image.load(IMAGE_PATH + "toasty.png")
################

# sound objects
################
THEME_SOUND = pygame.mixer.Sound(MUSIC_PATH + "theme.ogg")
BUZZ_SOUND = pygame.mixer.Sound(MUSIC_PATH + "ringin.ogg")
TIMEOUT_SOUND = pygame.mixer.Sound(MUSIC_PATH + "timeout.ogg")
BOARDFILL_SOUND = pygame.mixer.Sound(MUSIC_PATH + "boardfill.ogg")
DAILYDOUBLE_SOUND = pygame.mixer.Sound(MUSIC_PATH + "dailydouble.ogg")
FINALJEP_SOUND = pygame.mixer.Sound(MUSIC_PATH + "finaljeopardy.ogg")
APPLAUSE_SOUND = pygame.mixer.Sound(MUSIC_PATH + "applause.ogg")
CHARSELECT_SOUND = pygame.mixer.Sound(MUSIC_PATH + "charselect.ogg")
################

NAMES_SOUND_ARR = []
for i in range(NUM_SPRITES+1):
	print i
	NAMES_SOUND_ARR.append(pygame.mixer.Sound(MUSIC_PATH + "name" + str(i) + ".ogg"))

# character names
################
CHARACTER_NAMES = ["Mystery Man", "Alex Trebek", "Sean Connery", "Burt Reynolds", "French Stewart", "Watson", "Bill Cosby", "Sharon Osbourne", "Keanu Reeves", "Kathy Griffin", "Bjork", "Jesus"]
################

# state constants
################
MAIN_STATE = 0
BET_STATE = 1
BUZZED_STATE = 2
SHOW_CLUE_STATE = 3
SHOW_RESP_STATE = 4
FINAL_BET_STATE = 5
FINAL_CHECK_STATE = 6
END_STATE = 7
################

# delay times
################
DELAY = 1000
CLUE_TIMEOUT = 15000
BUZZ_TIMEOUT = 8000
FINAL_TIMEOUT = 60000
################

# create font surfaces
################
KORINNA = []
HELVETICA = []
DIGITAL = []

for i in range(1, 65):
	KORINNA.append(pygame.font.Font(FONT_PATH + "korinna.ttf", i))
	HELVETICA.append(pygame.font.Font(FONT_PATH + "helvetica.ttf", i))
	DIGITAL.append(pygame.font.Font(FONT_PATH + "digital.ttf", i))
################
