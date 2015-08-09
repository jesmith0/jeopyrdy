import constants, time

class State:

	def __init__(self):
	
		# GENERAL STATES
		self.main = True
		self.bet = False
		self.display_clue = False
		self.display_resp = False
		self.check_resp = False
		self.buzzed_in = False
		self.dailydouble = False
		
		# PLAYER STATES
		self.active_player = 0
		self.buzzed_player = 0
		
		# STATE COUNT
		self.count = 0
		
		# HELPER STATES
		self.button_raised = False
		self.buzzed_timeout = False
		
		# DELAYS
		self.DELAY = 1000
		self.CLUE_TIMEOUT = 15000
		self.BUZZ_TIMEOUT = 8000
		
	def get_state(self): return [self.main, self.bet, self.display_clue, self.display_resp, self.check_resp, self.buzzed_in, self.dailydouble]
	
	def set_buzzed_player(self, p): self.buzzed_player = p
		
	def update(self, input, game_clock, cur_block = None):
	
		# INCREMENT STATE COUNT
		self.count += 1
		
		# CHECK IF STATE TIMED OUT
		timedout = self.__check_timeout(game_clock)
		
		# ONLY UPDATE ON NON-NULL INPUT
		if input or timedout:
		
			# MAIN SCREEN STATE LOGIC
			if self.main and ((( int(input[self.active_player][0]) and not cur_block.clue_completed() ))):
				
				cur_block.see_clue()
				
				self.main = False
				self.buzzed_timeout = False
				
				if not cur_block.is_dailydouble(): self.display_clue = True
				else:
					self.bet = True
					self.dailydouble = True
					constants.DAILYDOUBLE_SOUND.play()
				
				self.__end_state()
			
			# BETTING SCREEN STATE LOGIC
			elif self.bet and ((( self.__check_button_raised(input, 0) and int(input[self.active_player][0]) ))):
				
				self.bet = False
				self.buzzed_in = True
				self.buzzed_player = self.active_player
				
				self.__end_state()
			
			# DISPLAY CLUE SCREEN STATE LOGIC
			elif self.display_clue and ((( timedout or self.__check_button_raised(input, 0, False) and int(input[self.buzzed_player][0]) ))):
			
				self.display_clue = False
			
				if not timedout: self.buzzed_in = True
				else:
					constants.TIMEOUT_SOUND.play()
					self.display_resp = True
				
				self.__end_state()
			
			# DISPLAY RESPONSE SCREEN STATE LOGIC
			elif self.display_resp and (((( not timedout and self.__check_button_raised(input, 0, False) and int(input[self.buzzed_player][0]) ))) \
										or ((( timedout and self.__check_button_raised(input, 0) and int(input[self.active_player][0]) )))):
										
				self.display_resp = False
				
				if self.buzzed_timeout: self.check_resp = True
				else: self.check_resp = True
			
				self.__end_state()
			
			# CHECK RESPONSE SCREEN STATE LOGIC
			elif self.check_resp and ((( int(input[self.buzzed_player][2]) or int(input[self.buzzed_player][3]) or self.buzzed_timeout))):
			
				self.check_resp = False
				self.main = True
				self.dailydouble = False
				
				self.__end_state()
			
			# BUZZED IN SCREEN STATE LOGIC
			elif self.buzzed_in and ((( timedout or self.__check_button_raised(input, 0, False) and int(input[self.buzzed_player][0]) ))):
				
				if timedout:
					constants.TIMEOUT_SOUND.play()
					time.sleep(0.5)
					self.buzzed_timeout = True
				
				self.buzzed_in = False
				self.display_resp = True
				
				self.__end_state()
		
	def __check_button_raised(self, input, button, active = True):
	
		if not self.button_raised:
			
			# check active/buzzed player
			if active and not int(input[self.active_player][button]): self.button_raised = True
			elif not active and not int(input[self.buzzed_player][button]): self.button_raised = True
		
		return self.button_raised
	
	def __check_timeout(self, game_clock):
	
		if self.display_clue and (game_clock >= self.CLUE_TIMEOUT): return True
		elif self.buzzed_in and (game_clock >= self.BUZZ_TIMEOUT): return True
		else: return False
		
	def __end_state(self):
	
		self.count = 0
		self.button_raised = False
		
	def __str__(self): return str(self.get_state)