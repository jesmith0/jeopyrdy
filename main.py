import pygame, os							# FOR GUI
import usb.core, usb.util					# FOR USB BUZZER INTERFACING
import random, urllib, urllib2				# FOR GENERATING A CLUE LIBRARY
import constants							# LOCAL CONSTANTS
from game import *							# Game OBJECT CLASS

# GLOBAL VARIABLES
image_count = 0

def buzz_setup(buzz_dev):

	# SETUP USB BUZZERS
	if buzz_dev is None:
		raise ValueError('Device not found')

	# may need to claim device from kernel
	# see: http://www.orangecoat.com/how-to/read-and-decode-data-from-your-mouse-using-this-pyusb-hack
		
	buzz_dev.set_configuration()
	
	buzz_cfg = buzz_dev.get_active_configuration()
	buzz_intf = buzz_cfg[(0,0)]
	
	buzz_ep = usb.util.find_descriptor(buzz_intf, buzz_intf[0])
	
	if buzz_ep is None:
		raise ValueError('Endpoint not found')
	else:
		print "BUZZERS (setup):\tOK"
		
	return buzz_ep[0]
	
def gamify_input(buzz_input):

	if buzz_input == None: return None
	else:
	
		bin_input = []
		
		# convert to binary and normalize
		for b in buzz_input[2:]:
			bin_input.append(bin(b)[2:])
			while(len(bin_input[-1]) < 8):
				bin_input[-1] = '0' + bin_input[-1]
		
		# hard coded from buzzer device
		b1 = [bin_input[0][7], bin_input[0][3], bin_input[0][4], bin_input[0][5], bin_input[0][6]]
		b2 = [bin_input[0][2], bin_input[1][6], bin_input[1][7], bin_input[0][0], bin_input[0][1]]
		b3 = [bin_input[1][5], bin_input[1][1], bin_input[1][2], bin_input[1][3], bin_input[1][4]]
		b4 = [bin_input[1][0], bin_input[2][4], bin_input[2][5], bin_input[2][6], bin_input[2][7]]
		
		return [b1, b2, b3, b4]

def scrub_text(text):

	# remove static tags
	new_text = text.replace('&amp;', '&')
	new_text = new_text.replace('<br />', ' ')
	new_text = new_text.replace('<br/>', ' ')
	new_text = new_text.replace('<i>','')
	new_text = new_text.replace('</i>','')
	new_text = new_text.replace('<u>','')
	new_text = new_text.replace('</u>','')
	new_text = new_text.replace('</em>','')
	new_text = new_text.replace('</a>','')
	
	# remove emphasis tag
	if (not new_text.find('<em') == -1):
		new_text = new_text[:new_text.find('<em')] + new_text[new_text.find('>')+2:]
	
	# for each hyperlink tag
	while (not new_text.find('<a') == -1):
			
		# removes every hyperlink reference tag from text
		new_text = new_text[:new_text.find('<a')] + new_text[new_text.find('">')+2:]
		
	return new_text

def get_resource(text, num):

	if not text.find('<a') == -1:
	
		# attempt to pull image from j-archive.com
		try:
			res = urllib.urlretrieve(text[text.find("http://"):text.find('.jpg')+4], constants.TEMP_PATH + "temp" + str(num) + ".jpg")
			print res
			return res
		except:
			# google image search
			print "url non-responsive"
	
	return None
	
	# TODO: DETECT 404 ERRORS
	
def lib_setup():

	cat = []
	clue = []
	resp = []
	res = []
	
	res_count = 0

	# RANDOMLY GENERATE USEABLE GAME NUMBER
	game_num = str(random.randint(1, constants.MAX_GAME))
	
	print game_num
	
	# REDUCE WEBPAGE TO RELEVANT LINES (also sets display window caption)
	for line in urllib2.urlopen(constants.WEB_ADDR_CLUE + game_num).readlines():
		if 'class="clue_text">' in line:
			clue.append(line)
			res.append(None)
		elif 'class="category_name">' in line: cat.append(line)
		elif 'id="game_title">' in line: pygame.display.set_caption(line[line.find('id="game_title"><h1>')+20:line.find('</h1>')].upper())
		
	for line in urllib2.urlopen(constants.WEB_ADDR_RESP + game_num).readlines():
		if 'class="correct_response">' in line: resp.append(line)
	
	# FORMAT LIBRARY INFO
	for i in range(len(clue)):
	
		unscrubed_clue = clue[i][clue[i].find('class="clue_text">')+18:clue[i].find('</td>')]
		
		hold_res = get_resource(unscrubed_clue, res_count)
		if hold_res: res_count += 1
		
		res[i] = hold_res
		clue[i] = scrub_text(unscrubed_clue)
		
	for i in range(len(cat)):
		cat[i] = scrub_text(cat[i][cat[i].find('class="category_name">')+22:cat[i].find('</td>')])
		
	for i in range(len(resp)):
		resp[i] = scrub_text(resp[i][resp[i].find('class="correct_response">')+25:resp[i].find('</em>')])
	
	# RETURN LIBRARY
	return [cat, clue, resp]
	
	# TODO: ASSERT UNVISITED CLUES ARE CONSIDERED
	
