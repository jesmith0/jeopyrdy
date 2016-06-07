import pygame, os					# FOR GUI
import pyttsx                       # FOR TEXT-TO-SPEECH
import random, urllib, urllib2		# FOR GENERATING A CLUE LIBRARY
import library, constants, util		# LOCAL LIBRARIES
import menu as m					# Menu OBJECT CLASS
import game as g					# Game OBJECT CLASS
	
def main():

	menu_active = True
	game_active = False
	game_set = False

	menu = None
	game = None
	buzzers = None
	
	timeout = 0
	
	# INITIALIZE ALL IMPORTED PYGAME/PYTTSX MODULES
	pygame.init()
	pyttsx_engine = pyttsx.init()
	
	# CREATE CLOCK OBJECT
	clock = pygame.time.Clock()
	
	# INITIALIZE SCREEN SURFACE
	#screen = pygame.display.set_mode(constants.DISPLAY_RES, pygame.FULLSCREEN)
	screen = pygame.display.set_mode(constants.DISPLAY_RES)
	pygame.mouse.set_visible(False)
	
	# SET ICON AND CAPTION
	pygame.display.set_caption("PYTHON Jeopardy")
	pygame.display.set_icon(constants.ICON_IMAGE)
	
	# CREATE THEME MUSIC CHANNEL
	theme_channel = pygame.mixer.Channel(0)
	
	# INITIAL CHECK FOR USB BUZZERS
	buzzers = util.get_buzzers()
	
	# GAME LOOP
	while (menu_active or game_active):
	
		# CREATE MENU/GAME OBJECTS
		if menu_active and not menu: menu = m.Menu(screen, theme_channel, buzzers)
		if game_active and not game: game = g.Game(screen, lib, active_players, pyttsx_engine, sfx_on, speech_on, input_type)
	
		# UPDATE DISPLAY
		pygame.display.flip()
		
		# RUN PYTTSX
		# pyttsx_engine.runAndWait()
		
		# GENERATE NEW GAME
		if not game_set:
		
			game_set = True
			
			# setup clue library
			setup_ret = util.lib_setup()
			lib = setup_ret[0]
			
			# update menu
			menu.set_game_date(setup_ret[1][0])
			menu.update(None)
			
		# UPDATE GAME CLOCK
		passed_time = clock.tick()
		if game_active: game.tick_game_clock(passed_time)
				
		# CHECK TIMEOUT
		if timeout <= 2000: timeout += passed_time
		else:
			
			# recheck buzzers, update menu
			if menu_active:
				if buzzers: buzzers.quit()
				buzzers = util.get_buzzers()
				menu.update_buzzers(buzzers)
			
			# update game
			elif game_active: game.update(None)
			
			# reset timeout
			timeout = 0
			
			# clear events
			pygame.event.clear(pygame.JOYBUTTONDOWN)
			pygame.event.clear(pygame.JOYBUTTONUP)
		
		# GET EVENTS FROM QUEUE
		for event in pygame.event.get():

			print event

			# final jeopardy over
			if event.type == constants.END_FJ_EVENT:

				game.state.fj_timeout = True
		
			# exit from pygame
			if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
			
				game_active = False
				menu_active = False

			elif event.type == pygame.KEYDOWN and event.key == pygame.K_BACKSPACE:

				game_set = False
				game_active = False
				menu_active = True
				game = None
				menu = None
				break
					
			# jump to final jeopardy
			elif event.type == pygame.KEYDOWN and event.key == pygame.K_TAB:
				
				game.state.set_final_jeopardy()
				game.cur_round = 2
				game.force_update_round()
			
			# check for button down
			elif event.type == pygame.KEYDOWN or event.type == pygame.JOYBUTTONDOWN:
				
				if game_active:
				
					# update game object
					game_active = game.update(util.gamify_input(event), event)
					
					# return to main menu
					if game.return_to_menu():
						
						game_set = False
						game_active = False
						menu_active = True
						game = None
						menu = None
						break
								
				elif menu_active:
				
					# update menu object
					menu_ret = menu.update(util.gamify_input(event))
					
					menu_active = menu_ret[0]
					active_players = menu_ret[1]
					sfx_on = menu_ret[2]
					speech_on = menu_ret[3]
					input_type = menu_ret[4]
					
					if menu.get_new_game(): game_set = False
					
					if not menu_active: game_active = True
	
	# RETURN USB DEVICE AND PYGAME RESOURCES TO SYSTEM
	pygame.quit()
	
	# DELETE PULLED IMAGE FILES
	util.dtf()
	
	print "PROGRAM HALT"

if __name__ == "__main__": main()
