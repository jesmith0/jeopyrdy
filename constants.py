import platform, pygame

# game information
################
MAX_GAME = 4985
NUM_SPRITES = 4
################

# addressing
################
if "Windows" in platform.system():
	IMAGE_PATH = "images\\"
	FONT_PATH = "fonts\\"
	MUSIC_PATH = "music\\"
else:
	IMAGE_PATH = "images/"
	FONT_PATH = "fonts/"
	MUSIC_PATH = "music/"
	
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
COLOR_KEY = 0, 255, 0
################

# point value defaults
################
POINT_VALUES = [[100, 200, 300, 400, 500], [200, 400, 600, 800, 1000]]
################