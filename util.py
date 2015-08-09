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
			value_surf[-1].append(generate_text_surface(value, width, height, font_size, color, "helvetica", constants.DARK_BLUE))
	
	return value_surf

def generate_text_surface(text, max_width = constants.BOARD_SIZE[0], max_height = constants.BOARD_SIZE[1],
							font_size = 40, color = constants.WHITE, font_fam = "helvetica", color_key = constants.BLUE):
	
	# encode data as string
	text = str(text)
	
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

def generate_correct_surface():

	main_surf = pygame.Surface(constants.BOARD_SIZE)
	main_center_loc = [constants.BOARD_SIZE[0]/2, constants.BOARD_SIZE[1]/2]

	correct_text_surf = generate_text_surface("CORRECT")
	incorrect_text_surf = generate_text_surface("INCORRECT")
	
	orange_rect_surf = pygame.Surface((100, 50)).convert()
	green_rect_surf = pygame.Surface((100, 50)).convert()
	
	main_surf.fill(constants.BLUE)
	main_surf.set_colorkey(constants.BLUE)
	main_surf.set_alpha(255)
	
	orange_rect_surf.fill(constants.ORANGE)
	green_rect_surf.fill(constants.GREEN)
	
	main_surf.blit(orange_rect_surf, (main_center_loc[0]-100, main_center_loc[1]-50))
	main_surf.blit(green_rect_surf, (main_center_loc[0]-100, main_center_loc[1]+50))
	main_surf.blit(correct_text_surf, (100, 80))
	main_surf.blit(incorrect_text_surf, (100, -20))
	
	return main_surf
	
def generate_bet_surface(category, player, bet):

	main_surf = pygame.Surface(constants.DISPLAY_RES)
	main_surf.fill(constants.BLUE)
	
	prompt_text_surf = generate_text_surface(category)
	scaled_image_surf = pygame.transform.scale(player.blank_char_surface, (player.blank_char_surface.get_width()*3, player.blank_char_surface.get_height()*3))
	bet_text_surf = generate_text_surface(bet, scaled_image_surf.get_width(), scaled_image_surf.get_height(), 63, constants.WHITE, "digital")
	
	scaled_image_surf.blit(bet_text_surf, (0,scaled_image_surf.get_height()/3+20))
	
	main_surf.blit(prompt_text_surf, (constants.DISPLAY_RES[0]/2-prompt_text_surf.get_width()/2, -200))
	main_surf.blit(scaled_image_surf, (constants.DISPLAY_RES[0]/2-scaled_image_surf.get_width()/2,constants.DISPLAY_RES[1]-scaled_image_surf.get_height()))
	
	return main_surf

# CODE FROM: http://www.nerdparadise.com/tech/python/pygame/blitopacity/
# create surface with given opacity
def blit_alpha(target, source, location, opacity):

	x = location[0]
	y = location[1]
	temp = pygame.Surface((source.get_width(), source.get_height())).convert()
	temp.blit(target, (-x, -y))
	temp.blit(source, (0, 0))
	temp.set_alpha(opacity)        
	target.blit(temp, location)
	
# GAMIFY LIST FOR SIMPLER USE THROUGHOUT GAME
# assumes list is fully populated
def gamify_list(list):

	gamified_list = [[],[]]
	split_list = [list[:len(list)/2], list[len(list)/2:-1]]
	
	i = 0
	for round in split_list:
	
		for x in range(6): gamified_list[i].append([])
	
		j = 0
		for item in round:
			gamified_list[i][j].append(item)
			
			if j == 5: j = 0
			else: j += 1
		
		i += 1
	
	# add final jeopardy item
	gamified_list.append([[list[-1]]])
			
	return gamified_list