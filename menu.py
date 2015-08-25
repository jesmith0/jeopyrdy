import pygame, gen

from constants import *

class Menu:

	def __init__(self, screen):
	
		self.screen = screen
		
		self.sfx_state = True
		self.music_state = True
		self.new_game = False
		
		self.cursor_loc = 0
		
		# generate surfaces
		self.start_text_surface = gen.menu_item("> ", "START GAME", True)
		self.newgame_text_surface = gen.menu_item("> ", "GET NEW GAME", False)
		self.sfx_text_surface = gen.menu_item("> SFX: ", "ON", False)
		self.music_text_surface = gen.menu_item("> MUSIC: ", "ON", False)
		
		# initial blit to screen
		self.__update_display()
		
	def update(self, input):
	
		if input:

			# P1 red button
			if int(input[0][0]):
			
				# START GAME
				if self.cursor_loc == 0: return False
				elif self.cursor_loc == 1: self.new_game = True
				elif self.cursor_loc == 2: self.sfx_state = not self.sfx_state
				elif self.cursor_loc == 3: self.music_state = not self.music_state
			
			# P1 blue button
			if int(input[0][1]):
			
				# UP
				if self.cursor_loc == 0: self.cursor_loc = 3
				else: self.cursor_loc -= 1
			
			# P1 yellow button			
			if int(input[0][4]):
			
				# DOWN
				if self.cursor_loc == 3: self.cursor_loc = 0
				else: self.cursor_loc += 1
		
			# only need to update when new input
			self.__update_display()
		
		return True
	
	# check if new game
	def get_new_game(self):
	
		if self.new_game:
			
			self.new_game = False
			return True
			
		else: return False
		
	def __exit_menu(self):
	
		# update game constants
		SFX_ON = self.sfx_state
		MUSIC_ON = self.music_state
	
		return False
	
	def __update_display(self):
	
		# update text surfaces based on state values
		self.__update_text_surfaces()
		
		# calculate offset for centering text
		offset = gen.menu_item(">", "GET NEW GAME", False).get_width()/2
		x_loc = DISPLAY_RES[0]/2 - offset - HELVETICA[50].size("")[0]
		
		# fill screen
		self.screen.fill(BLUE)
		
		# blit surfaces
		self.screen.blit(PYGAME_IMAGE, (DISPLAY_RES[0]/2-PYGAME_IMAGE.get_width()/2, 5))
		self.screen.blit(LOGO_IMAGE, (DISPLAY_RES[0]/2-LOGO_IMAGE.get_width()/2, 120))
		self.screen.blit(self.start_text_surface, (x_loc, 325))
		self.screen.blit(self.newgame_text_surface, (x_loc, 375))
		self.screen.blit(self.sfx_text_surface, (x_loc, 425))
		self.screen.blit(self.music_text_surface, (x_loc, 475))
		
	def __update_text_surfaces(self):
	
		# determine value of menu items
		if self.sfx_state: sfx_value = "ON"
		else: sfx_value = "OFF"
		
		if self.music_state: music_value = "ON"
		else: music_value = "OFF"
	
		# update text surfaces based on cursor location
		self.start_text_surface = gen.menu_item("> ", "START GAME", (self.cursor_loc == 0))
		self.newgame_text_surface = gen.menu_item("> ", "GET NEW GAME", (self.cursor_loc == 1))
		self.sfx_text_surface = gen.menu_item("> SFX: ", sfx_value, (self.cursor_loc == 2))
		self.music_text_surface = gen.menu_item("> MUSIC: ", music_value, (self.cursor_loc == 3))
		
		