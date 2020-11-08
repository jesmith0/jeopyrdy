import pygame, constants, player, random, urllib, urllib2, usb.core, usb.util, library, os, platform

# GLOBAL VARIABLES
image_count = 0

# CONVERT PYGAME EVENT TO USABLE GAME INPUT
def gamify_input(event):

	buzz_map = [[0, 4, 3, 2, 1], [5, 9, 8, 7, 6], [10, 14, 13, 12, 11], [15, 19, 18, 17, 16]]
	key_map = [[50, 119, 100, 97, 115], [53, 116, 104, 102, 103], [56, 105, 108, 106, 107], [45, 91, 13, 59, 39]]
	
	ret = []
	arr = []
	
	if event.type == pygame.KEYDOWN:
		map = key_map
		button = event.key
	elif event.type == pygame.JOYBUTTONDOWN or event.type == pygame.JOYBUTTONUP:
		map = buzz_map
		button = event.button
	
	for set in map:
			
		if button in set:
			for value in set:
			
				if button == value: arr.append(1)
				else: arr.append(0)
				
			ret.append(arr)
					
		else: ret.append([0, 0, 0, 0, 0])
	
	return ret

# REMOVE UNNECESSARY HTML
def scrub_text(text):

	# remove static tags
	new_text = text.replace('&amp;', '&')
	new_text = new_text.replace('<br />', ' ')
	new_text = new_text.replace('<br/>', ' ')
	new_text = new_text.replace('<i>', '')
	new_text = new_text.replace('</i>','')
	new_text = new_text.replace('<u>','')
	new_text = new_text.replace('</u>','')
	new_text = new_text.replace('<del>','')
	new_text = new_text.replace('</del>','')
	new_text = new_text.replace('</em>','')
	new_text = new_text.replace('</a>','')
	
	# remove emphasis tag
	if (not new_text.find('<em') == -1):
		new_text = new_text[:new_text.find('<em')] + new_text[new_text.find('>')+2:]
	
	# for each hyperlink tag
	while (not new_text.find('<a') == -1):
			
		# removes every hyperlink reference tag from text
		new_text = new_text[:new_text.find('<a')] + new_text[new_text.find('">')+2:]
		
	return new_text

# PULL MEDIA RESOURCES FROM J-ARCHIVE
def get_resource(text, num):

	if not text.find('<a') == -1:
	
		# attempt to pull image from j-archive.com
		try:
			res = urllib.urlretrieve(text[text.find("http://"):text.find('.jpg')+4], constants.TEMP_PATH + "temp" + str(num) + ".jpg")
			
			if "text/html" in str(res[1]): return None
			else: return res[0]
			
		except:
			# google image search
			print "url non-responsive"
		
	return None

# PULL GAME DATA FROM J-ARCHIVE	
def parse_jarchive():

	cat = []
	clue = []
	resp = []
	res = []
	info = []
	
	res_count = 0

	# RANDOMLY GENERATE USEABLE GAME NUMBER
	game_num = str(random.randint(1, constants.MAX_GAME))
	
	print game_num
	
	# REDUCE WEBPAGE TO RELEVANT LINES (also sets display window caption)
	# retrieves categories and clues
	for line in urllib2.urlopen(constants.WEB_ADDR_CLUE + game_num).readlines():
		if 'class="clue_text">' in line:
			clue.append(line)
			res.append(None)
		elif 'class="category_name">' in line: cat.append(line)
		elif 'id="game_title">' in line: info.append(line[line.find('id="game_title"><h1>')+20:line.find('</h1>')].upper())
	
	# retrieves responses
	for line in urllib2.urlopen(constants.WEB_ADDR_RESP + game_num).readlines():
		if 'class="correct_response">' in line: resp.append(line)
	
	# FORMAT LIBRARY INFO
	for i in range(len(clue)):
	
		unscrubed_clue = clue[i][clue[i].find('class="clue_text">')+18:clue[i].find('</td>')]
		
		hold_res = get_resource(unscrubed_clue, res_count)
		if hold_res: res_count += 1
		
		res[i] = hold_res
		clue[i] = scrub_text(unscrubed_clue)
		
	for i in range(len(cat)):
		cat[i] = scrub_text(cat[i][cat[i].find('class="category_name">')+22:cat[i].find('</td>')])
		
	for i in range(len(resp)):
		resp[i] = scrub_text(resp[i][resp[i].find('class="correct_response">')+25:resp[i].find('</em>')])
	
	# RETURN LIBRARY
	return [cat, clue, resp, res, info]

