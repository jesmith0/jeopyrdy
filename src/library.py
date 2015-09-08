import util, constants, pygame, gen

class Block:

	def __init__(self, category, clue, response, resource):
	
		self.category = category
		self.clue = clue
		self.response = response
		self.resource = resource
		
	def cat_board_surface(self): return self.category.board_surface
	
	def cat_display_surface(self): return self.category.display_surface
		
	def category_completed(self): return self.category.completed
		
	def clue_completed(self): return self.clue.completed
	
	def set_dailydouble(self, bool): self.clue.dailydouble = True
		
	def is_dailydouble(self): return self.clue.dailydouble
	
	def see_clue(self): self.clue.completed = True
	
	def complete_category(self): self.category.completed = True
	
	def if_resource(self):
		
		if self.resource: return True
		else: return False

class Category:

	def __init__(self, text):
	
		# data
		self.text = text
		self.board_surface = None
		self.display_surface = None
		
		# state
		self.completed = False
		
		self.board_surface = gen.text_surface(self.text, constants.BOARD_SIZE[0]/6 - 20, constants.BOARD_SIZE[0]/6 - 20, 20, constants.YELLOW, "helvetica", constants.DARK_BLUE)
		
	def __str__(self): return self.text

class Clue:

	def __init__(self, text, dailydouble = False):
	
		# data
		self.text = text
		self.surface = None
		
		# state
		self.completed = False
		self.dailydouble = dailydouble
		
		# CALL TO __generate_surface()
		
	def __str__(self): return self.text
		
class Response:

	def __init__(self, text):
	
		# data
		self.text = text
		self.surface = None
		
		# CALL TO __generate_surface()
		
	def __str__(self): return self.text
	
class Resource:

	def __init__(self, res):
	
		# data
		self.res = res
		self.surface = self.__generate_surf(res)
		
	def __generate_surf(self, res):
	
		if res: return pygame.image.load(res)
		
		else: return None
		
	def __str__(self): return self.res