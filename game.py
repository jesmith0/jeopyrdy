import pygame, constants, random, pyttsx

class Game:

	def __init__(self, screen, res, lib, num_players, pyttsx_engine):
	
		self.screen = screen	# screen surface
		
		# GAME RESOURCES
		self.images = res[0]
		self.alex_surf = self.images[0]		# image of Alex Trebek
		self.chars_surf = self.images[1]	# image of all four player characters
		self.logo_surf = self.images[2]		# image of Jeopardy logo
		self.board_surf = None				# generated at the end of initialization
		self.value_surf = None				# generated at the end of initialization
		
		self.fonts = res[1]
		self.korinna_font = self.fonts[0]	# font sizes 1-64
		self.helvetica_font = self.fonts[1] # addressable as 0-63
		self.digital_font = self.fonts[2]	# Helvetica not recognized
		
		self.music = res[2]
		self.theme_sound = self.music[0]		# theme song played on loop
		self.dd_sound = self.music[1]			# laser beam sounds
		self.ringin_sound = self.music[2]		# buzz in sound
		self.timeout_sound = self.music[3]		# play when clue times outs
		self.board_fill = self.music[4]
		self.char_wrong_sounds = self.music[5]	# list of sound objects
		
		# CLUE LIBRARY
		self.cat = self.__organize_list(lib[0])		# lists are of the following form:
		self.clue = self.__organize_list(lib[1])	#
		self.resp = self.__organize_list(lib[2])	# list[round][category][clue]
		
		# STATE VARIABLES
		self.num_players = 4						# determined in menu
		self.cur_round = 0							# DJ = 1, FJ = 2
		self.cursor_loc = [0,0]						# game cursor location
		self.active_player = 0						# 0-3 players
		self.buzzed_player = 0						# player currently buzzed in
		self.clue_arr = self.__generate_clue_arr()	# each list corresponds to a round
		self.points = [0, 0, 0, 0]					# each players points
		self.menu_cursor_loc = 0					# cursor for menu and misc
		
		self.game_clock = 0
		self.clue_timeout = False
		self.buzzin_timeout = False
		self.button_raised = False
		self.tts_done = False
		
		self.show_main = True
		self.show_clue = False
		self.show_resp = False
		self.check_resp = False
		self.buzzed_in = False
		
		# CREATE SURFACES
		self.board_surf = self.__generate_board_surf()			# returns a blank board surface
		self.blank_board_surf = self.__generate_board_surf()	# returns a blank board surface (kept blank)
		self.cursor_surf = self.__generate_cursor_surf()		# returns a cursor surface
		self.value_surf = self.__generate_value_surf()			# returns a list of two lists of value surfaces
		self.cat_surf = self.__generate_cat_surf()				# returns a list of three lists of category surfaces
		
		self.pyttsx_engine = pyttsx_engine
		
		# LOOP THEME
		self.theme_sound.play(-1)
		self.board_fill.play()
		
		# INITIAL UPDATE
		self.update()
		
		
	def update(self, input = None):
	
		### CHANGE STATES ###
		
		# buzz delay
		if self.game_clock >= 1500: delay = True
		else: delay = False
		
		# TIMER
		if self.show_clue:
		
			# about 10 seconds
			if self.game_clock >= 15000:
			
				self.timeout_sound.play()
			
				# skip buzz_in state
				self.show_clue = False
				self.show_resp = True
				self.clue_timeout = True
				self.game_clock = 0
				#self.buzzed_player = self.active_player
			
		elif self.buzzed_in:
		
			# about 5 seconds
			if self.game_clock >= 8000:
			
				self.timeout_sound.play()
			
				# mark player incorrect
				self.buzzed_in = False
				self.show_resp = True
				self.buzzin_timeout = True
				self.game_clock = 0
				#self.buzzed_player = self.active_player
		
		# only if there is input
		if input:
		
			if self.show_main:
			
				# ONLY ACTIVE PLAYER IN CONTROL ON MAIN SCREEN
				if int(input[self.active_player][0]) == 1:
				
					if self.clue_arr[self.cur_round][self.cursor_loc[0]][self.cursor_loc[1]+1] == 0:
						
						if self.show_main:
						
							self.show_main = False
							self.show_clue = True
							self.game_clock = 0		# reset game clock for timer on show_clue
						
				# move cursor
				elif int(input[self.active_player][1]) == 1: self.__update_cursor_loc(1)	# up = 1
				elif int(input[self.active_player][2]) == 1: self.__update_cursor_loc(2)	# right = 2
				elif int(input[self.active_player][3]) == 1: self.__update_cursor_loc(3)	# left = 3
				elif int(input[self.active_player][4]) == 1: self.__update_cursor_loc(4)	# down = 4
				
			elif self.show_clue:
			
				# ANY PLAYER MAY BUZZ IN
				i = 0
				buzzed_players = []
				for buzzer in input[:self.num_players]:
					if int(buzzer[0]) == 1: buzzed_players.append(i)
					i += 1
				
				# only if someone has buzzed in
				if len(buzzed_players) > 0:
				
					# choose random player, if both buzzed together
					self.buzzed_player = buzzed_players[random.randint(0, len(buzzed_players)-1)]
					
					# play 'ring in' sound
					self.ringin_sound.play()
					
					# update state
					self.show_clue = False
					self.buzzed_in = True
					self.tts_done = False
					self.game_clock = 0		# reset game clock for timer on show_clue
				
			elif self.buzzed_in:
			
				# requires player to lift button (prevents)
				#################################################################################
				### THIS NEEDS TO BE DONE FOR EVERY BUZZ-IN STATE ###############################
				### IT'S" THE REASON BOARD NAVIGATION CAN BE INFLUENCED BY NON-ACTIVE PLAYERS ###
				#################################################################################
				if not self.button_raised and int(input[self.buzzed_player][0]) == 0:
					self.button_raised = True
			
				# ONLY BUZZED PLAYER MAY CONTINUE
				elif self.button_raised and int(input[self.buzzed_player][0]) == 1 and delay:
				
					# update state
					self.buzzed_in = False
					self.show_resp = True
					self.game_clock = 0
					self.button_raised = False
				
			elif self.show_resp:
			
				# ONLY BUZZED PLAYER MAY CONTINUE
				if int(input[self.buzzed_player][0]) == 1 and delay:
				
					if self.clue_timeout or self.buzzin_timeout: self.show_main = True
					else: self.check_resp = True
					
					# deduct points
					if self.buzzin_timeout:
					
						self.points[self.buzzed_player] -= constants.POINT_VALUES[self.cur_round][self.cursor_loc[1]]
						self.char_wrong_sounds[self.buzzed_player].play()
					
					self.show_resp = False
					self.clue_timeout = False
					self.buzzin_timeout = False
					self.tts_done = False
					self.game_clock = 0
					
					# update clue array
					self.clue_arr[self.cur_round][self.cursor_loc[0]][self.cursor_loc[1]+1] = 1
					
					# check if round over
					if self.__check_round():
					
						if self.cur_round < 2:
							self.cur_round += 1
							self.board_fill.play()
						else: return False
					
			elif self.check_resp:
			
				# ONLY BUZZED PLAYER MAY CONTINUE
				if int(input[self.buzzed_player][0]) == 1 and delay:
				
					# update state
					self.check_resp = False
					self.show_main = True
					self.game_clock = 0
					
					# if correct
					if self.menu_cursor_loc == 0:
						self.points[self.buzzed_player] += constants.POINT_VALUES[self.cur_round][self.cursor_loc[1]]
						self.active_player = self.buzzed_player
					else:
						self.points[self.buzzed_player] -= constants.POINT_VALUES[self.cur_round][self.cursor_loc[1]]
						self.char_wrong_sounds[self.buzzed_player].play()
						
					self.menu_cursor_loc = 0
					
				else:
					for dir_button in input[self.buzzed_player][1:]:
						if int(dir_button) == 1:
							if self.menu_cursor_loc == 0: self.menu_cursor_loc = 1
							else: self.menu_cursor_loc = 0
					
			
		### DISPLAY CHANGES ###
		
		# blit clues and categories to board surface
		if self.show_main: self.__display_main()
		elif self.show_clue: self.__display_clue_resp(self.show_clue, self.buzzed_in, self.show_resp)		
		elif self.buzzed_in: self.__display_clue_resp(self.show_clue, self.buzzed_in, self.show_resp)
		elif self.show_resp: self.__display_clue_resp(self.show_clue, self.buzzed_in, self.show_resp)
		elif self.check_resp: self.__display_check()
		
		# check if game over
		return True
	
	def tick_game_clock(self, ms):
	
		self.game_clock += ms
	
	# ORGANIZE LIST FOR SIMPLER USE THROUGHOUT GAME
	# assumes list is full
	def __organize_list(self, list):
	
		organized_list = [[],[]]
		split_list = [list[:len(list)/2], list[len(list)/2:-1]]
		
		i = 0
		for round in split_list:
		
			for x in range(6): organized_list[i].append([])
		
			j = 0
			for item in round:
				organized_list[i][j].append(item)
				
				if j == 5: j = 0
				else: j += 1
			
			i += 1
		
		# add final jeopardy item
		organized_list.append([[list[-1]]])
				
		return organized_list
	
	# GENERATES GAME BOARD SURFACE
	def __generate_board_surf(self):
	
		width_interval = constants.BOARD_SIZE[0]/6
		height_interval = constants.BOARD_SIZE[1]/6
		color = constants.YELLOW
	
		# create surface and fill with dark blue
		board_surf = pygame.Surface(constants.BOARD_SIZE)
		board_surf.fill(constants.DARK_BLUE)
		
		# draw horizontal, then vertical line
		for i in range(7):
			pygame.draw.line(board_surf, color, (0,i*height_interval), (constants.BOARD_SIZE[0],i*height_interval), 3)
			pygame.draw.line(board_surf, color, (i*width_interval,0), (i*width_interval,constants.BOARD_SIZE[1]), 3)
		
		return board_surf
	
	# GENERATES A CURSOR SURFACE
	def __generate_cursor_surf(self):
	
		# cursor size based on board
		width = constants.BOARD_SIZE[0]/6
		height = constants.BOARD_SIZE[1]/6
		color = constants.WHITE
		
		cursor_surf = pygame.Surface((width+1, height+1))
		
		# set colour key and alpha
		cursor_surf.fill(constants.COLOR_KEY)
		cursor_surf.set_colorkey(constants.COLOR_KEY)
		cursor_surf.set_alpha(255)
		
		# horizontal lines
		pygame.draw.line(cursor_surf, color, (0,0), (width,0), 5)
		pygame.draw.line(cursor_surf, color, (0,height), (width,height), 5)
		
		# vertical lines
		pygame.draw.line(cursor_surf, color, (0,0), (0,height), 5)
		pygame.draw.line(cursor_surf, color, (width,0), (width,height), 5)
	
		return cursor_surf
	
	# GENERATES A LIST OF TWO LISTS
	# each list corresponds to a different round
	# each contains a list of Surfaces
	def __generate_value_surf(self):
		
		width = constants.BOARD_SIZE[0]/6 - 20
		height = constants.BOARD_SIZE[1]/6 - 20
		font_size = 40
		color = constants.YELLOW
		
		value_surf = []
		
		for value_set in constants.POINT_VALUES:
		
			value_surf.append([])
			
			for value in value_set:
				value_surf[-1].append(self.__generate_text_surf(str(value), width, height, font_size, color, True, constants.DARK_BLUE))
		
		return value_surf
	
	# GENERATES A LIST OF TWO LISTS
	# each corresponds to a round
	# each contains a list of Surfaces
	def __generate_cat_surf(self):
	
		width = constants.BOARD_SIZE[0]/6 - 20
		height = constants.BOARD_SIZE[1]/6 - 20
		font_size = 20
		color = constants.YELLOW
			
		cat_surf = []
	
		for round in self.cat[:-1]:
		
			cat_surf.append([])
			
			for cat in round:
				cat_surf[-1].append(self.__generate_text_surf(cat[0], width, height, font_size, color, True, constants.DARK_BLUE))
				
		return cat_surf
	
	# GENERATES A SURFACE FROM TEXT
	# for display active clues/responses
	def __generate_text_surf(self, text, max_width = constants.BOARD_SIZE[0], max_height = constants.BOARD_SIZE[1],
								font_size = 40, color = constants.WHITE, helvetica = True, color_key = constants.BLUE):
		
		text_surf = pygame.Surface((max_width, max_height)).convert()
		
		text_surf.fill(color_key)
		text_surf.set_colorkey(color_key)
		text_surf.set_alpha(255)
		
		line_list = ['']
		line_len = 0
		
		if helvetica: font = self.helvetica_font
		else: font = self.digital_font
		
		word_list = text.split()
		
		italic = False
		underline = True
		
		for word in word_list:
					
			# if first word on line
			if line_list[-1] == '':
			
				line_list[-1] += word
				line_len += font[font_size].size(word)[0]
				
			else:
			
				word_size = font[font_size].size(' ' + word)
				line_len += word_size[0]
				
				if line_len <= max_width:
					line_list[-1] += ' ' + word
					line_len += word_size[0]
				else:
					line_list.append(word)
					line_len = word_size[0]
					
		# blit each line to a single surface
		i = 0
		for line in line_list:
			text_surf.blit(font[font_size].render(line, 1, color), (max_width/2 - font[font_size].size(line)[0]/2, max_height/2-(len(line_list)*font_size)/2+i*font_size))
			i += 1
				
		return text_surf
	
	# GENERATES A LIST OF TWO LISTS
	# each list corresponds to a different round
	# each contains a set of ints
	def __generate_clue_arr(self):
	
		clue_arr = [[],[]]
		
		# exclude final jeopardy round
		for i in range(len(self.clue[:-1])):
			for j in range(len(self.clue[i])):
			
				# new list for each category
				clue_arr[i].append([0])
				
				for clue in self.clue[i][j]:
				
					# if no clue, mark as seen
					if clue: clue_arr[i][j].append(0)
					else: clue_arr[i][j].append(1)
					
		return clue_arr
	
	# GENERATES A SURFACE FOR CHARACTER
	# num corresponds to player
	def __generate_char_surf(self, num):
	
		char_surf = pygame.Surface(constants.CHAR_SIZE).convert()
		
		char_surf.fill(constants.DARK_BLUE)
		char_surf.set_colorkey(constants.DARK_BLUE)
		char_surf.set_alpha(255)
		
		char_surf.blit(self.chars_surf, (0, 0), (num*180, 0, 180, 200))
		
		# BLIT SCORE
		if self.points[num] >= 0: color = constants.WHITE
		else: color = constants.RED
		
		score_surf = self.__generate_text_surf(str(self.points[num]), char_surf.get_width(), char_surf.get_height(), 30, color, False)
		char_surf.blit(score_surf, (0, 70))
		
		return char_surf
	
	# UPDATES CLUES AND CATEGORIES AND CURSOR ON BOARD SURFACE
	def __update_board_surf(self):
	
		width_interval = constants.BOARD_SIZE[0]/6
		height_interval = constants.BOARD_SIZE[1]/6
	
		# blit board surface with blank board
		self.board_surf.blit(self.blank_board_surf, (0,0))
		
		# blit cursor to board
		self.board_surf.blit(self.cursor_surf, (self.cursor_loc[0]*width_interval,(self.cursor_loc[1]+1)*height_interval))
	
		# blit board surface with values
		i = 0
		for category in self.clue_arr[self.cur_round]:
		
			self.board_surf.blit(self.cat_surf[self.cur_round][i], (i*width_interval+10,10))
		
			j = 0
			for clue in category[1:]:
				if clue == 0:
				
					self.board_surf.blit(self.value_surf[self.cur_round][j], (i*width_interval+10, (j+1)*height_interval+10))
				
				j += 1
			i += 1

	# BLIT CLUE/RESPONSE DISPLAY TO SCREEN
	# show_clue = True if CLUE DISPLAY
	# show_clue = False if RESPONSE DISPLAY
	def __display_clue_resp(self, show_clue, buzzed_in, show_resp):
	
		self.screen.fill(constants.BLUE)
		
		clue_surf = self.__generate_text_surf((self.cat[self.cur_round][self.cursor_loc[0]][0]).upper())
	
		# if clue display
		if show_clue:
			char_surf = self.alex_surf
			text_surf = self.__generate_text_surf(self.clue[self.cur_round][self.cursor_loc[0]][self.cursor_loc[1]])
			tts = self.clue[self.cur_round][self.cursor_loc[0]][self.cursor_loc[1]]
		elif buzzed_in:
			char_surf = self.__generate_char_surf(self.buzzed_player)
			text_surf = self.__generate_text_surf(self.clue[self.cur_round][self.cursor_loc[0]][self.cursor_loc[1]])
		elif show_resp:
			char_surf = self.__generate_char_surf(self.buzzed_player)
			text_surf = self.__generate_text_surf(self.resp[self.cur_round][self.cursor_loc[0]][self.cursor_loc[1]])
			tts = self.resp[self.cur_round][self.cursor_loc[0]][self.cursor_loc[1]]
		
		# scale character surface
		scaled_image = pygame.transform.scale(char_surf, (char_surf.get_width()*3, char_surf.get_height()*3))
		
		# blit character and text to screen
		self.__blit_alpha(self.screen, scaled_image, (0, constants.DISPLAY_RES[1]-scaled_image.get_height()), 100)
		self.screen.blit(char_surf, (0, constants.DISPLAY_RES[1]-char_surf.get_height()))
		self.screen.blit(clue_surf, (200, -200))
		self.screen.blit(text_surf, (constants.DISPLAY_RES[0]/2 - constants.BOARD_SIZE[0]/2,0))
		
		# read clue/response
		if (show_clue or show_resp) and not self.tts_done:
			self.pyttsx_engine.say(tts)
			self.tts_done = True
	
	# BLIT MAIN DISPLAY TO SCREEN
	def __display_main(self):
	
		self.screen.fill(constants.BLUE)
		self.__update_board_surf()
		
		char_surfs = []
		
		# generate character surfaces
		for i in range(self.num_players):
			char_surfs.append(self.__generate_char_surf(i))
			
		active_char = char_surfs[self.active_player]
		scaled_image = pygame.transform.scale(active_char, (active_char.get_width()*3, active_char.get_height()*3))
		
		# blit active char
		self.__blit_alpha(self.screen, scaled_image, (0, constants.DISPLAY_RES[1]-scaled_image.get_height()), 100)
		
		# blit game board
		self.screen.blit(self.board_surf, (constants.DISPLAY_RES[0]/2-constants.BOARD_SIZE[0]/2,0))
		
		width_interval = constants.DISPLAY_RES[0]/self.num_players
		
		# blit all characters
		for i in range(self.num_players):
			self.screen.blit(char_surfs[i], (((width_interval*(i)) + width_interval/2) - char_surfs[i].get_width()/2, constants.DISPLAY_RES[1]-char_surfs[i].get_height()))
	
	# BLIT CHECK RESPONSE DISPLAY TO SCREEN
	# correct = 0, incorrect = 1
	def __display_check(self):

		correct_surf = self.__generate_text_surf('CORRECT')
		incorrect_surf = self.__generate_text_surf('INCORRECT')
		
		char_surf = self.__generate_char_surf(self.buzzed_player)
		scaled_image = pygame.transform.scale(char_surf, (char_surf.get_width()*3, char_surf.get_height()*3))
		
		self.screen.fill(constants.BLUE)
		
		if self.menu_cursor_loc == 0: active_surf = correct_surf
		else: active_surf = incorrect_surf
		
		self.__blit_alpha(self.screen, scaled_image, (0, constants.DISPLAY_RES[1]-scaled_image.get_height()), 100)
		self.screen.blit(char_surf, (0, constants.DISPLAY_RES[1]-char_surf.get_height()))
		
		self.screen.blit(active_surf, (constants.DISPLAY_RES[0]/2-constants.BOARD_SIZE[0]/2,0))
	
	# UPDATE CURSON BASED ON BUTTON DIRECTION
	# up = 1, right = 2, left = 3, down = 4
	def __update_cursor_loc(self, direction):
	
		if self.show_main:
		
			if direction == 1:		
				if self.cursor_loc[1] > 0: self.cursor_loc[1] -= 1
				else: self.cursor_loc[1] = 4
				
			elif direction == 2:
				if self.cursor_loc[0] < 5: self.cursor_loc[0] += 1
				else: self.cursor_loc[0] = 0
			
			elif direction == 3:
				if self.cursor_loc[0] > 0: self.cursor_loc[0] -= 1
				else: self.cursor_loc[0] = 5
			
			elif direction == 4:
				if self.cursor_loc[1] < 4: self.cursor_loc[1] += 1
				else: self.cursor_loc[1] = 0
	
	# check to see if current round is over
	def __check_round(self):
	
		cat_done = True
		for clue in self.clue_arr[self.cur_round][self.cursor_loc[0]][1:]:
			if clue == 0: cat_done = False
		if cat_done: self.clue_arr[self.cur_round][self.cursor_loc[0]][0] = 1
		
		round_done = True
		for cat in self.clue_arr[self.cur_round]:
			if cat[0] == 0: round_done = False
			
		return round_done
	
	# CODE FROM: http://www.nerdparadise.com/tech/python/pygame/blitopacity/
	def __blit_alpha(self, target, source, location, opacity):
		x = location[0]
		y = location[1]
		temp = pygame.Surface((source.get_width(), source.get_height())).convert()
		temp.blit(target, (-x, -y))
		temp.blit(source, (0, 0))
		temp.set_alpha(opacity)        
		target.blit(temp, location)