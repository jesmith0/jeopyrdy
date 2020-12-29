import pygame, pygame.gfxdraw
from constants import *

def text_surface(text, max_width = BOARD_SIZE[0], max_height = BOARD_SIZE[1], font_size = 40, color = WHITE, font_fam = "helvetica", color_key = BLUE, shadow = True):
	
	# encode data as string
	text = str(text)
	
	# create blank surface
	text_surf = pygame.Surface((max_width, max_height)).convert()
	
	# set transparency
	text_surf.fill(color_key)
	text_surf.set_colorkey(color_key)
	text_surf.set_alpha(255)
	
	# set font face AND alculate line padding
	if font_fam == "helvetica":
		font = HELVETICA
		padding = font_size
		
	elif font_fam == "korinna":
		font = KORINNA
		padding = font_size + 7
		
	elif font_fam == "digital":
		font = DIGITAL
		padding = font_size
	
	line_list = ['']
	line_len = 0
	
	# split text into list of words
	word_list = text.split()
	
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
	
		# blit locations
		x_loc = max_width/2 - font[font_size].size(line)[0]/2
		y_loc = max_height/2-(len(line_list)*padding)/2+i*padding
		
		# render text
		if shadow: text_surf.blit(font[font_size].render(line, 1, BLACK), (x_loc+2, y_loc+2))
		text_surf.blit(font[font_size].render(line, 1, color), (x_loc, y_loc))
		
		# next line
		i += 1
			
	return text_surf

def menu_item(option, value, active):

	font = HELVETICA[30]

	option_surf = font.render(option, 1, WHITE)
	option_surf_bg = font.render(option, 1, BLACK)
	
	# all renders fonts underlined
	if active: font.set_underline(True)
	
	value_surf = font.render(value, 1, WHITE)
	value_surf_bg = font.render(value, 1, BLACK)
	
	# reset underline state
	font.set_underline(False)
	
	# create blank surface
	main_surf = pygame.Surface((option_surf.get_width() + value_surf.get_width(), option_surf.get_height())).convert()
	
	# set transparency
	main_surf.fill(BLUE)
	main_surf.set_colorkey(BLUE)
	main_surf.set_alpha(255)
	
	# blit surfaces
	main_surf.blit(option_surf_bg, (2,2))
	main_surf.blit(option_surf, (0,0))
	main_surf.blit(value_surf_bg, (option_surf.get_width()+2, 2))
	main_surf.blit(value_surf, (option_surf.get_width(), 0))
	
	return main_surf
	
def board_surface():

	color = YELLOW
	
	# intervals for line placement
	width_interval = BOARD_SIZE[0]/6
	height_interval = BOARD_SIZE[1]/6

	# create surface and fill with dark blue
	board_surf = pygame.Surface(BOARD_SIZE)
	board_surf.fill(DARK_BLUE)
	
	# draw horizontal, then vertical line
	for i in range(7):
		pygame.draw.line(board_surf, color, (0, i*height_interval), (BOARD_SIZE[0], i*height_interval), 3)
		pygame.draw.line(board_surf, color, (i*width_interval, 0), (i*width_interval, BOARD_SIZE[1]), 3)
	
	return board_surf
	
def cursor_surface(width = BOARD_SIZE[0]/6, height = BOARD_SIZE[1]/6, color = WHITE, text = None):
	
	# create surface
	cursor_surf = pygame.Surface((width+1, height+1))
	
	# fill surface 
	cursor_surf.fill(BLUE)
	
	# draw player indicator
	if text:
	
		text_surf = HELVETICA[20].render(text, True, BLUE)
		text_size = text_surf.get_size()
	
		# calculate location for circle and text
		if text == "P1":
			center = [5, 5]
			text_loc = [center[0]+3, center[1]+3]
		elif text == "P2":
			center = [width - 5, 5]
			text_loc = [center[0]-3-text_size[0], center[1]+3]
		elif text == "P3":
			center = [5, height - 5]
			text_loc = [center[0]+3, center[1]-3-text_size[1]]
		elif text == "P4":
			center = [width - 5, height - 5]
			text_loc = [center[0]-3-text_size[0], center[1]-3-text_size[1]]
	
		# blit surfaces
		pygame.gfxdraw.filled_circle(cursor_surf, center[0], center[1], 35, color)
		pygame.gfxdraw.aacircle(cursor_surf, center[0], center[1], 35, color)
		cursor_surf.blit(text_surf, (text_loc[0], text_loc[1]))
		
	# set colour key and alpha
	cursor_surf.set_colorkey(BLUE)
	cursor_surf.set_alpha(255)
	
	# horizontal lines
	pygame.draw.line(cursor_surf, color, (0,0), (width,0), 5)
	pygame.draw.line(cursor_surf, color, (0,height), (width,height), 5)
	
	# vertical lines
	pygame.draw.line(cursor_surf, color, (0,0), (0,height), 5)
	pygame.draw.line(cursor_surf, color, (width,0), (width,height), 5)

	return cursor_surf
	
def value_surfaces():

	font_size = 40
	color = YELLOW
	
	# based on board size
	width = BOARD_SIZE[0]/6 - 20
	height = BOARD_SIZE[1]/6 - 20
	
	# create list of surfaces
	value_surfs = []
	
	# for each set of values
	for value_set in POINT_VALUES:
	
		value_surfs.append([])
		
		# for each value in value set
		for value in value_set:
			value_surfs[-1].append(text_surface(value, width, height, font_size, color, "helvetica", DARK_BLUE))
	
	return value_surfs

def char_surface(num):
	
	# create blank surface
	char_surf = pygame.Surface(CHAR_SIZE).convert()
	
	# fill and set alpha
	char_surf.fill(DARK_BLUE)
	char_surf.set_colorkey(DARK_BLUE)
	char_surf.set_alpha(255)

	if num == -1:
		# blit toasty
		char_surf.blit(TOASTY_IMAGE, (0, 0), (0, 0, 180, 200))
	else:	
		# blit slice from character image
		char_surf.blit(CHARACTERS_IMAGE, (0, 0), (num*180, 0, 180, 200))
	
	return char_surf

def skip_surface(order):

	surf = pygame.Surface((50,50)).convert()
	text_surf = text_surface("P" + str(order), 40, 40)

	surf.fill(DARK_BLUE)
	surf.set_colorkey(DARK_BLUE)
	surf.set_alpha(255)

	pygame.draw.circle(surf, YELLOW, (25, 25), 25, 0)
	surf.blit(text_surf, (5, 5))

	return surf

	
def correct_surface(correct = True):

	# generate text surface
	if correct: text_surf = text_surface("CORRECT", 200, 100)
	else: text_surf = text_surface("INCORRECT", 200, 100)
	
	# create blank rectangle surface
	rect_surf = pygame.Surface((100, 50)).convert()
	
	# fill rectangle with correct color
	if correct: rect_surf.fill(GREEN)
	else: rect_surf.fill(ORANGE)
	
	# create blank main surface
	main_surf = pygame.Surface((300, 100)).convert()
	
	# fill and set alpha
	main_surf.fill(DARK_BLUE)
	main_surf.set_colorkey(DARK_BLUE)
	main_surf.set_alpha(255)
	
	# compensate for extra length
	if correct: dist = 75
	else: dist = 87
	
	# blit surfaces
	main_surf.blit(rect_surf, (0, 20))
	main_surf.blit(text_surf, (dist, 0))
	
	return main_surf