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
		self.points_updated = False
		self.check_round = False
		self.all_bets_set = False
		self.all_checks_set = False
		self.fj_timeout = False
	
	def set_buzzed_player(self, p): self.buzzed_player = p
	
	def set_final_jeopardy(self):
	
		# players bet first
		self.final = True
		self.cur_state = FINAL_BET_STATE
		
		# P1 is first to bet
		# self.active_player = 0
		
	def update(self, input, cur_block = None):
	
		# RESET CLOCK
		if self.count == 0: self.game_clock = 0
		
		# RESET VARIABLES
		self.check_round = False
	
		# INCREMENT STATE COUNT
		self.count += 1
		
		# CHECK IF STATE TIMED OUT
		timedout = self.__check_timeout()
		
		# ONLY UPDATE ON NON-NULL INPUT
		if input or timedout:
		
			# skip if timed out
			if input:
			
				active_down = int(input[self.active_player][0])
				buzzed_down = int(input[self.buzzed_player][0])
				check_down = int(input[self.buzzed_player][2]) or int(input[self.buzzed_player][3])
		
			# MAIN SCREEN STATE LOGIC
			if self.if_state(MAIN_STATE) and active_down and not cur_block.clue_completed():
				
				# mark clue as seen
				cur_block.see_clue()
				
				# reset state variables
				self.buzzed_timeout = False
				self.clue_timeout = False
				self.dailydouble = False
				
				# check daily double
				if cur_block.is_dailydouble():
				
					self.cur_state = BET_STATE
					self.dailydouble = True
					DAILYDOUBLE_SOUND.play()
				
				else: self.cur_state = SHOW_CLUE_STATE
				
				self.__end_state()
			
			# BETTING SCREEN STATE LOGIC
			elif self.if_state(BET_STATE) and self.__check_button_raised(input, 0) and active_down:
				
				self.cur_state = BUZZED_STATE
				
				# automatically buzz active player
				self.buzzed_player = self.active_player
				
				self.__end_state()
			
			# DISPLAY CLUE SCREEN STATE LOGIC
			elif self.if_state(SHOW_CLUE_STATE) and ((( timedout or (not self.final and self.__check_button_raised(input, 0, False) and buzzed_down) ))):
			
				if not timedout and not self.final: self.cur_state = BUZZED_STATE
				else:
					TIMEOUT_SOUND.play()
					time.sleep(1)
					self.clue_timeout = True
					
					if self.final: self.cur_state = FINAL_CHECK_STATE
					else: self.cur_state = SHOW_RESP_STATE
				
				self.__end_state()
				
			# BUZZED IN SCREEN STATE LOGIC
			elif self.if_state(BUZZED_STATE) and ((( timedout or (self.game_clock >= DELAY and buzzed_down) ))):
				
				if timedout:
				
					TIMEOUT_SOUND.play()
					time.sleep(1)
					self.buzzed_timeout = True
				
				self.cur_state = SHOW_RESP_STATE
				
				self.__end_state()
			
			# DISPLAY RESPONSE SCREEN STATE LOGIC
			elif self.if_state(SHOW_RESP_STATE) and (((( timedout and self.__check_button_raised(input, 0) and active_down ))) \
										or ((( not timedout and buzzed_down ))) ):
				
				# timed out
				if (self.buzzed_timeout or self.clue_timeout) and not self.final:
				
					self.cur_state = MAIN_STATE
					self.check_round = True
					self.points_updated = False
					
				elif self.final: self.cur_state = FINAL_CHECK_STATE
				else: self.cur_state = CHECK_STATE
			
				self.__end_state()
			
			# CHECK RESPONSE SCREEN STATE LOGIC
			elif self.if_state(CHECK_STATE) and (check_down or self.buzzed_timeout):
			
				self.cur_state = MAIN_STATE
				self.check_round = True
				
				self.__end_state()
			
			# FINAL BET SCREEN STATE LOGIC
			elif self.if_state(FINAL_BET_STATE) and self.all_bets_set:
			
				self.cur_state = SHOW_CLUE_STATE
				self.all_bets_set = False
			
			# FINAL CHECK SCREEN STATE LOGIC
			elif self.if_state(FINAL_CHECK_STATE) and self.all_checks_set:
			
				self.cur_state = END_STATE
				self.all_checks_set = False
		
	def __check_button_raised(self, input, button, active = True):
	
		if not self.button_raised:
			
			# check active/buzzed player
			if active and not int(input[self.active_player][button]): self.button_raised = True
			elif not active and not int(input[self.buzzed_player][button]): self.button_raised = True
		
		return self.button_raised
	
	def __check_timeout(self):
	
		if self.fj_timeout: return True
		elif self.if_state(SHOW_CLUE_STATE) and not self.final and (self.game_clock >= CLUE_TIMEOUT): return True
		elif self.if_state(BUZZED_STATE) and (self.game_clock >= BUZZ_TIMEOUT): return True
		else: return False
		
	def __end_state(self):
	
		self.count = 0
		self.button_raised = False
		
	def if_state(self, state):
	
		if self.cur_state == state: return True
		else: return False
		
	def __str__(self):
	
		if self.if_state(MAIN_STATE): return "MAIN STATE"
		elif self.if_state(BET_STATE): return "BET STATE"
		elif self.if_state(BUZZED_STATE): return "BUZZED STATE"
		elif self.if_state(SHOW_CLUE_STATE): return "SHOW CLUE STATE"
		elif self.if_state(SHOW_RESP_STATE): return "SHOW RESPONSE STATE"
		elif self.if_state(CHECK_STATE): return "CHECK RESPONSE STATE"