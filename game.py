import pygame, random, pyttsx
import constants, util, player, state, time

class Game:

	def __init__(self, screen, lib, num_players, pyttsx_engine):
	
		self.screen = screen
		self.lib = lib
		
		# STATE VARIABLES
		self.state = state.State()
		self.num_players = 4						# determined in menu
		self.cur_round = 0							# DJ = 1, FJ = 2
		self.cursor_loc = [0,0]						# game cursor location
		self.points = [0, 0, 0, 0]					# each players points
		self.cur_bet = 0
		self.cur_block = self.lib[self.cur_round][self.cursor_loc[0]][self.cursor_loc[1]]
		
		self.game_clock = 0
		self.dd = False
		
		# PLAYER OBJECTS
		self.players = []
		
		for num in range(self.num_players):
			self.players.append(player.Player(num))
		
		# GENERATE STATIC SURFACES
		self.board_surf = util.generate_board_surface()				# returns a blank board surface
		self.blank_board_surf = util.generate_board_surface()		# returns a blank board surface (kept blank)
		self.cursor_surf = util.generate_cursor_surface()			# returns a cursor surface
		self.value_surf = util.generate_value_surface()				# returns a list of two lists of value surfaces
		self.correct_surf = util.generate_correct_surface()			# returns a surface to choose between 'correct/incorrect'
		
		self.pyttsx_engine = pyttsx_engine
		
		# SET DAILY DOUBLES
		self.__set_dailydoubles()
		
		# LOOP THEME
		# constants.THEME_SOUND.play(-1)
		constants.BOARDFILL_SOUND.play()
		
		# INITIAL UPDATE
		self.update()
		
	def tick_game_clock(self, ms): self.game_clock += ms
		
	def update(self, input = None):
	
		if input:
			
			# MAIN SCREEN GAME LOGIC
			if self.state.main:
				
				if int(input[self.state.active_player][1]) == 1: self.__update_cursor_loc(1)	# up = 1
				elif int(input[self.state.active_player][2]) == 1: self.__update_cursor_loc(2)	# right = 2
				elif int(input[self.state.active_player][3]) == 1: self.__update_cursor_loc(3)	# left = 3
				elif int(input[self.state.active_player][4]) == 1: self.__update_cursor_loc(4)	# down = 4
				
				# set current block to correspond with cursor's position
				self.cur_block = self.lib[self.cur_round][self.cursor_loc[0]][self.cursor_loc[1]]
			
			# BET SCREEN MAIN LOGIC
			elif self.state.bet:
			
				# determine maximum bet from player score
				if self.players[self.state.active_player].score <= 1000: max_bet = 1000
				else: max_bet = self.players[self.state.active_player].score
			
				# set maximum bet
				if self.state.count == 0: self.cur_bet = max_bet
				
				# increase/decrease current bet
				if (int(input[self.state.active_player][1]) or int(input[self.state.active_player][2])) and (self.cur_bet + 100 <= max_bet): self.cur_bet += 100
				elif (int(input[self.state.active_player][3]) or int(input[self.state.active_player][4])) and (self.cur_bet - 100 >= 0): self.cur_bet -= 100
			
			# DISPLAY CLUE SCREEN GAME LOGIC
			elif self.state.display_clue:
			
				if self.state.count == 0: self.game_clock = 0
			
				buzzed_players = []
			
				# (IF NOT A DAILY DOUBLE) ANY PLAYER MAY BUZZ IN
				if self.state.dailydouble: buzzed_players.append(self.state.active_player)
				else:
					i = 0
					for buzzer in input[:self.num_players]:
						if int(buzzer[0]) == 1: buzzed_players.append(i)
						i += 1
				
				# only if someone has buzzed in
				if len(buzzed_players) > 0:
				
					# choose random player, if both buzzed together
					self.state.set_buzzed_player(buzzed_players[random.randint(0, len(buzzed_players)-1)])
					
					# play 'ring in' sound
					if not self.state.dailydouble: constants.BUZZ_SOUND.play()
			
			# BUZZED-IN SCREEN GAME LOGIC
			elif self.state.buzzed_in:
				
				# reset game clock
				if self.state.count == 0: self.game_clock = 0
			
			# DISPLAY RESPONSE SCREEN GAME LOGIC
			elif self.state.display_resp: pass
			
			# CHECK RESPONSE SCREEN GAME LOGIC
			elif self.state.check_resp:
			
				# determine points to add/sub
				if self.state.dailydouble: points = self.cur_bet
				else: points = constants.POINT_VALUES[self.cur_round][self.cursor_loc[1]]
				
				# player indicates CORRECT
				if int(input[self.state.buzzed_player][3]):
				
					self.players[self.state.buzzed_player].add_to_score(points)
					self.state.active_player = self.state.buzzed_player
				
				# player indicates INCORRECT
				elif int(input[self.state.buzzed_player][2]) or self.state.buzzed_timeout:
				
					self.players[self.state.buzzed_player].sub_from_score(points)
					constants.WRONG_SOUNDS[self.state.buzzed_player].play()
			
				# check if round over
				if self.__check_round():
				
					if self.cur_round == 2: return False
					else:
						self.cur_round += 1
						constants.BOARDFILL_SOUND.play()
	
		# UPDATE GAME STATE
		self.state.update(input, self.game_clock, self.cur_block)
		
		# DISPLAY LOGIC
		if self.state.main: self.__display_main()
		elif self.state.display_clue: self.__display_clue_resp(self.state.display_clue, self.state.buzzed_in, self.state.display_resp)			
		elif self.state.buzzed_in: self.__display_clue_resp(self.state.display_clue, self.state.buzzed_in, self.state.display_resp)
		elif self.state.display_resp: self.__display_clue_resp(self.state.display_clue, self.state.buzzed_in, self.state.display_resp)
		elif self.state.check_resp and not self.state.buzzed_timeout: self.__display_check()
		elif self.state.bet: self.screen.blit(util.generate_bet_surface(self.cur_block.category, self.players[self.state.buzzed_player], self.cur_bet), (0, 0))
		
		return True
		
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
		for category in self.lib[self.cur_round]:
		
			# self.board_surf.blit(self.cat_surf[self.cur_round][i], (i*width_interval+10,10))
			self.board_surf.blit(self.lib[self.cur_round][i][0].cat_board_surface(), (i*width_interval+10,-10))
		
			j = 0
			for block in category:
				if not block.clue.completed:
				
					self.board_surf.blit(self.value_surf[self.cur_round][j], (i*width_interval+10, (j+1)*height_interval+10))
				
				j += 1
			i += 1

	# BLIT CLUE/RESPONSE DISPLAY TO SCREEN
	# show_clue = True if CLUE DISPLAY
	# show_clue = False if RESPONSE DISPLAY
	def __display_clue_resp(self, show_clue, buzzed_in, show_resp):
	
		self.screen.fill(constants.BLUE)
		
		clue_surf = util.generate_text_surface((str(self.cur_block.category).upper()))
	
		# if clue display
		if show_clue:
			char_surf = constants.ALEX_IMAGE
			text_surf = util.generate_text_surface(self.cur_block.clue)
			tts = self.cur_block.clue
		elif buzzed_in:
			char_surf = self.players[self.state.buzzed_player].char_surface
			text_surf = util.generate_text_surface(self.cur_block.clue)
			tts = self.cur_block.clue
		elif show_resp:
			char_surf = self.players[self.state.buzzed_player].char_surface
			text_surf = util.generate_text_surface(self.cur_block.response)
			tts = self.cur_block.response
		
		# scale character surface
		scaled_image = pygame.transform.scale(char_surf, (char_surf.get_width()*3, char_surf.get_height()*3))
		
		# blit character and text to screen
		util.blit_alpha(self.screen, scaled_image, (0, constants.DISPLAY_RES[1]-scaled_image.get_height()), 100)
		self.screen.blit(char_surf, (0, constants.DISPLAY_RES[1]-char_surf.get_height()))
		self.screen.blit(clue_surf, (constants.DISPLAY_RES[0]/2 - constants.BOARD_SIZE[0]/2, -200))
		self.screen.blit(text_surf, (constants.DISPLAY_RES[0]/2 - constants.BOARD_SIZE[0]/2,0))
		
		# read clue/response
		if (show_clue or show_resp or (buzzed_in and self.state.dailydouble)) and (self.state.count == 0): self.pyttsx_engine.say(str(tts).decode('utf-8'))
	
	# BLIT MAIN DISPLAY TO SCREEN
	def __display_main(self):
	
		self.screen.fill(constants.BLUE)
		self.__update_board_surf()
		
		char_surfs = []
		
		# generate character surfaces
		for i in range(self.num_players):
			#char_surfs.append(self.__generate_char_surf(i))
			char_surfs.append(self.players[i].char_surface)
			
		active_char = char_surfs[self.state.active_player]
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

		char_surf = self.players[self.state.buzzed_player].char_surface
		scaled_image = pygame.transform.scale(char_surf, (char_surf.get_width()*3, char_surf.get_height()*3))
		
		self.screen.fill(constants.BLUE)
		
		util.blit_alpha(self.screen, scaled_image, (0, constants.DISPLAY_RES[1]-scaled_image.get_height()), 100)
		self.screen.blit(char_surf, (0, constants.DISPLAY_RES[1]-char_surf.get_height()))
		
		self.screen.blit(self.correct_surf, (constants.DISPLAY_RES[0]/2-constants.BOARD_SIZE[0]/2,0))
	
	# UPDATE CURSON BASED ON BUTTON DIRECTION
	# up = 1, right = 2, left = 3, down = 4
	def __update_cursor_loc(self, direction):
	
		if self.state.main:
		
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
				
	def __set_dailydoubles(self):
	
		for round in self.lib[:-1]:
		
			dd1 = [random.randint(0, 5), random.randint(0, 4)]
			dd2 = [random.randint(0, 5), random.randint(0, 4)]
			
			while (dd1[0] == dd2[0]): dd2[0] = random.randint(0, 5)
			
			round[dd1[0]][dd1[1]].set_dailydouble(True)
			round[dd2[0]][dd2[1]].set_dailydouble(True)
	
	# check to see if current round is over
	def __check_round(self):
	
		cat_done = True
		#for clue in self.clue_arr[self.cur_round][self.cursor_loc[0]][1:]:
		for block in self.lib[self.cur_round][self.cursor_loc[0]]:
			if not block.clue_completed(): cat_done = False
		if cat_done: self.lib[self.cur_round][self.cursor_loc[0]][0].complete_category()
		
		round_done = True
		for block in self.lib[self.cur_round]:
			if not block[0].category_completed(): round_done = False
			
		return round_done