def res_setup():

	# LOAD IMAGES
	images = []
	images.append(pygame.image.load(constants.IMAGE_PATH + "alex.png"))
	images.append(pygame.image.load(constants.IMAGE_PATH + "chars.png"))
	images.append(pygame.image.load(constants.IMAGE_PATH + "logo.png"))
	images.append(pygame.image.load(constants.IMAGE_PATH + "board.png"))
	
	# LOAD MUSIC
	music = []
	music.append(pygame.mixer.Sound(constants.MUSIC_PATH + "theme.ogg"))
	music.append(pygame.mixer.Sound(constants.MUSIC_PATH + "dailydouble.ogg"))
	music.append(pygame.mixer.Sound(constants.MUSIC_PATH + "ringin.ogg"))
	music.append(pygame.mixer.Sound(constants.MUSIC_PATH + "timeout.ogg"))
	music.append(pygame.mixer.Sound(constants.MUSIC_PATH + "boardfill.ogg"))
	
	wrong = []
	wrong.append(pygame.mixer.Sound(constants.MUSIC_PATH + "alex_wrong.ogg"))
	wrong.append(pygame.mixer.Sound(constants.MUSIC_PATH + "sean_wrong.ogg"))
	wrong.append(pygame.mixer.Sound(constants.MUSIC_PATH + "burt_wrong.ogg"))
	wrong.append(pygame.mixer.Sound(constants.MUSIC_PATH + "french_wrong.ogg"))
	music.append(wrong)
	
	print "RESOURCES (setup):\tOK"
	
	return [images, music]
	
def main():

	menu_active = True
	game_active = False
	num_players = 1

	# SETUP USB BUZZERS
	buzz_dev = usb.core.find()
	try: buzz_listener = buzz_setup(buzz_dev)
	except: print "BUZZERS (setup):\tFAILED"
	
	# SETUP CLUE LIBRARY
	# primitive solution to ensure no unseen clues
	lib_valid = False
	while (not lib_valid):
		lib = lib_setup()
		if len(lib[1]) == 61: lib_valid = True
	print "LIBRARY (setup):\tOK"
	
	# INITIALIZE ALL IMPORTED PYGAME MODULES
	pygame.init()
	
	# SETUP GAME RESOURCES
	res = res_setup()
	
	# INITIALIZE SCREEN SURFACE
	screen = pygame.display.set_mode(constants.DISPLAY_RES, pygame.FULLSCREEN)
	#screen = pygame.display.set_mode(constants.DISPLAY_RES)
	pygame.mouse.set_visible(False)
	clock = pygame.time.Clock()
	pyttsx_engine = pyttsx.init()
	screen.fill(constants.BLUE)
	
	# MENU LOOP
	while (menu_active):
	
		print "\nMENU LOOP"
		menu_active = False
		game_active = True
		
	# CREATE GAME OBJECT FROM res AND lib AND num_players
	game = Game(screen, res, lib, num_players, pyttsx_engine)
		
	# GAME LOOP
	while (game_active):
	
		# update display, pump event queue
		pygame.display.flip()
		pyttsx_engine.runAndWait()
		
		# check for ESCAPE key
		for event in pygame.event.get():
			if event.type == pygame.KEYDOWN:
				if event.key == pygame.K_ESCAPE:
					game_active = False
		
		# if ESCAPE key, break before update
		if game_active == False: continue
		
		# update game clock
		game.tick_game_clock(clock.tick())

		# get input from buzzers
		try:
			buzz_input = buzz_dev.read(buzz_listener.bEndpointAddress, buzz_listener.wMaxPacketSize)
		except usb.core.USBError as e:
			buzz_input = None
			if e.args == ('Operation timed out'): continue
			
		# send input to game, update
		print gamify_input(buzz_input)
		game_active = game.update(gamify_input(buzz_input))
	
	# RETURN USB DEVICE AND PYGAME RESOURCES TO SYSTEM
	pygame.quit()
	usb.util.dispose_resources(buzz_dev)
	
	print "PROGRAM HALT"

if __name__ == "__main__": main()
