import pygame, constants

def generate_board_surface():

	color = constants.YELLOW
	
	# intervals for line placement
	width_interval = constants.BOARD_SIZE[0]/6
	height_interval = constants.BOARD_SIZE[1]/6

	# create surface and fill with dark blue
	board_surf = pygame.Surface(constants.BOARD_SIZE)
	board_surf.fill(constants.DARK_BLUE)
	
	# draw horizontal, then vertical line
	for i in range(7):
		pygame.draw.line(board_surf, color, (0,i*height_interval), (constants.BOARD_SIZE[0],i*height_interval), 3)
		pygame.draw.line(board_surf, color, (i*width_interval,0), (i*width_interval,constants.BOARD_SIZE[1]), 3)
	
	return board_surf

def generate_cursor_surface():

	color = constants.WHITE
	
	# cursor size based on board size
	width = constants.BOARD_SIZE[0]/6
	height = constants.BOARD_SIZE[1]/6
	
	# create surface
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
	
def generate_value_surface():

	font_size = 40
	color = constants.YELLOW
	
	# based on board size
	width = constants.BOARD_SIZE[0]/6 - 20
	height = constants.BOARD_SIZE[1]/6 - 20
	
	# create list of surfaces
	value_surf = []
	
	# for each set of values
	for value_set in constants.POINT_VALUES:
	
		value_surf.append([])
		
		# for each value in value set
		for value in value_set:
			value_surf[-1].append(generate_text_surface(str(value), width, height, font_size, color, "helvetica", constants.DARK_BLUE))
	
	return value_surf

def generate_category_surface(category_list):

	font_size = 20
	color = constants.YELLOW

	# width based on board size
	width = constants.BOARD_SIZE[0]/6 - 20
	height = constants.BOARD_SIZE[1]/6 - 20
	
	# create surface
	cat_surf = []

	# for each round in list
	for round in category_list[:-1]:
	
		cat_surf.append([])
		
		# for each category in round
		for cat in round:
			cat_surf[-1].append(generate_text_surface(cat[0], width, height, font_size, color, "helvetica", constants.DARK_BLUE))
			
	return cat_surf
	
def generate_text_surface(text, max_width = constants.BOARD_SIZE[0], max_height = constants.BOARD_SIZE[1],
							font_size = 40, color = constants.WHITE, font_fam = "helvetica", color_key = constants.BLUE):
	
	text_surf = pygame.Surface((max_width, max_height)).convert()
	
	text_surf.fill(color_key)
	text_surf.set_colorkey(color_key)
	text_surf.set_alpha(255)
	
	line_list = ['']
	line_len = 0
	
	if font_fam == "helvetica": font = constants.HELVETICA
	elif font_fam == "korinna": font = constants.KORINNA
	elif font_fam == "digital": font = constants.DIGITAL
	
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
	
# CODE FROM: http://www.nerdparadise.com/tech/python/pygame/blitopacity/
def blit_alpha(target, source, location, opacity):

	x = location[0]
	y = location[1]
	temp = pygame.Surface((source.get_width(), source.get_height())).convert()
	temp.blit(target, (-x, -y))
	temp.blit(source, (0, 0))
	temp.set_alpha(opacity)        
	target.blit(temp, location)