# GENERATE LIBRARY OBJECT FROM PULLED DATA
def gen_lib_object(parsed):

	cat = gamify_list(parsed[0])
	clue = gamify_list(parsed[1])
	resp = gamify_list(parsed[2])
	res = gamify_list(parsed[3])
	
	lib = []

	# each round is its own list of block objects
	for i in range(len(clue)):
	
		lib.append([])
		
		for j in range(len(clue[i])):
			lib[-1].append([])
			for k in range(len(clue[i][j])):
				lib[-1][-1].append(library.Block(library.Category(cat[i][j][0]), library.Clue(clue[i][j][k]), library.Response(resp[i][j][k]), library.Resource(res[i][j][k])))
		
	return lib

# SETUP LIBRARY OBJECT
def lib_setup():

	# primitive solution to ensure no unseen clues
	parse_valid = False
	
	while (not parse_valid):
		parsed_data = parse_jarchive()
		if len(parsed_data[1]) == 61: parse_valid = True
	
	print "LIBRARY (setup):\tOK"
	
	return [gen_lib_object(parsed_data), parsed_data[-1]]

# DELETE TEMPORARY FILES (MEDIA RESOURCES)
def dtf():

	if 'Windows' in platform.system(): path = 'temp\\'
	else: path = 'temp/'
	
	num = 0
	while num >= 0:
		try:
			os.remove(path + 'temp' + str(num) + '.jpg')
			num += 1
		except: num = -1

# CREATE PYGAME JOYSTICK OBJECT OF USB BUZZERS
def get_buzzers():

	pygame.joystick.quit()
	pygame.joystick.init()
	
	### POSSIBLE MEMORY LEAK ###

	buzzer = None

	for i in range(0, pygame.joystick.get_count()):
	
		if pygame.joystick.Joystick(i).get_name() == 'Buzz':
			buzzer = pygame.joystick.Joystick(i)
			buzzer.init()

	return buzzer
	
# INITIALiZE PLAYER OBJECTS (CHOOSE CHARACTERS)
def init_player_objects(active_players):

	players = []
	used_nums = []
	
	print active_players
	
	# generate initial random number
	num = random.randint(1, constants.NUM_SPRITES)
	
	# add chosen characters to used list
	for ap_val in active_players: used_nums.append(ap_val)
	
	# determine characters
	for ap_val in active_players:
	
		# player index
		i = len(players)
	
		# player is inactive
		if ap_val == -1: p = player.Player(i, -1)
		
		# choose random character
		elif ap_val == 0:
			
			while num in used_nums: num = random.randint(1, constants.NUM_SPRITES)
			
			p = player.Player(i, num)
		
			used_nums.append(num)
		
		# player chose character
		else: p = player.Player(i, ap_val)
		
		# append player to list
		players.append(p)
	
	return players
	
# GAMIFY LIST FOR SIMPLER USE THROUGHOUT GAME
### MAY BE UNUSED ###
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
	
### CODE FROM: http://www.nerdparadise.com/tech/python/pygame/blitopacity/ ###
# CREATE SURFACE WITH GIVEN OPACITY
def blit_alpha(target, source, location, opacity):

	x = location[0]
	y = location[1]
	temp = pygame.Surface((source.get_width(), source.get_height())).convert()
	temp.blit(target, (-x, -y))
	temp.blit(source, (0, 0))
	temp.set_alpha(opacity)
	target.blit(temp, location)
##############################################################################