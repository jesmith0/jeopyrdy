import pygame, gen, util

from constants import *

class Menu:

	def __init__(self, screen):
	
		self.screen = screen
		
		self.sfx_state = True
		self.speech_state = True
		self.music_state = True
		self.new_game = False
		
		self.cursor_loc = 0
		self.game_date = None
		
		# which players are active
		self.active_players = [True, False, False, False]
		
		# prevents players from interfering with each other
		self.button_raised = [False, False, False, False]
		
		# mixer channel for theme music
		self.music_channel = THEME_SOUND.play(-1)
		
		# generate surfaces
		self.start_text_surface = gen.menu_item("> ", "START GAME", True)
		self.newgame_text_surface = gen.menu_item("> ", "GET NEW GAME", False)
		self.sfx_text_surface = gen.menu_item("> SFX: ", "ON", False)
		self.speech_text_surface = gen.menu_item("> SPEECH: ", "ON", False)
		self.music_text_surface = gen.menu_item("> MUSIC: ", "ON", False)
		self.gamedate_text_surface = gen.menu_item("  GETTING ", "GAME...", False)
		
		# initial blit to screen
		self.__update_display()
		
	def set_game_date(self, date):
	
		self.game_date = date
		print self.game_date
		self.gamedate_text_surface = gen.menu_item("", self.game_date, False)
		
	def update(self, input):
	
		if input:

			# P1 red button
			if int(input[0][0]):
			
				# START GAME
				if self.cursor_loc == 0:
				
					# if music off, release channel
					if not self.music_state: self.music_channel.stop()
					return [False, self.active_players, self.sfx_state, self.speech_state]
				
				elif self.cursor_loc == 1:
				
					# trigger get new game function
					self.new_game = True
					self.gamedate_text_surface = gen.menu_item("  GETTING ", "GAME...", False)
					
				elif self.cursor_loc == 2:
				
					# play daily double sound to indicate sfx on
					self.sfx_state = not self.sfx_state
					if self.sfx_state: DAILYDOUBLE_SOUND.play()
					
				elif self.cursor_loc == 3:
				
					self.speech_state = not self.speech_state
				
				elif self.cursor_loc == 4:
				
					# pause/unpause music accordingly
					self.music_state = not self.music_state
					if self.music_state: self.music_channel.set_volume(1)
					else: self.music_channel.set_volume(0)
			
			# P1 blue button
			elif int(input[0][1]):
			
				# UP
				if self.cursor_loc == 0: self.cursor_loc = 4
				else: self.cursor_loc -= 1
			
			# P1 yellow button			
			elif int(input[0][4]):
			
				# DOWN
				if self.cursor_loc == 4: self.cursor_loc = 0
				else: self.cursor_loc += 1
			
			# P2 red button
			if int(input[1][0]): self.active_players[1] = not self.active_players[1]
			elif not int(input[1][0]): self.button_raised[1] = True
				
			# P3 red button
			if int(input[2][0]): self.active_players[2] = not self.active_players[2]
			elif not int(input[2][0]): self.button_raised[2] = True
			
			# P4 red button
			if int(input[3][0]): self.active_players[3] = not self.active_players[3]
			elif not int(input[3][0]): self.button_raised[3] = True
		
		# only need to update when new input
		self.__update_display()
		
		return [True, self.active_players, self.sfx_state, self.speech_state]
	
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
		self.screen.blit(LOGO_IMAGE, (DISPLAY_RES[0]/2-LOGO_IMAGE.get_width()/2, 70))
		self.screen.blit(self.gamedate_text_surface, (DISPLAY_RES[0]/2 - self.gamedate_text_surface.get_width()/2, 275))
		self.screen.blit(self.start_text_surface, (x_loc, 325))
		self.screen.blit(self.newgame_text_surface, (x_loc, 375))
		self.screen.blit(self.sfx_text_surface, (x_loc, 425))
		self.screen.blit(self.speech_text_surface, (x_loc, 475))
		self.screen.blit(self.music_text_surface, (x_loc, 525))
		
		# display players
		self.__blit_all_characters(self.screen)
		
	def __update_text_surfaces(self):
	
		# determine value of menu items
		if self.sfx_state: sfx_value = "ON"
		else: sfx_value = "OFF"
		
		if self.speech_state: speech_value = "ON"
		else: speech_value = "OFF"
		
		if self.music_state: music_value = "ON"
		else: music_value = "OFF"
	
		# update text surfaces based on cursor location
		self.start_text_surface = gen.menu_item("> ", "START GAME", (self.cursor_loc == 0))
		self.newgame_text_surface = gen.menu_item("> ", "GET NEW GAME", (self.cursor_loc == 1))
		self.sfx_text_surface = gen.menu_item("> SFX: ", sfx_value, (self.cursor_loc == 2))
		self.speech_text_surface = gen.menu_item("> SPEECH: ", speech_value, (self.cursor_loc == 3))
		self.music_text_surface = gen.menu_item("> MUSIC: ", music_value, (self.cursor_loc == 4))
	
	def __blit_all_characters(self, screen):
	
		char_surfs = []
		for i in range(4):
			char_surfs.append(gen.char_surface(0).convert())
		
		# width interval dependant on number of players
		width_interval = DISPLAY_RES[0]/4
		
		blit_loc = (((width_interval*(i)) + width_interval/2) - char_surfs[i].get_width()/2, DISPLAY_RES[1]-char_surfs[i].get_height())
		
		# blit all characters
		for i in range(4):
		
			# calculate location
			blit_loc = (((width_interval*(i)) + width_interval/2) - char_surfs[i].get_width()/2, DISPLAY_RES[1]-char_surfs[i].get_height())
			
			if not self.active_players[i]: util.blit_alpha(screen, char_surfs[i], blit_loc, 25)
			else: screen.blit(char_surfs[i], blit_loc)