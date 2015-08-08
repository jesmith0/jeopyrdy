import pygame, random, pyttsx
import constants, util, player

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
		
		self.music = res[1]
		self.theme_sound = self.music[0]		# theme song played on loop
		self.dd_sound = self.music[1]			# play when daily double clue displayed
		self.ringin_sound = self.music[2]		# play when a player buzzes in
		self.timeout_sound = self.music[3]		# play when clue / player times outs
		self.board_fill = self.music[4]			# play at beginning of main rounds
		self.char_wrong_sounds = self.music[5]	# play on incorrect response (list of sound objects)
		
		# CLUE LIBRARY
		self.cat = util.gamify_list(lib[0])		# lists are of the following form:
		self.clue = util.gamify_list(lib[1])	#
		self.resp = util.gamify_list(lib[2])	# list[round][category][clue
		
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
		
		# PLAYER OBJECTS
		self.players = []
		
		for num in range(self.num_players):
			self.players.append(player.Player(num))
		
		# CREATE SURFACES
		self.board_surf = util.generate_board_surface()				# returns a blank board surface
		self.blank_board_surf = util.generate_board_surface()		# returns a blank board surface (kept blank)
		self.cursor_surf = util.generate_cursor_surface()			# returns a cursor surface
		self.value_surf = util.generate_value_surface()				# returns a list of two lists of value surfaces
		self.cat_surf = util.generate_category_surface(self.cat)	# returns a list of three lists of category surfaces
		self.correct_surf = util.generate_correct_surface()			# returns a surface to choose between 'correct/incorrect'
		
		self.pyttsx_engine = pyttsx_engine
		
		# LOOP THEME
		self.theme_sound.play(-1)
		self.board_fill.play()
		
		# INITIAL UPDATE
		self.update()
		
		
	def update(self, input = None):
	
		### CHANGE STATES ###
		
		# buzz delay
		if self.game_clock >= 900: delay = True
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
					
						self.players[self.buzzed_player].sub_from_score(constants.POINT_VALUES[self.cur_round][self.cursor_loc[1]])
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
				# if int(input[self.buzzed_player][0]) == 1 and delay:
				if (int(input[self.buzzed_player][2]) == 1 or int(input[self.buzzed_player][3]) == 1): # and delay:
				
					# update state
					self.check_resp = False
					self.show_main = True
					self.game_clock = 0
					
					# if correct
					# if self.menu_cursor_loc == 0:
					if int(input[self.buzzed_player][2]) == 1:
						self.players[self.buzzed_player].add_to_score(constants.POINT_VALUES[self.cur_round][self.cursor_loc[1]])
						self.active_player = self.buzzed_player
					#else:
					elif int(input[self.buzzed_player][3]) == 1:
						self.players[self.buzzed_player].sub_from_score(constants.POINT_VALUES[self.cur_round][self.cursor_loc[1]])
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
		
		clue_surf = util.generate_text_surface((self.cat[self.cur_round][self.cursor_loc[0]][0]).upper())
	
		# if clue display
		if show_clue:
			char_surf = self.alex_surf
			text_surf = util.generate_text_surface(self.clue[self.cur_round][self.cursor_loc[0]][self.cursor_loc[1]])
			tts = self.clue[self.cur_round][self.cursor_loc[0]][self.cursor_loc[1]]
		elif buzzed_in:
			#char_surf = self.__generate_char_surf(self.buzzed_player)
			char_surf = self.players[self.buzzed_player].char_surface
			text_surf = util.generate_text_surface(self.clue[self.cur_round][self.cursor_loc[0]][self.cursor_loc[1]])
		elif show_resp:
			#char_surf = self.__generate_char_surf(self.buzzed_player)
			char_surf = self.players[self.buzzed_player].char_surface
			text_surf = util.generate_text_surface(self.resp[self.cur_round][self.cursor_loc[0]][self.cursor_loc[1]])
			tts = self.resp[self.cur_round][self.cursor_loc[0]][self.cursor_loc[1]]
		
		# scale character surface
		scaled_image = pygame.transform.scale(char_surf, (char_surf.get_width()*3, char_surf.get_height()*3))
		
		# blit character and text to screen
		util.blit_alpha(self.screen, scaled_image, (0, constants.DISPLAY_RES[1]-scaled_image.get_height()), 100)
		self.screen.blit(char_surf, (0, constants.DISPLAY_RES[1]-char_surf.get_height()))
		self.screen.blit(clue_surf, (constants.DISPLAY_RES[0]/2 - constants.BOARD_SIZE[0]/2, -200))
		self.screen.blit(text_surf, (constants.DISPLAY_RES[0]/2 - constants.BOARD_SIZE[0]/2,0))
		
		# read clue/response
		if (show_clue or show_resp) and not self.tts_done:
			self.pyttsx_engine.say(tts.decode('utf-8'))
			self.tts_done = True
	
	# BLIT MAIN DISPLAY TO SCREEN
	def __display_main(self):
	
		self.screen.fill(constants.BLUE)
		self.__update_board_surf()
		
		char_surfs = []
		
		# generate character surfaces
		for i in range(self.num_players):
			#char_surfs.append(self.__generate_char_surf(i))
			char_surfs.append(self.players[i].char_surface)
			
		active_char = char_surfs[self.active_player]
		scaled_image = pygame.transform.scale(active_char, (active_char.get_width()*3, active_char.get_height()*3))
		
		# blit active char
		util.blit_alpha(self.screen, scaled_image, (0, constants.DISPLAY_RES[1]-scaled_image.get_height()), 100)
		
		# blit game board
		self.screen.blit(self.board_surf, (constants.DISPLAY_RES[0]/2-constants.BOARD_SIZE[0]/2,0))
		
		width_interval = constants.DISPLAY_RES[0]/self.num_players
		
		# blit all characters
		for i in range(self.num_players):
			self.screen.blit(char_surfs[i], (((width_interval*(i)) + width_interval/2) - char_surfs[i].get_width()/2, constants.DISPLAY_RES[1]-char_surfs[i].get_height()))
	
	# BLIT CHECK RESPONSE DISPLAY TO SCREEN
	# correct = 0, incorrect = 1
	def __display_check(self):

		#correct_surf = util.generate_text_surface('CORRECT')
		#incorrect_surf = util.generate_text_surface('INCORRECT')
		
		#char_surf = self.__generate_char_surf(self.buzzed_player)
		char_surf = self.players[self.buzzed_player].char_surface
		scaled_image = pygame.transform.scale(char_surf, (char_surf.get_width()*3, char_surf.get_height()*3))
		
		self.screen.fill(constants.BLUE)
		
		#if self.menu_cursor_loc == 0: active_surf = correct_surf
		#else: active_surf = incorrect_surf
		
		util.blit_alpha(self.screen, scaled_image, (0, constants.DISPLAY_RES[1]-scaled_image.get_height()), 100)
		self.screen.blit(char_surf, (0, constants.DISPLAY_RES[1]-char_surf.get_height()))
		
		#self.screen.blit(active_surf, (constants.DISPLAY_RES[0]/2-constants.BOARD_SIZE[0]/2,0))
		self.screen.blit(self.correct_surf, (constants.DISPLAY_RES[0]/2-constants.BOARD_SIZE[0]/2,0))
	
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