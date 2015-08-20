import platform, pygame

# game information
################
MAX_GAME = 4985
################

# addressing
################
if "Windows" in platform.system():
	IMAGE_PATH = "images\\"
	FONT_PATH = "fonts\\"
	MUSIC_PATH = "music\\"
	TEMP_PATH = "temp\\"
else:
	IMAGE_PATH = "images/"
	FONT_PATH = "fonts/"
	MUSIC_PATH = "music/"
	TEMP_PATH = "temp/"
	
WEB_ADDR_CLUE = "http://www.j-archive.com/showgame.php?game_id="
WEB_ADDR_RESP = "http://j-archive.com/showgameresponses.php?game_id="
################

# default resolutions
################
pygame.init()
display_info = pygame.display.Info()
DISPLAY_RES = (display_info.current_w, display_info.current_h)
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
SOUND_ON = True
################

# point value defaults
################
POINT_VALUES = [[100, 200, 300, 400, 500], [200, 400, 600, 800, 1000]]
################

# static image surfaces
################
CHARACTERS_IMAGE = pygame.image.load(IMAGE_PATH + "chars.png")
ALEX_IMAGE = pygame.image.load(IMAGE_PATH + "alex.png")
LOGO_IMAGE = pygame.image.load(IMAGE_PATH + "logo.png")
DDBG_IMAGE = pygame.image.load(IMAGE_PATH + "ddbackground.jpg")
FJBG_IMAGE = pygame.image.load(IMAGE_PATH + "fjbackground.png")
################

# sound objects
################
THEME_SOUND = pygame.mixer.Sound(MUSIC_PATH + "theme.ogg")
BUZZ_SOUND = pygame.mixer.Sound(MUSIC_PATH + "ringin.ogg")
TIMEOUT_SOUND = pygame.mixer.Sound(MUSIC_PATH + "timeout.ogg")
BOARDFILL_SOUND = pygame.mixer.Sound(MUSIC_PATH + "boardfill.ogg")
DAILYDOUBLE_SOUND = pygame.mixer.Sound(MUSIC_PATH + "dailydouble.ogg")
FINALJEP_SOUND = pygame.mixer.Sound(MUSIC_PATH + "finaljeopardy.ogg")

RIGHT_SOUNDS = []

WRONG_SOUNDS = []
WRONG_SOUNDS.append(pygame.mixer.Sound(MUSIC_PATH + "alex_wrong.ogg"))
WRONG_SOUNDS.append(pygame.mixer.Sound(MUSIC_PATH + "sean_wrong.ogg"))
WRONG_SOUNDS.append(pygame.mixer.Sound(MUSIC_PATH + "burt_wrong.ogg"))
WRONG_SOUNDS.append(pygame.mixer.Sound(MUSIC_PATH + "french_wrong.ogg"))
################

# state constants
################
MAIN_STATE = 0
BET_STATE = 1
BUZZED_STATE = 2
SHOW_CLUE_STATE = 3
SHOW_RESP_STATE = 4
CHECK_RESP_STATE = 5
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