import pygame, random, pyttsx, time
import util, state, gen

from constants import *

class Game:

	def __init__(self, screen, lib, active_players, pyttsx_engine, sfx_on, speech_on):
	
		# STATIC VARIABLES
		self.screen = screen
		self.lib = lib
		self.num_players = 4
		self.active_players = active_players
		self.SFX_ON = sfx_on
		self.SPEECH_ON = speech_on
		
		# TTS OBJECT
		self.pyttsx_engine = pyttsx_engine
		
		# STATE VARIABLES
		self.state = state.State(sfx_on)
		self.cursor_loc = [0,0]
		self.cur_round = 0
		self.cur_block = self.lib[0][0][0]
		self.cur_bet = 0 ### reduce to player object ###
		
		# PLAYER OBJECTS
		self.players = util.init_player_objects(self.active_players)
		
		# GENERATE STATIC SURFACES
		self.board_surf = gen.board_surface()			# returns a blank board surface
		self.blank_board_surf = gen.board_surface()		# returns a blank board surface (kept blank)
		self.cursor_surf = gen.cursor_surface()			# returns a cursor surface
		self.value_surfs = gen.value_surfaces()			# returns a list of two lists of value surfaces
		
		# SOUND CHANNELS
		self.fj_channel = None
		
		# SET DAILY DOUBLES
		self.__set_dailydoubles()
		
		# PLAY SOUNDS
		if self.SFX_ON: BOARDFILL_SOUND.play()
		
		# INITIAL UPDATE
		self.update()
		
	def tick_game_clock(self, ms): self.state.game_clock += ms
		
	def update(self, input = None):
	
		# final jeopardy time out
		if self.fj_channel and not self.fj_channel.get_busy(): self.state.fj_timeout = True
	
		if input:
		
			active_up = int(input[self.state.active_player][1])
			active_right = int(input[self.state.active_player][2])
			active_left = int(input[self.state.active_player][3])
			active_down = int(input[self.state.active_player][4])
			buzzed_green = int(input[self.state.buzzed_player][3])
			buzzed_orange = int(input[self.state.buzzed_player][2])
			
			# MAIN SCREEN GAME LOGIC
			if self.state.if_state(MAIN_STATE):
			
				# reset buzzed player variable to active player
				if (self.state.count == 0): self.state.buzzed_player = self.state.active_player
				
				# move cursor
				if active_up: self.__update_cursor_loc('up')
				elif active_right: self.__update_cursor_loc('right')
				elif active_left: self.__update_cursor_loc('left')
				elif active_down: self.__update_cursor_loc('down')
				
				# set current block to correspond with cursor's position
				self.cur_block = self.lib[self.cur_round][self.cursor_loc[0]][self.cursor_loc[1]]
			
			# BET SCREEN GAME LOGIC
			elif self.state.if_state(BET_STATE):
			
				# get maximum bet
				max_bet = self.players[self.state.active_player].get_max_bet()
			
				# set maximum bet
				if self.state.count == 0: self.cur_bet = max_bet
				
				# increase/decrease current bet
				if active_up and (self.cur_bet + 100 <= max_bet): self.cur_bet += 100
				elif active_down and (self.cur_bet - 100 >= 0): self.cur_bet -= 100
			
			# DISPLAY CLUE SCREEN GAME LOGIC
			elif self.state.if_state(SHOW_CLUE_STATE):
			
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
					if self.SFX_ON and not self.state.dailydouble and not self.state.final: BUZZ_SOUND.play()
			
			# BUZZED-IN SCREEN GAME LOGIC
			elif self.state.if_state(BUZZED_STATE): pass
			
			# DISPLAY RESPONSE SCREEN GAME LOGIC
			elif self.state.if_state(SHOW_RESP_STATE): 
			
				# if timed out, subtract points
				if self.state.buzzed_timeout and not self.state.points_updated:
				
					self.__update_points(False)
					self.state.points_updated = True
			
			# CHECK RESPONSE SCREEN GAME LOGIC
			elif self.state.if_state(CHECK_STATE):
				
				# add points
				if buzzed_green:
				
					self.__update_points()
					self.state.active_player = self.state.buzzed_player
					
				# subtract points
				elif buzzed_orange or self.state.buzzed_timeout: self.__update_points(False)
			
			# FINAL JEOPARDY BET SCREEN GAME LOGIC
			elif self.state.if_state(FINAL_BET_STATE):
					
				# process input
				self.__proc_final_input(input)
				
				# check if completed
				completed = True
				for player in self.players:
					if not player.bet_set: completed = False
				
				# on completion, notify state object
				if completed:
				
					# update state
					self.state.all_bets_set = True
				
					# play final jeopardy music
					self.fj_channel = FINALJEP_SOUND.play()
					
					# mute is sound effects off
					if not self.SFX_ON: self.fj_channel.set_volume(0)
					
					# set up check state
					for player in self.players:		
						if player.cur_bet <= 0: player.check_set = True
			
			# FINAL JEOPARDY CHECK SCREEN GAME LOGIC
			elif self.state.if_state(FINAL_CHECK_STATE):
					
				# process input
				self.__proc_final_input(input)
				
				# check if completed
				completed = True
				for player in self.players:
					if not player.check_set: completed = False
				
				# on completion, notify state object
				if completed: self.state.all_checks_set = True
				
		# UPDATE GAME STATE
		self.state.update(input, self.cur_block)
		
		# UPDATE ROUND
		self.__update_round()
		
		# DISPLAY GAME STATE
		self.__display_state(self.state.cur_state)
		
		return True
		
	def __proc_final_input(self, input):
	
		for i in range(self.num_players):
		
			player =  self.players[i]
		
			# increment/decrement bet
			if self.state.if_state(FINAL_BET_STATE) and not player.bet_set:
				
				if int(input[i][0]): player.bet_set = True
				elif int(input[i][1]): player.add_to_bet()
				elif int(input[i][4]): player.sub_from_bet()
			
			# indicate correct/incorrect
			if self.state.if_state(FINAL_CHECK_STATE):
			
				if int(input[i][2]):
					player.sub_from_score(player.cur_bet)
					player.check_set = True
					
				elif int(input[i][3]):
					player.add_to_score(player.cur_bet)
					player.check_set = True
		
	def __update_round(self):
	
		# check if round over
		if self.state.check_round and self.__check_round():
		
			# increment round, play sound
			self.cur_round += 1
			if self.SFX_ON: BOARDFILL_SOUND.play()
			
			# initiate final jeopardy
			if self.cur_round == 2:
			
				self.__init_final()
				
				# set up final bet state
				for player in self.players: player.setup_bet(True)
	
	### DEBUGGING ONLY ###
	def force_update_round(self):
	
		self.__init_final()
				
		# set up final bet state
		for player in self.players: player.setup_bet(True)
		
	def __display_state(self, cur_state):
	
		# call appropriate display function based on the current state
		if cur_state == MAIN_STATE: 			self.__display_main()
		elif cur_state == SHOW_CLUE_STATE: 		self.__display_clue_resp()			
		elif cur_state == BUZZED_STATE: 		self.__display_clue_resp()
		elif cur_state == SHOW_RESP_STATE: 		self.__display_clue_resp()
		elif cur_state == CHECK_STATE: 			self.__display_check()
		elif cur_state == BET_STATE: 			self.__display_bet()
		elif cur_state == FINAL_BET_STATE:		self.__display_final_bet()
		elif cur_state == FINAL_CHECK_STATE: 	self.__display_final_check()
		elif cur_state == END_STATE: 			self.__display_end()
		
	# UPDATES CLUES AND CATEGORIES AND CURSOR ON BOARD SURFACE
	def __update_board_surf(self):
	
		width_interval = BOARD_SIZE[0]/6
		height_interval = BOARD_SIZE[1]/6
	
		# blit board surface with blank board
		self.board_surf.blit(self.blank_board_surf, (0,0))
		
		# blit cursor to board
		self.board_surf.blit(self.cursor_surf, (self.cursor_loc[0]*width_interval,(self.cursor_loc[1]+1)*height_interval))
	
		# blit board surface with values
		i = 0
		for category in self.lib[self.cur_round]:
		
			self.board_surf.blit(self.lib[self.cur_round][i][0].cat_board_surface(), (i*width_interval+10,-10))
		
			j = 0
			for block in category:
				if not block.clue.completed:
				
					self.board_surf.blit(self.value_surfs[self.cur_round][j], (i*width_interval+10, (j+1)*height_interval+10))
				
				j += 1
			i += 1

	# BLIT CLUE/RESPONSE DISPLAY TO SCREEN
	def __display_clue_resp(self):
	
		self.screen.fill(BLUE)
		
		clue_surf = gen.text_surface((str(self.cur_block.category).upper()))
	
		# if clue display
		if self.state.if_state(SHOW_CLUE_STATE):
			char_surf = ALEX_IMAGE
			text_surf = gen.text_surface(self.cur_block.clue)
			tts = self.cur_block.clue
		elif self.state.if_state(BUZZED_STATE):
			char_surf = self.players[self.state.buzzed_player].char_surface
			text_surf = gen.text_surface(self.cur_block.clue)
			tts = self.cur_block.clue
		elif self.state.if_state(SHOW_RESP_STATE):
			char_surf = self.players[self.state.buzzed_player].char_surface
			text_surf = gen.text_surface(self.cur_block.response)
			tts = self.cur_block.response
		
		# scale character surface
		scaled_image = pygame.transform.scale(char_surf, (char_surf.get_width()*3, char_surf.get_height()*3))
		
		res_surface = self.cur_block.resource.surface
		
		# blit character and text to screen
		util.blit_alpha(self.screen, scaled_image, (0, DISPLAY_RES[1]-scaled_image.get_height()), 100)
		self.screen.blit(char_surf, (0, DISPLAY_RES[1]-char_surf.get_height()))
		
		if res_surface:
			res_surface = pygame.transform.scale(res_surface, (res_surface.get_width()/2, res_surface.get_height()/2))
			self.screen.blit(res_surface, (DISPLAY_RES[0]/2 - res_surface.get_width()/2, 400))
		
		self.screen.blit(clue_surf, (DISPLAY_RES[0]/2 - BOARD_SIZE[0]/2, -200))
		self.screen.blit(text_surf, (DISPLAY_RES[0]/2 - BOARD_SIZE[0]/2,0))
		
		# read clue/response
		if self.SPEECH_ON and ((self.state.if_state(SHOW_CLUE_STATE) or self.state.if_state(SHOW_RESP_STATE) or (self.state.if_state(BUZZED_STATE) and self.state.dailydouble)) and (self.state.count == 0)):
			try: self.pyttsx_engine.say(str(tts).decode('utf-8'))
			except UnicodeDecodeError: self.pyttsx_engine.say('Unicode Decode Error')
			except: self.pyttsx_engine.say('Unknown Error')
	
	# BLIT MAIN DISPLAY TO SCREEN
	def __display_main(self):
	
		self.screen.fill(BLUE)
		self.__update_board_surf()
		
		# create scaled character surface
		active_char_surf = self.players[self.state.active_player].char_surface
		scaled_image = pygame.transform.scale(active_char_surf, (active_char_surf.get_width()*3, active_char_surf.get_height()*3))
		
		# blit active char
		util.blit_alpha(self.screen, scaled_image, (0, DISPLAY_RES[1]-scaled_image.get_height()), 100)
		
		# blit game board
		self.screen.blit(self.board_surf, (DISPLAY_RES[0]/2-BOARD_SIZE[0]/2,0))
		
		# blit all characters
		self.__blit_all_characters(self.screen)
	
	# BLIT CHECK RESPONSE DISPLAY TO SCREEN
	def __display_check(self):
		
		# generate marker surfaces
		correct_surf = gen.correct_surface(True)
		incorrect_surf = gen.correct_surface(False)

		# scale character surface
		char_surf = self.players[self.state.buzzed_player].char_surface
		scaled_image = pygame.transform.scale(char_surf, (char_surf.get_width()*3, char_surf.get_height()*3))
		
		# fill screen
		self.screen.fill(BLUE)
		
		# blit character surface
		util.blit_alpha(self.screen, scaled_image, (0, DISPLAY_RES[1]-scaled_image.get_height()), 100)
		self.screen.blit(char_surf, (0, DISPLAY_RES[1]-char_surf.get_height()))
		
		# blit marker surfaces
		self.screen.blit(incorrect_surf, (DISPLAY_RES[0]/2-incorrect_surf.get_width()/2, DISPLAY_RES[1]/2-40))
		self.screen.blit(correct_surf, (DISPLAY_RES[0]/2-correct_surf.get_width()/2, DISPLAY_RES[1]/2+40))
		
	def __display_bet(self):
	
		category = self.cur_block.category
		player = self.players[self.state.buzzed_player]
		bet = self.cur_bet
		
		background_surf = pygame.transform.scale(DDBG_IMAGE, DISPLAY_RES)
		
		prompt_text_surf = gen.text_surface(category)
		scaled_image_surf = pygame.transform.scale(player.blank_char_surface, (player.blank_char_surface.get_width()*3, player.blank_char_surface.get_height()*3))
		bet_text_surf = gen.text_surface(bet, scaled_image_surf.get_width(), scaled_image_surf.get_height(), 63, WHITE, "digital")
		
		scaled_image_surf.blit(bet_text_surf, (0, scaled_image_surf.get_height()/3+20))
		
		self.screen.blit(background_surf, (0, 0))
		self.screen.blit(prompt_text_surf, (DISPLAY_RES[0]/2-prompt_text_surf.get_width()/2, -200))
		self.screen.blit(scaled_image_surf, (DISPLAY_RES[0]/2-scaled_image_surf.get_width()/2, DISPLAY_RES[1]-scaled_image_surf.get_height()))
		
	def __display_final_bet(self):
	
		# blit background image
		background_surf = pygame.transform.scale(FJBG_IMAGE, DISPLAY_RES)
		self.screen.blit(background_surf, (0, 0))
		
		# blit category
		prompt_text_surf = gen.text_surface(self.cur_block.category)
		self.screen.blit(prompt_text_surf, (DISPLAY_RES[0]/2-prompt_text_surf.get_width()/2, -200))
		
		# blit all characters
		self.__blit_all_characters(self.screen)
		
	def __display_final_check(self):
	
		main_center_loc = [BOARD_SIZE[0]/2, BOARD_SIZE[1]/2]
	
		correct_surf = gen.correct_surface(True)
		incorrect_surf = gen.correct_surface(False)
	
		# fill screen
		self.screen.fill(BLUE)
		
		# blit response
		self.screen.blit(gen.text_surface(self.cur_block.response), (DISPLAY_RES[0]/2 - BOARD_SIZE[0]/2,0))
		
		# blit markers
		self.screen.blit(incorrect_surf, (main_center_loc[0]-100, main_center_loc[1]+100))
		self.screen.blit(correct_surf, (main_center_loc[0]+incorrect_surf.get_width(), main_center_loc[1]+100))
		
		# blit all characters
		self.__blit_all_characters(self.screen)
		
	def __display_end(self):
	
		# scale and blit background image
		background_surf = pygame.transform.scale(MAINBG_IMAGE, DISPLAY_RES)
		self.screen.blit(background_surf, (0, 0))
		
		# determine winners (may be a tie)
		winners = self.__determine_winners()
		
		# blit winners
		for i in range(len(winners)):
			char_surf = winners[i].char_surface
			self.screen.blit(pygame.transform.scale(char_surf, (char_surf.get_width()*3, char_surf.get_height()*3)), (i*300, 150))
		
		self.screen.blit(gen.text_surface("CONGRATULATIONS!!!"), (0,-200))
		
	def __determine_winners(self):
	
		winners = [self.players[0]]
		for player in self.players[1:]:
			if player.score > winners[0].score: winners = [player]
			elif player.score == winners[0].score: winners.append(player)
			
		return winners
		
	def __blit_all_characters(self, screen):
	
		char_surfs = []
		
		# generate character surfaces
		for i in range(self.num_players):
			char_surfs.append(self.players[i].char_surface)
		
		# width interval dependant on number of players
		width_interval = DISPLAY_RES[0]/self.num_players
		
		blit_loc = (((width_interval*(i)) + width_interval/2) - char_surfs[i].get_width()/2, DISPLAY_RES[1]-char_surfs[i].get_height())
		
		# blit all characters
		for i in range(self.num_players):
		
			# calculate location
			blit_loc = (((width_interval*(i)) + width_interval/2) - char_surfs[i].get_width()/2, DISPLAY_RES[1]-char_surfs[i].get_height())
			
			if not self.players[i].playing: util.blit_alpha(screen, char_surfs[i], blit_loc, 0)
			
			elif (self.state.if_state(FINAL_BET_STATE) and self.players[i].bet_set) or (self.state.if_state(FINAL_CHECK_STATE) and self.players[i].check_set):
				util.blit_alpha(screen, char_surfs[i], blit_loc, 25)
				
			else: screen.blit(char_surfs[i], blit_loc)
	
	# UPDATE CURSON BASED ON BUTTON DIRECTION
	def __update_cursor_loc(self, direction):
	
		# up
		if direction == 'up':		
			if self.cursor_loc[1] > 0: self.cursor_loc[1] -= 1
			else: self.cursor_loc[1] = 4
		
		# right
		elif direction == 'right':
			if self.cursor_loc[0] < 5: self.cursor_loc[0] += 1
			else: self.cursor_loc[0] = 0
		
		# left
		elif direction == 'left':
			if self.cursor_loc[0] > 0: self.cursor_loc[0] -= 1
			else: self.cursor_loc[0] = 5
		
		# down
		elif direction == 'down':
			if self.cursor_loc[1] < 4: self.cursor_loc[1] += 1
			else: self.cursor_loc[1] = 0
				
	def __set_dailydoubles(self):
	
		# for both rounds
		for round in self.lib[:-1]:
		
			# choose random locations
			dd1 = [random.randint(0, 5), random.randint(0, 4)]
			dd2 = [random.randint(0, 5), random.randint(0, 4)]
			
			# asserts that locations are different
			while (dd1[0] == dd2[0]): dd2[0] = random.randint(0, 5)
			
			# set daily double
			round[dd1[0]][dd1[1]].set_dailydouble(True)
			round[dd2[0]][dd2[1]].set_dailydouble(True)
	
	# check to see if current round is over
	def __check_round(self):
	
		for category in self.lib[self.cur_round]:
			for block in category:
				if not block.clue_completed(): return False
		
		return True
	
	# by default ADD points
	def __update_points(self, add = True):
	
		# determine points to add/sub
		if self.state.dailydouble or self.state.final: points = self.cur_bet
		else: points = POINT_VALUES[self.cur_round][self.cursor_loc[1]]
	
		if add:
			self.players[self.state.buzzed_player].add_to_score(points)
		else:
			self.players[self.state.buzzed_player].sub_from_score(points)
			if self.SFX_ON: self.players[self.state.buzzed_player].play_wrong()
			
	def __init_final(self):
	
		# set-up state object
		self.state.set_final_jeopardy()
		
		# set current block to final jeopardy block
		self.cur_block = self.lib[2][0][0]
		# self.cur_bet = self.players[self.state.active_player].get_max_bet()