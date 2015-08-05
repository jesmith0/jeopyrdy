import pygame, constants, util

class Player:

	def __init__(self, num):
	
		self.num = num
		self.score = 0
		
		self.blank_char_surface = self.__generate_char_surface(self.num)
		self.char_surface = self.__generate_char_surface(self.num)
		
		self.correct_sound = None
		self.incorrect_sound = None
		
		# blit initial score
		self.add_to_score(0)
	
	# NEGATES POINTS AND CALLS add_to_score
	def sub_from_score(self, points):
	
		self.add_to_score(points * -1)
	
	# ADD TO PLAYER SCORE, UPDATE SURFACE
	def add_to_score(self, points):
	
		# add points to scores
		self.score += points
		
		# determine display color
		if self.score >= 0: color = constants.WHITE
		else: color = constants.RED
		
		# update player surface
		self.char_surface.fill(constants.DARK_BLUE)
		self.char_surface.blit(self.blank_char_surface, (0,0))
		self.char_surface.blit(util.generate_text_surface(str(self.score), self.char_surface.get_width(), self.char_surface.get_height(), 30, color, "digital", constants.BLUE), (0, 70))
	
	# GENERATE BLANK CHARACTER SURFACE
	def __generate_char_surface(self, num):
	
		# create blank surface
		char_surf = pygame.Surface(constants.CHAR_SIZE).convert()
		
		# fill and set alpha
		char_surf.fill(constants.DARK_BLUE)
		char_surf.set_colorkey(constants.DARK_BLUE)
		char_surf.set_alpha(255)
		
		# blit slice from character image
		char_surf.blit(constants.CHARACTERS_IMAGE, (0, 0), (num*180, 0, 180, 200))
		
		return char_surf