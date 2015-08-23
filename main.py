import pygame, os							# FOR GUI
import usb.core, usb.util					# FOR USB BUZZER INTERFACING
import random, urllib, urllib2				# FOR GENERATING A CLUE LIBRARY
import constants							# LOCAL CONSTANTS
import library								# Block OBJECT CLASS
import util
from game import *							# Game OBJECT CLASS
	
def main():

	menu_active = True
	game_active = False
	num_players = 4

	# SETUP USB BUZZERS
	buzz_dev = usb.core.find()
	try: buzz_listener = util.buzz_setup(buzz_dev)
	except: print "BUZZERS (setup):\tFAILED"
	
	# INITIALIZE ALL IMPORTED PYGAME/PYTTSX MODULES
	pygame.init()
	pyttsx_engine = pyttsx.init()
	
	# CREATE CLOCK OBJECT
	clock = pygame.time.Clock()
	
	# INITIALIZE SCREEN SURFACE
	#screen = pygame.display.set_mode(constants.DISPLAY_RES, pygame.FULLSCREEN)
	screen = pygame.display.set_mode(constants.DISPLAY_RES)
	pygame.mouse.set_visible(False)
	
	screen.fill(constants.BLUE)
	
	# SETUP CLUE LIBRARY
	lib = util.lib_setup()
	
	# MENU LOOP
	while (menu_active):
	
		print "\nMENU LOOP"
		menu_active = False
		game_active = True
		
	# CREATE GAME OBJECT FROM res AND lib AND num_players
	game = Game(screen, lib, num_players, pyttsx_engine)
		
	# GAME LOOP
	while (game_active):
	
		# update display, pump event queue
		pygame.display.flip()
		pyttsx_engine.runAndWait()
		
		# check for ESCAPE key
		for event in pygame.event.get():
			if event.type == pygame.KEYDOWN:
			
				# exit from pygame
				if event.key == pygame.K_ESCAPE:
					game_active = False
				
				# jump to final jeopardy
				elif event.key == pygame.K_k:
					game.state.set_final_jeopardy()
					game.cur_round = 2
					game.force_update_round()
		
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
		print util.gamify_input(buzz_input)
		game_active = game.update(util.gamify_input(buzz_input))
	
	# RETURN USB DEVICE AND PYGAME RESOURCES TO SYSTEM
	pygame.quit()
	usb.util.dispose_resources(buzz_dev)
	
	print "PROGRAM HALT"

if __name__ == "__main__": main()
