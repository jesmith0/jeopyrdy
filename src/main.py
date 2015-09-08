import pygame, os					# FOR GUI
import random, urllib, urllib2		# FOR GENERATING A CLUE LIBRARY
import library, constants, util		# LOCAL LIBRARIES
import pyttsx
import menu as m					# Menu OBJECT CLASS
import game as g					# Game OBJECT CLASS
	
def main():

	menu_active = True
	game_active = False
	game_set = False

	menu = None
	game = None
	buzzer = None
	
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
	
	# GAME LOOP
	while (menu_active or game_active):
	
		# CREATE MENU/GAME OBJECTS
		if menu_active and not menu: menu = m.Menu(screen)
		if game_active and not game: game = g.Game(screen, lib, active_players, pyttsx_engine, sfx_on, speech_on)
	
		# UPDATE DISPLAY
		pygame.display.flip()
		
		# RUN PYTTSX
		pyttsx_engine.runAndWait()
		
		# SETUP USB BUZZERS
		while(not buzzer):
		
			for i in range(0, pygame.joystick.get_count()):
	
				if pygame.joystick.Joystick(i).get_name() == 'Buzz':
					buzzer = pygame.joystick.Joystick(i)
					buzzer.init()
		
		# GENERATE NEW GAME
		if not game_set:
		
			setup_ret = util.lib_setup()
			lib = setup_ret[0]
			menu.set_game_date(setup_ret[1][0])
			game_set = True
			
		# UPDATE GAME CLOCK
		passed_time = clock.tick()
		if game_active: game.tick_game_clock(passed_time)
				
		# CHECK TIMEOUT
		if timeout <= 500: timeout += passed_time
		else:
			if menu_active: menu.update(None)
			elif game_active: game.update(None)
			timeout = 0
			pygame.event.clear(pygame.JOYBUTTONDOWN)
			pygame.event.clear(pygame.JOYBUTTONUP)
		
		# GET EVENTS FROM QUEUE
		for event in pygame.event.get():
		
			# check for escape
			if event.type == pygame.KEYDOWN:
			
				# exit from pygame
				if event.key == pygame.K_ESCAPE:
					game_active = False
					menu_active = False
					
				# jump to final jeopardy
				elif event.key == pygame.K_k:
					game.state.set_final_jeopardy()
					game.cur_round = 2
					game.force_update_round()
			
			# check for button down
			elif event.type == pygame.JOYBUTTONDOWN or event.type == pygame.JOYBUTTONUP:
				
				if game_active:
				
					# update game object
					game_active = game.update(util.gamify_input(event.button, event.type == pygame.JOYBUTTONUP))
					
					# return to main menu
					if game.return_to_menu():
						
						game_set = False
						game_active = False
						menu_active = True
						
						game = None
						menu = None
								
				elif menu_active:
				
					menu_ret = menu.update(util.gamify_input(event.button, event.type == pygame.JOYBUTTONUP))
					
					menu_active = menu_ret[0]
					active_players = menu_ret[1]
					sfx_on = menu_ret[2]
					speech_on = menu_ret[3]
					
					if menu.get_new_game(): game_set = False
					if not menu_active: game_active = True
	
	# RETURN USB DEVICE AND PYGAME RESOURCES TO SYSTEM
	pygame.quit()
	
	# DELETE PULLED IMAGE FILES
	util.dtf()
	
	print "PROGRAM HALT"

if __name__ == "__main__": main()
