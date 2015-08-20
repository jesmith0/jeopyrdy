import time

from constants import *

class State:

	def __init__(self):
		
		self.cur_state = MAIN_STATE
		self.game_clock = 0
		
		# PLAYER STATES
		self.active_player = 0
		self.buzzed_player = 0
		self.hold_active = 0
		
		# STATE COUNT
		self.count = 0
		
		# HELPER STATES
		self.final = False
		self.dailydouble = False
		self.button_raised = False
		self.buzzed_timeout = False
		self.clue_timeout = False
		self.skip_player = False
	
	def set_buzzed_player(self, p): self.buzzed_player = p
	
	def set_final_jeopardy(self):
	
		# players bet first
		self.final = True
		self.cur_state = BET_STATE
		
		# P1 is first to bet
		self.active_player = 0
		
	def update(self, input, cur_block = None):
	
		# RESET CLOCK
		if self.count == 0: self.game_clock = 0
	
		# INCREMENT STATE COUNT
		self.count += 1
		
		# CHECK IF STATE TIMED OUT
		timedout = self.__check_timeout()
		
		# ONLY UPDATE ON NON-NULL INPUT
		if input or timedout:
		
			# MAIN SCREEN STATE LOGIC
			if self.if_state(MAIN_STATE) and ((( int(input[self.active_player][0]) and not cur_block.clue_completed() ))):
				
				cur_block.see_clue()
				
				self.buzzed_timeout = False
				self.clue_timeout = False
				self.dailydouble = False
				
				if not cur_block.is_dailydouble(): self.cur_state = SHOW_CLUE_STATE
				else:
					self.cur_state = BET_STATE
					self.dailydouble = True
					DAILYDOUBLE_SOUND.play()
				
				self.__end_state()
			
			# BETTING SCREEN STATE LOGIC
			elif self.if_state(BET_STATE) and ((( (self.__check_button_raised(input, 0) and int(input[self.active_player][0])) or self.skip_player))) :
				
				if self.final:
				
					# cycle through each player
					if self.active_player < 3: self.active_player += 1
					else:
						self.cur_state = SHOW_CLUE_STATE
						FINALJEP_SOUND.play()
				
				else:
				
					self.cur_state = BUZZED_STATE
					self.buzzed_player = self.active_player
				
				self.__end_state()
			
			# DISPLAY CLUE SCREEN STATE LOGIC
			elif self.if_state(SHOW_CLUE_STATE) and ((( timedout or self.__check_button_raised(input, 0, False) and int(input[self.buzzed_player][0]) ))):
			
				print str(timedout)
			
				if not timedout and not self.final: self.cur_state = BUZZED_STATE
				else:
					TIMEOUT_SOUND.play()
					time.sleep(1)
					self.clue_timeout = True
					self.cur_state = SHOW_RESP_STATE
				
				self.__end_state()
				
			# BUZZED IN SCREEN STATE LOGIC
			elif self.if_state(BUZZED_STATE) and ((( timedout or (self.game_clock >= DELAY and int(input[self.buzzed_player][0])) ))):
				
				if timedout:
					TIMEOUT_SOUND.play()
					time.sleep(1)
					self.buzzed_timeout = True
				
				self.cur_state = SHOW_RESP_STATE
				
				self.__end_state()
			
			# DISPLAY RESPONSE SCREEN STATE LOGIC
			elif self.if_state(SHOW_RESP_STATE) and (((( timedout and self.__check_button_raised(input, 0) and int(input[self.active_player][0]) ))) \
										or ((( not timedout and int(input[self.buzzed_player][0]) ))) ):
				
				if (self.buzzed_timeout or self.clue_timeout) and not self.final: self.cur_state = MAIN_STATE
				else: self.cur_state = CHECK_RESP_STATE
			
				self.__end_state()
			
			# CHECK RESPONSE SCREEN STATE LOGIC
			elif self.if_state(CHECK_RESP_STATE) and ((( int(input[self.buzzed_player][2]) or int(input[self.buzzed_player][3]) or self.buzzed_timeout))):
			
				if self.final:
				
					if self.active_player < 3: self.active_player += 1
					else:
						self.cur_state = MAIN_STATE
						self.final = False
					
				else: self.cur_state = MAIN_STATE
				
				self.__end_state()
		
	def __check_button_raised(self, input, button, active = True):
	
		if not self.button_raised:
			
			# check active/buzzed player
			if active and not int(input[self.active_player][button]): self.button_raised = True
			elif not active and not int(input[self.buzzed_player][button]): self.button_raised = True
		
		return self.button_raised
	
	def __check_timeout(self):
	
		if self.if_state(SHOW_CLUE_STATE) and self.final and (self.game_clock >= FINAL_TIMEOUT): return True
		elif self.if_state(SHOW_CLUE_STATE) and not self.final and (self.game_clock >= CLUE_TIMEOUT): return True
		elif self.if_state(BUZZED_STATE) and (self.game_clock >= BUZZ_TIMEOUT): return True
		else: return False
		
	def __end_state(self):
	
		self.count = 0
		self.button_raised = False
		self.skip_player = False
		
	def if_state(self, state):
	
		if self.cur_state == state: return True
		else: return False
		
	def __str__(self):
	
		if self.if_state(MAIN_STATE): return "MAIN STATE"
		elif self.if_state(BET_STATE): return "BET STATE"
		elif self.if_state(BUZZED_STATE): return "BUZZED STATE"
		elif self.if_state(SHOW_CLUE_STATE): return "SHOW CLUE STATE"
		elif self.if_state(SHOW_RESP_STATE): return "SHOW RESPONSE STATE"
		elif self.if_state(CHECK_RESP_STATE): return "CHECK RESPONSE STATE"