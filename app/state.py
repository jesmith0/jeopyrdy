import time

from constants import *

class State:

	def __init__(self, sfx_on):
		
		self.cur_state = MAIN_STATE
		self.game_clock = 0
		self.SFX_ON = sfx_on
		
		# PLAYER STATES
		self.active_player = 0
		self.buzzed_player = 0
		self.hold_active = 0
		
		# HELPER STATES
		self.init = True
		self.final = False
		self.dailydouble = False
		self.buzzed_timeout = False
		self.clue_timeout = False
		self.points_updated = False
		self.check_round = False
		self.all_bets_set = False
		self.all_checks_set = False
		self.fj_timeout = False
		self.new_game = False
	
	def set_buzzed_player(self, p):
		self.buzzed_player = p
	
	def set_final_jeopardy(self):
	
		# players bet first
		self.final = True
		self.cur_state = FINAL_BET_STATE
		
	def update(self, input, cur_block = None, skip = False, speaking = False):
	
		# RESET VARIABLES
		self.check_round = False
		active_down = False
		buzzed_down = False
		check_down = False
	
		# RESET CLOCK
		if self.init: self.reset_clock()
		
		# CHECK IF STATE TIMED OUT
		timedout = self.__check_timeout(skip)
		
		# ONLY UPDATE ON NON-NULL INPUT
		if input or timedout:
		
			# skip if timed out
			if input:
			
				active_down = int(input[self.active_player][0]) and not speaking
				buzzed_down = int(input[self.buzzed_player][0]) and not speaking
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
					if self.SFX_ON: DAILYDOUBLE_SOUND.play()
				
				else: self.cur_state = SHOW_CLUE_STATE
				
				self.__end_state()
				return
			
			# BETTING SCREEN STATE LOGIC
			elif self.if_state(BET_STATE) and active_down:
				
				self.cur_state = BUZZED_STATE
				
				# automatically buzz active player
				self.buzzed_player = self.active_player
				
				self.__end_state()
				return
			
			# DISPLAY CLUE SCREEN STATE LOGIC
			elif self.if_state(SHOW_CLUE_STATE) and ((( timedout or (not self.final and buzzed_down) ))):
			
				if not timedout and not self.final: self.cur_state = BUZZED_STATE
				else:
					if self.SFX_ON: TIMEOUT_SOUND.play()
					time.sleep(1)
					self.clue_timeout = True
					
					if self.final: self.cur_state = FINAL_CHECK_STATE
					else: self.cur_state = SHOW_RESP_STATE
				
				self.__end_state()
				return
				
			# BUZZED IN SCREEN STATE LOGIC
			elif self.if_state(BUZZED_STATE) and ((( timedout or (self.game_clock >= DELAY and buzzed_down) ))):
				
				if timedout:
				
					if self.SFX_ON: TIMEOUT_SOUND.play()
					time.sleep(1)
					self.buzzed_timeout = True
				
				self.cur_state = SHOW_RESP_STATE
				
				self.__end_state()
				return
			
			# DISPLAY RESPONSE SCREEN STATE LOGIC
			elif self.if_state(SHOW_RESP_STATE) and ((not timedout and check_down) or (self.clue_timeout and active_down) or (self.buzzed_timeout and buzzed_down)):
				
				if self.final: self.cur_state = FINAL_CHECK_STATE
				else:
					self.cur_state = MAIN_STATE
					self.check_round = True
					self.points_updated = False
			
				self.__end_state()
				return
			
			# FINAL BET SCREEN STATE LOGIC
			elif self.if_state(FINAL_BET_STATE) and self.all_bets_set:
			
				self.cur_state = SHOW_CLUE_STATE
				self.all_bets_set = False
				
				self.__end_state()
				return
			
			# FINAL CHECK SCREEN STATE LOGIC
			elif self.if_state(FINAL_CHECK_STATE) and self.all_checks_set:
			
				self.cur_state = END_STATE
				self.all_checks_set = False
				
				self.__end_state()
				return
			
			# END SCREEN STATE LOGIC
			elif self.if_state(END_STATE) and active_down:
			
				# initiates creation of new game object
				self.new_game = True
				return
				
		self.init = False
	
	def __check_timeout(self, skip = False):
	
		if self.fj_timeout:
			return True
		elif self.if_state(SHOW_CLUE_STATE) and not self.final and ((self.game_clock >= CLUE_TIMEOUT) or skip): return True

		# oh god im so ashamed
		elif self.if_state(BUZZED_STATE):
			if self.dailydouble:
				if (self.game_clock >= CLUE_TIMEOUT): return True
			else:
				if (self.game_clock >= BUZZ_TIMEOUT): return True

		elif self.if_state(BUZZED_STATE) and (self.game_clock >= BUZZ_TIMEOUT): return True
		elif (self.buzzed_timeout or self.clue_timeout) and not self.final: return True
		else: return False
		
	def __end_state(self):
	
		self.init = True
		
	def if_state(self, state):
	
		if self.cur_state == state: return True
		else: return False

	def reset_clock(self): self.game_clock = 0
		
	def __str__(self):
	
		if self.if_state(MAIN_STATE): return "MAIN STATE"
		elif self.if_state(BET_STATE): return "BET STATE"
		elif self.if_state(BUZZED_STATE): return "BUZZED STATE"
		elif self.if_state(SHOW_CLUE_STATE): return "SHOW CLUE STATE"
		elif self.if_state(SHOW_RESP_STATE): return "SHOW RESPONSE STATE"
		elif self.if_state(CHECK_STATE): return "CHECK RESPONSE STATE"