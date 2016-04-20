import pygame, gen, util

from constants import *

class Menu:

	def __init__(self, screen, theme_channel, buzzers):
	
		self.SCREEN = screen
		self.THEME_CHANNEL = theme_channel
		self.BUZZERS = buzzers
		
		# play if channel inactive
		if not theme_channel.get_busy(): theme_channel.play(THEME_SOUND, -1)
		
		# menu state
		self.charsel_state = False
		
		# info state
		self.input_state = bool(buzzers)
		self.sfx_state = True
		self.speech_state = True
		self.music_state = True
		self.new_game = False
		self.check_buzzers = False
		
		# misc variables
		self.cursor_loc = 0
		self.game_date = None
		self.charsel_dimension = [((NUM_SPRITES + 1) / 2) , (NUM_SPRITES + 1) % 2]
		
		# which players are active
		self.active_players = [-1, -1, -1, -1]
		self.player_cursor_pos = [0, 0, 0, 0]
		self.char_selected = [False, True, True, True]
		
		# text surfaces
		self.start_text_surface = None
		self.newgame_text_surface = None
		self.check_buzzers_surface = None
		self.sfx_text_surface = None
		self.speech_text_surface = None
		self.music_text_surface = None
		self.gamedate_text_surface = None
		
		# cursor surfaces
		self.cursor_surfaces = [gen.cursor_surface(180, 120, WHITE, "P1"), gen.cursor_surface(180, 120, WHITE, "P2"), gen.cursor_surface(180, 120, WHITE, "P3"), gen.cursor_surface(180, 120, WHITE, "P4")]
		self.border_surface = gen.cursor_surface(180, 120, YELLOW)
		
		# buzzer status surface
		self.buzzer_prompt_surface = gen.text_surface("BUZZERS FOUND: ", 175, 50, 20)
		self.buzzer_status_surface = self.__get_buzzer_status_surface()
		
		# initial blit to screen
		self.__update_display()
		
	def set_game_date(self, date):
	
		print self.game_date
	
		self.game_date = date
		self.gamedate_text_surface = gen.menu_item("", self.game_date, False)
		
		self.__update_display()
		
	def update_buzzers(self, buzzers):
	
		if bool(self.BUZZERS) != bool(buzzers):
			self.input_state = bool(buzzers)
			
		self.BUZZERS = buzzers
		
	def __get_pos_from_num(self, num):
	
		y_pos = num / (self.charsel_dimension[0])
		
		if y_pos > 0: x_pos = num % (y_pos * self.charsel_dimension[0])
		else: x_pos = num
	
		return [x_pos, y_pos]
		
	def __get_num_from_pos(self, pos):
	
		return pos[1]*self.charsel_dimension[0] + pos[0]
		
	def __move_cursor(self, num, dir):
	
		### calculate this ###
		num_rows = 1
		
		# get current position
		pos = self.__get_pos_from_num(self.player_cursor_pos[num])
		
		if dir == "up":
		
			if pos[1] > 0: pos[1] -= 1
			else: pos[1] = num_rows + self.charsel_dimension[1]
			
		elif dir == "down":
		
			if pos[1] < num_rows + self.charsel_dimension[1]: pos[1] += 1
			else: pos[1] = 0
		
		elif dir == "right":
	
			if pos[0] < self.charsel_dimension[0] - 1: pos[0] += 1
			else: pos[0] = 0
			
		elif dir == "left":
		
			if pos[0] > 0: pos[0] -= 1
			else: pos[0] = self.charsel_dimension[0] - 1

		self.player_cursor_pos[num] = self.__get_num_from_pos(pos)
		
	def __select_character(self, i):
	
		if not self.char_selected[i]:
		
			if not (self.player_cursor_pos[i] in self.active_players) or self.player_cursor_pos[i] == 0:
			
				# set character selected
				self.active_players[i] = self.player_cursor_pos[i]
				self.char_selected[i] = True
				
				# deactive character select cursor
				self.player_cursor_pos[i] = -1
			
		else:
		
			self.active_players[i] = -1
			self.player_cursor_pos[i] = 0
			self.char_selected[i] = False
	
	def __check_menu(self):
	
		list = self.char_selected
	
		return not (list[0] and list[1] and list[2] and list[3])
		
	def update(self, input):
	
		if input:
			
			# CHARACTER SELECT
			if self.charsel_state:
			
				for i in range(len(input)):
				
					if input[i][0]: self.__select_character(i)
					elif input[i][1]: self.__move_cursor(i, "up")
					elif input[i][2]: self.__move_cursor(i, "right")
					elif input[i][3]: self.__move_cursor(i, "left")
					elif input[i][4]: self.__move_cursor(i, "down")
			
			# MAIN MENU
			else:
			
				# P1 red button
				if int(input[0][0]):
				
					# START GAME
					if self.cursor_loc == 0:
					
						# if music off, release channel
						if not self.music_state: self.THEME_CHANNEL.stop()
						
						# move to character select screen
						self.charsel_state = True
						
						# inactive players set to (-1, -1) cursor position
						for i in range(len(self.char_selected)):
						
							if self.char_selected[i]: self.player_cursor_pos[i] = -1
					
					# GET NEW GAME
					elif self.cursor_loc == 1:
					
						# trigger get new game function
						self.new_game = True
						self.game_date = None
					
					# INPUT TYPE
					elif self.cursor_loc == 2:
					
						# change input type
						if self.input_state: self.input_state = False
						elif not self.input_state and self.BUZZERS: self.input_state = True
					
					# SOUND FX
					elif self.cursor_loc == 3:
					
						# play daily double sound to indicate sfx on
						self.sfx_state = not self.sfx_state
						if self.sfx_state: DAILYDOUBLE_SOUND.play()
					
					# TEXT-TO-SPEECH
					elif self.cursor_loc == 4:
					
						self.speech_state = not self.speech_state
					
					# PLAY MUSIC
					elif self.cursor_loc == 5:
					
						# pause/unpause music accordingly
						self.music_state = not self.music_state
						if self.music_state: self.THEME_CHANNEL.set_volume(1)
						else: self.THEME_CHANNEL.set_volume(0)
				
				# P1 blue button
				elif int(input[0][1]):
				
					# UP
					if self.cursor_loc == 0: self.cursor_loc = 5
					else: self.cursor_loc -= 1
				
				# P1 yellow button			
				elif int(input[0][4]):
				
					# DOWN
					if self.cursor_loc == 5: self.cursor_loc = 0
					else: self.cursor_loc += 1
				
				# P2-P4 red button
				for i in range(1, len(input)):
				
					if int(input[i][0]): self.char_selected[i] = not self.char_selected[i]
			
			# only need to update when new input
			self.__update_display()
			
		return self.__menu_return(self.__check_menu())
	
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
		
		# fill screen
		self.SCREEN.fill(BLUE)
		
		# calculate offset for centering text
		offset = gen.menu_item("> INPUT: ", "KEYBOARD", False).get_width()/2
		x_loc = DISPLAY_RES[0]/2 - offset - HELVETICA[30].size("")[0]
		
		# blit surfaces
		if self.charsel_state:
		
			self.__blit_character_select(self.SCREEN)
			#for i in range(NUM_SPRITES+1): self.SCREEN.blit(CHARACTERS_IMAGE, (180*i + 10, 50), (i*180, 0, 180, 120))
		
		else:
			self.SCREEN.blit(PYGAME_IMAGE, (DISPLAY_RES[0]/2-PYGAME_IMAGE.get_width()/2, 5))
			self.SCREEN.blit(LOGO_IMAGE, (DISPLAY_RES[0]/2-LOGO_IMAGE.get_width()/2, 70))
			self.SCREEN.blit(self.gamedate_text_surface, (DISPLAY_RES[0]/2 - self.gamedate_text_surface.get_width()/2, 275))
			self.SCREEN.blit(self.start_text_surface, (x_loc, 325))
			self.SCREEN.blit(self.newgame_text_surface, (x_loc, 360))
			self.SCREEN.blit(self.check_buzzers_surface, (x_loc, 395))
			self.SCREEN.blit(self.sfx_text_surface, (x_loc, 430))
			self.SCREEN.blit(self.speech_text_surface, (x_loc, 465))
			self.SCREEN.blit(self.music_text_surface, (x_loc, 500))
			self.SCREEN.blit(self.buzzer_prompt_surface, (0, 0))
			self.SCREEN.blit(self.buzzer_status_surface, (165, 0))
		
		# display players
		self.__blit_all_characters(self.SCREEN)
		
	def __update_text_surfaces(self):
	
		# determine value of menu items
		if self.input_state: input_value = "BUZZERS"
		else: input_value = "KEYBOARD"
		
		if self.sfx_state: sfx_value = "ON"
		else: sfx_value = "OFF"
		
		if self.speech_state: speech_value = "ON"
		else: speech_value = "OFF"
		
		if self.music_state: music_value = "ON"
		else: music_value = "OFF"
		
		# update buzzer status surface
		self.buzzer_status_surface = self.__get_buzzer_status_surface()
		
		# update game date
		if not self.game_date: self.gamedate_text_surface = gen.menu_item("  GETTING ", "GAME...", False)
	
		# update text surfaces based on cursor location
		self.start_text_surface = gen.menu_item("> ", "START GAME", (self.cursor_loc == 0))
		self.newgame_text_surface = gen.menu_item("> ", "GET NEW GAME", (self.cursor_loc == 1))
		self.check_buzzers_surface = gen.menu_item("> INPUT: ", input_value, (self.cursor_loc == 2))
		self.sfx_text_surface = gen.menu_item("> SFX: ", sfx_value, (self.cursor_loc == 3))
		self.speech_text_surface = gen.menu_item("> SPEECH: ", speech_value, (self.cursor_loc == 4))
		self.music_text_surface = gen.menu_item("> MUSIC: ", music_value, (self.cursor_loc == 5))
		
	def __blit_character_select(self, screen):
	
		x_dim = self.charsel_dimension[0]
		y_dim = 2 + self.charsel_dimension[1]
		
		x_home = DISPLAY_RES[0]/2 - (200*x_dim)/2
		y_home = 200
	
		for i in range(y_dim):
			for j in range(x_dim):
			
				charnum = (x_dim * i) + j
				
				char_surf = pygame.Surface((180, 120))
				char_surf.fill(BLUE)
				char_surf.blit(CHARACTERS_IMAGE, (0, 0), (charnum*180, 0, 180, 120))
				
				blit_loc = (x_home + 200*j, 50 + 170*i)
				
				if (charnum in self.active_players) and charnum != 0: util.blit_alpha(screen, char_surf, blit_loc, 25)
				else: screen.blit(char_surf, blit_loc)

				screen.blit(self.border_surface, (x_home + 200*j, 50 + 170*i))
				
				it = 0
				for num in self.player_cursor_pos:
				
					pos = self.__get_pos_from_num(num)
					if not self.char_selected[it]: screen.blit(self.cursor_surfaces[it], (x_home + 200*pos[0], 50 + 170*pos[1]))
					it += 1
	
	def __blit_all_characters(self, screen):
	
		char_surfs = []
		for i in range(4):
			if self.charsel_state:
			
				if self.char_selected[i]: charnum = self.active_players[i]
				else: charnum = self.player_cursor_pos[i]
				char_surfs.append(gen.char_surface(charnum).convert())
				
			else: char_surfs.append(gen.char_surface(0).convert())
		
		# width interval dependant on number of players
		width_interval = DISPLAY_RES[0]/4
		
		blit_loc = (((width_interval*(i)) + width_interval/2) - char_surfs[i].get_width()/2, DISPLAY_RES[1]-char_surfs[i].get_height())
		
		# blit all characters
		for i in range(4):
		
			# calculate location
			blit_loc = (((width_interval*(i)) + width_interval/2) - char_surfs[i].get_width()/2, DISPLAY_RES[1]-char_surfs[i].get_height())
			
			if self.char_selected[i]: util.blit_alpha(screen, char_surfs[i], blit_loc, 25)
			else: self.SCREEN.blit(char_surfs[i], blit_loc)
			
	def __get_buzzer_status_surface(self):
	
		if self.BUZZERS:
			color = WHITE
			text = "YES"
		else:
			color = RED
			text = "NO"
			
		return gen.text_surface(text, 50, 50, 20, color)
		
	def __menu_return(self, menu_active = True):
	
		return [menu_active, self.active_players, self.sfx_state, self.speech_state, self.input_state]