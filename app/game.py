import random
import subprocess

import gen
import state
import util
from constants import *


class Game:

    def __init__(self, screen, lib, active_players, sfx_on, speech_on, input_type):

        # STATIC VARIABLES
        self.SCREEN = screen
        self.LIB = lib
        self.SFX_ON = sfx_on
        self.SPEECH_ON = speech_on
        self.INPUT_TYPE = input_type
        self.NUM_ACTIVE = len(active_players)

        self.clear_events_flag = False

        # STATE VARIABLES
        self.state = state.State(sfx_on)
        self.cursor_loc = [0, 0]
        self.cur_round = 0
        self.cur_block = lib[0][0][0]
        self.game_over = False
        self.clue_read = False
        self.play_toasty = False

        self.currently_playing = None

        # TOASTY VARIABLES
        self.toasty_x = 0
        self.toasty_step = 0
        self.toasty = gen.char_surface(-1)

        # SKIP VARIABLES
        self.skip_arr = [False, False, False, False]

        # PLAYER OBJECTS
        self.players = util.init_player_objects(active_players)

        # GENERATE STATIC SURFACES
        self.board_surf = gen.board_surface()  # returns a blank board surface
        self.blank_board_surf = gen.board_surface()  # returns a blank board surface (kept blank)
        self.cursor_surf = gen.cursor_surface()  # returns a cursor surface
        self.value_surfs = gen.value_surfaces()  # returns a list of two lists of value surfaces

        # SOUND CHANNELS
        self.fj_channel = pygame.mixer.Channel(2)
        self.res_channel = None

        # SET DAILY DOUBLES
        self.__set_dailydoubles()

        # SYSTEM PROCESSES
        self.speech_popen = None

        # PLAY SOUNDS
        if self.SFX_ON: BOARDFILL_SOUND.play()

        # INITIAL UPDATE
        self.update()

    def tick_game_clock(self, ms):
        self.state.game_clock += ms

    def return_to_menu(self):

        if self.res_channel and self.state.new_game: self.res_channel.fadeout(1000)
        return self.state.new_game

    def __check_skip(self, input):

        i = 0
        for buzzer in input:
            if buzzer[4]: self.skip_arr[i] = not self.skip_arr[i]
            i += 1

        i = 0
        for player in self.players:
            if player.playing: i += 1

        if sum(self.skip_arr) == i:
            return True
        else:
            return False

    def update(self, dirty_input=None, event=None):

        # check if speaking
        speaking = False
        if self.speech_popen:
            speaking = self.speech_popen.poll() is None

        # sets input value of all inactive players to 0
        if dirty_input:
            input = self.__clean_input(dirty_input)
        else:
            input = None

        # players vote to skip
        skip = False

        # input logic
        if event and ((self.INPUT_TYPE and event.type == pygame.JOYBUTTONDOWN) or (
                not self.INPUT_TYPE and event.type == pygame.KEYDOWN)):

            active_up = int(input[self.state.active_player][1])
            active_right = int(input[self.state.active_player][2])
            active_left = int(input[self.state.active_player][3])
            active_down = int(input[self.state.active_player][4])
            buzzed_green = int(input[self.state.buzzed_player][3])
            buzzed_orange = int(input[self.state.buzzed_player][2])

            # MAIN SCREEN GAME LOGIC
            if self.state.if_state(MAIN_STATE):

                # move cursor
                if active_up:
                    self.__update_cursor_loc('up')
                elif active_right:
                    self.__update_cursor_loc('right')
                elif active_left:
                    self.__update_cursor_loc('left')
                elif active_down:
                    self.__update_cursor_loc('down')

                # set current block to correspond with cursor's position
                self.cur_block = self.LIB[self.cur_round][self.cursor_loc[0]][self.cursor_loc[1]]

            # BET SCREEN GAME LOGIC
            elif self.state.if_state(BET_STATE):

                betting_player = self.players[self.state.active_player]

                # increase/decrease current bet
                if active_up:
                    betting_player.inc_bet()
                elif active_down:
                    betting_player.dec_bet()

            # DISPLAY CLUE SCREEN GAME LOGIC
            elif self.state.if_state(SHOW_CLUE_STATE):

                buzzed_players = []

                # (IF NOT A DAILY DOUBLE) ANY PLAYER MAY BUZZ IN
                if self.state.dailydouble:
                    buzzed_players.append(self.state.active_player)
                # NO PLAYERS BUZZED IN
                else:

                    # CHECK FOR BUZZ IN
                    if not speaking:
                        i = 0
                        for buzzer in input[:NUM_PLAYERS]:
                            if int(buzzer[0]) == 1: buzzed_players.append(i)
                            i += 1

                    # CHECK FOR SKIP
                    skip = self.__check_skip(input)

                    if skip:
                        if speaking and self.speech_popen:
                            self.speech_popen.kill()

                # only if someone has buzzed in
                if len(buzzed_players) > 0:

                    # choose random player, if both buzzed together
                    self.state.set_buzzed_player(buzzed_players[random.randint(0, len(buzzed_players) - 1)])

                    # play 'ring in' sound
                    if self.SFX_ON and not self.state.dailydouble and not self.state.final: BUZZ_SOUND.play()

            # BUZZED-IN SCREEN GAME LOGIC
            elif self.state.if_state(BUZZED_STATE):
                pass

            # DISPLAY RESPONSE SCREEN GAME LOGIC
            elif self.state.if_state(SHOW_RESP_STATE):

                # reset skip functionality
                self.skip_arr = [False, False, False, False]

                # add points
                if buzzed_green and not (
                        self.state.clue_timeout or self.state.buzzed_timeout or self.state.points_updated):

                    self.__update_points()
                    self.state.active_player = self.state.buzzed_player
                    self.state.points_updated = True

                # subtract points
                elif ((buzzed_orange and not self.state.clue_timeout) or self.state.buzzed_timeout) and not (
                self.state.points_updated):

                    self.__update_points(False)
                    self.state.points_updated = True

            # FINAL JEOPARDY BET SCREEN GAME LOGIC
            elif self.state.if_state(FINAL_BET_STATE):

                # process input
                self.__proc_final_input(input)

                # check if completed
                completed = True
                for player in self.players:
                    if not player.bet_set: completed = False

                # on completion, notify state object
                if completed:

                    # update state
                    self.state.all_bets_set = True

                    # play final jeopardy music
                    if self.clue_read:
                        self.fj_channel.set_endevent(END_FJ_EVENT)
                        self.fj_channel.play(FINALJEP_SOUND)

                    # mute is sound effects off
                    if not self.SFX_ON: self.fj_channel.set_volume(0)

                    # set up check state
                    for player in self.players:
                        if player.cur_bet <= 0: player.check_set = True

            # FINAL JEOPARDY CHECK SCREEN GAME LOGIC
            elif self.state.if_state(FINAL_CHECK_STATE):

                # process input
                self.__proc_final_input(input)

                # force state gameclock to 0
                self.state.reset_clock()

                # check if completed
                completed = True
                for player in self.players:
                    if not player.check_set: completed = False

                # on completion, notify state object
                if completed: self.state.all_checks_set = True

        # UPDATE GAME STATE
        self.state.update(input, self.cur_block, skip, speaking)

        # UPDATE ROUND
        self.__update_round()

        # INITIAL STATE LOGIC (must happen before initial display)
        if self.state.init:

            if self.state.if_state(MAIN_STATE):
                self.state.buzzed_player = self.state.active_player
            elif self.state.if_state(BET_STATE):
                self.players[self.state.active_player].set_bet_to_max()
            elif self.state.if_state(SHOW_CLUE_STATE):
                self.clue_read = False
            elif self.state.if_state(END_STATE):
                self.game_over = True
                if self.SFX_ON: self.res_channel = APPLAUSE_SOUND.play()

        # stop playback of wrong phrase if leaving main board
        if self.state.if_state(BET_STATE) or self.state.if_state(SHOW_CLUE_STATE) or self.state.if_state(
                FINAL_BET_STATE):

            if self.currently_playing:
                self.currently_playing.stop()

        # DISPLAY GAME STATE
        self.__update_display()

        return True

    # UPDATES THE DISPLAY
    def __update_display(self):

        self.__display_state(self.state.cur_state)

    # CALLED IN EVENT LOOP TO END FINAL JEOPARDY
    def end_final_jeopardy(self):

        # end final jeopardy
        self.state.fj_timeout = True

        # remove end event
        self.fj_channel.set_endevent(None)

    def __proc_final_input(self, input):

        for i in range(NUM_PLAYERS):

            player = self.players[i]

            # increment/decrement bet
            if self.state.if_state(FINAL_BET_STATE):

                if player.bet_set:
                    if int(input[i][0]): player.bet_set = False
                else:
                    if int(input[i][0]):
                        player.bet_set = True
                    elif int(input[i][1]):
                        player.inc_bet(True)
                    elif int(input[i][4]):
                        player.dec_bet(True)

            # indicate correct/incorrect
            if self.state.if_state(FINAL_CHECK_STATE):

                if int(input[i][2]) and not player.check_set:
                    player.sub_from_score(player.cur_bet)
                    player.check_set = True

                elif int(input[i][3]) and not player.check_set:
                    player.add_to_score(player.cur_bet)
                    player.check_set = True

    def __update_round(self):

        # check if round over
        if self.state.check_round and self.__check_round():

            # increment round, play sound
            self.cur_round += 1
            if self.SFX_ON: BOARDFILL_SOUND.play()

            # initiate final jeopardy
            if self.cur_round == 2:

                self.__init_final()

                # set up final bet state
                for player in self.players: player.setup_bet(True)

    ### DEBUGGING ONLY ###
    def force_update_round(self):

        self.__init_final()

        # set up final bet state
        for player in self.players: player.setup_bet(True)

    def __display_state(self, cur_state):

        # call appropriate display function based on the current state
        if cur_state == MAIN_STATE:
            self.__display_main()
        elif cur_state == SHOW_CLUE_STATE:
            self.__display_clue()
        elif cur_state == BUZZED_STATE:
            self.__display_clue()
        elif cur_state == SHOW_RESP_STATE:
            self.__display_resp()
        elif cur_state == BET_STATE:
            self.__display_bet()
        elif cur_state == FINAL_BET_STATE:
            self.__display_final_bet()
        elif cur_state == FINAL_CHECK_STATE:
            self.__display_final_check()
        elif cur_state == END_STATE:
            self.__display_end()

    # UPDATES CLUES AND CATEGORIES AND CURSOR ON BOARD SURFACE
    def __update_board_surf(self):

        width_interval = BOARD_SIZE[0] / 6
        height_interval = BOARD_SIZE[1] / 6

        # blit board surface with blank board
        self.board_surf.blit(self.blank_board_surf, (0, 0))

        # blit cursor to board
        self.board_surf.blit(self.cursor_surf,
                             (self.cursor_loc[0] * width_interval, (self.cursor_loc[1] + 1) * height_interval))

        # blit board surface with values
        i = 0
        for category in self.LIB[self.cur_round]:

            self.board_surf.blit(self.LIB[self.cur_round][i][0].cat_board_surface(), (i * width_interval + 10, -10))

            j = 0
            for block in category:
                if not block.clue.completed:
                    self.board_surf.blit(self.value_surfs[self.cur_round][j],
                                         (i * width_interval + 10, (j + 1) * height_interval + 10))

                j += 1
            i += 1

    # BLIT CLUE DISPLAY TO SCREEN
    def __display_clue(self):

        # generate category and clue surface
        cat_surf = gen.text_surface((str(self.cur_block.category).upper()))
        clue_surf = gen.text_surface(self.cur_block.clue, BOARD_SIZE[0] + 100, BOARD_SIZE[1] + 100, 32, WHITE,
                                     "korinna")

        # determine character surface
        if self.state.if_state(SHOW_CLUE_STATE):
            char_surf = ALEX_IMAGE
        elif self.state.if_state(BUZZED_STATE):
            char_surf = self.players[self.state.buzzed_player].char_surface

        # scale character surface
        scaled_image = pygame.transform.scale(char_surf, (char_surf.get_width() * 3, char_surf.get_height() * 3))

        # fill screen
        self.SCREEN.fill(BLUE)

        # blit character and text to screen
        util.blit_alpha(self.SCREEN, scaled_image, (0, DISPLAY_RES[1] - scaled_image.get_height()), 100)
        self.SCREEN.blit(char_surf, (0, DISPLAY_RES[1] - char_surf.get_height()))

        i = 0
        for skip in self.skip_arr:
            if skip: self.SCREEN.blit(self.players[i].skip_surface, ((i * 100) + 50, 50))
            i += 1

        # get resource and display/play
        ### if self.cur_block.if_resource(): ### ACTUAL CHECK WHEN MOVIES AND MUSIC
        if self.cur_block.resource.surface:
            ### DETERMINE IF MOVIE, MUSIC, OR IMAGE ###
            res_surface = self.cur_block.resource.surface

            # resize
            scale_height = 200.0
            height = res_surface.get_height()
            scale_width = res_surface.get_width() * (scale_height / height)
            scaled_surf = pygame.Surface((scale_width, scale_height))

            # res_surface = pygame.transform.smoothscale(res_surface, (scale_width, scale_height), scaled_surf)
            res_surface = pygame.transform.scale(res_surface, (int(scale_width), int(scale_height)))

            # res_surface = pygame.transform.scale(res_surface, (res_surface.get_width()/2, res_surface.get_height()/2))
            # self.SCREEN.blit(scaled_surf, (DISPLAY_RES[0]/2 - res_surface.get_width()/2, 400))
            self.SCREEN.blit(res_surface, (
            (DISPLAY_RES[0] / 2) - (res_surface.get_width() / 2), DISPLAY_RES[1] - res_surface.get_height() - 20))

        # blit category and clue to screen
        self.SCREEN.blit(cat_surf, (DISPLAY_RES[0] / 2 - BOARD_SIZE[0] / 2, -200))
        self.SCREEN.blit(clue_surf, ((DISPLAY_RES[0] / 2 - BOARD_SIZE[0] / 2) - 50, 0))

        # read response
        if self.state.init and (self.state.if_state(SHOW_CLUE_STATE) or self.state.dailydouble): self.__ttsx_speak(
            self.cur_block.clue)

    # BLIT RESPONSE DISPLAY TO SCREEN
    def __display_resp(self):

        main_center_loc = [BOARD_SIZE[0] / 2, BOARD_SIZE[1] / 2]

        # generate marker surfaces
        correct_surf = gen.correct_surface(True)
        incorrect_surf = gen.correct_surface(False)

        # generate character and text surfaces
        cat_surf = gen.text_surface((str(self.cur_block.category).upper()))
        char_surf = self.players[self.state.buzzed_player].char_surface
        text_surf = gen.text_surface(self.cur_block.response, BOARD_SIZE[0], BOARD_SIZE[1], 40, WHITE, "korinna")

        # scale character surface
        scaled_image = pygame.transform.scale(char_surf, (char_surf.get_width() * 3, char_surf.get_height() * 3))

        # fill screen
        self.SCREEN.fill(BLUE)

        # blit character and text to screen
        util.blit_alpha(self.SCREEN, scaled_image, (0, DISPLAY_RES[1] - scaled_image.get_height()), 100)
        self.SCREEN.blit(char_surf, (0, DISPLAY_RES[1] - char_surf.get_height()))

        # blit response
        self.SCREEN.blit(cat_surf, (DISPLAY_RES[0] / 2 - BOARD_SIZE[0] / 2, -200))
        self.SCREEN.blit(text_surf, (DISPLAY_RES[0] / 2 - BOARD_SIZE[0] / 2, 0))

        # blit markers
        if not (self.state.buzzed_timeout or self.state.clue_timeout):
            self.SCREEN.blit(correct_surf, (main_center_loc[0] - 100, main_center_loc[1] + 150))
            self.SCREEN.blit(incorrect_surf,
                             (main_center_loc[0] + incorrect_surf.get_width(), main_center_loc[1] + 150))

        # read response
        if self.state.init: self.__ttsx_speak(self.cur_block.response)

    # BLIT MAIN DISPLAY TO SCREEN
    def __display_main(self):

        self.SCREEN.fill(BLUE)
        self.__update_board_surf()

        # create scaled character surface
        active_char_surf = self.players[self.state.active_player].char_surface
        scaled_image = pygame.transform.scale(active_char_surf,
                                              (active_char_surf.get_width() * 3, active_char_surf.get_height() * 3))

        # blit active char
        util.blit_alpha(self.SCREEN, scaled_image, (0, DISPLAY_RES[1] - scaled_image.get_height()), 100)

        # blit game board
        self.SCREEN.blit(self.board_surf, (DISPLAY_RES[0] / 2 - BOARD_SIZE[0] / 2, 0))

        # blit all characters
        self.__blit_all_characters(self.SCREEN)

        # toasty animation
        if self.play_toasty: self.__run_toasty()

    def __display_bet(self):

        # set variables
        category = self.cur_block.category
        player = self.players[self.state.buzzed_player]

        # scale surfaces
        background_surf = pygame.transform.scale(DDBG_IMAGE, DISPLAY_RES)
        scaled_image_surf = pygame.transform.scale(player.blank_char_surface, (
        player.blank_char_surface.get_width() * 3, player.blank_char_surface.get_height() * 3))

        # generate other surfaces
        prompt_text_surf = gen.text_surface(category)
        bet_text_surf = gen.text_surface(player.cur_bet, scaled_image_surf.get_width(), scaled_image_surf.get_height(),
                                         63, WHITE, "digital")

        # blit to image surface
        scaled_image_surf.blit(bet_text_surf, (0, scaled_image_surf.get_height() / 3 + 20))

        # blit to screen
        self.SCREEN.blit(background_surf, (0, 0))
        self.SCREEN.blit(prompt_text_surf, (DISPLAY_RES[0] / 2 - prompt_text_surf.get_width() / 2, -200))
        self.SCREEN.blit(scaled_image_surf, (
        DISPLAY_RES[0] / 2 - scaled_image_surf.get_width() / 2, DISPLAY_RES[1] - scaled_image_surf.get_height()))

    def __display_final_bet(self):

        # blit background image
        background_surf = pygame.transform.scale(FJBG_IMAGE, DISPLAY_RES)
        self.SCREEN.blit(background_surf, (0, 0))

        # blit category
        prompt_text_surf = gen.text_surface(self.cur_block.category)
        self.SCREEN.blit(prompt_text_surf, (DISPLAY_RES[0] / 2 - prompt_text_surf.get_width() / 2, -200))

        # blit all characters
        self.__blit_all_characters(self.SCREEN)

    def __display_final_check(self):

        main_center_loc = [BOARD_SIZE[0] / 2, BOARD_SIZE[1] / 2]

        correct_surf = gen.correct_surface(True)
        incorrect_surf = gen.correct_surface(False)

        # fill screen
        self.SCREEN.fill(BLUE)

        # blit response
        self.SCREEN.blit(gen.text_surface(self.cur_block.response), (DISPLAY_RES[0] / 2 - BOARD_SIZE[0] / 2, 0))

        # blit markers
        self.SCREEN.blit(correct_surf, (main_center_loc[0] - 100, main_center_loc[1] + 100))
        self.SCREEN.blit(incorrect_surf, (main_center_loc[0] + incorrect_surf.get_width(), main_center_loc[1] + 100))

        # blit all characters
        self.__blit_all_characters(self.SCREEN)

    def __display_end(self):

        # scale and blit background image
        background_surf = pygame.transform.scale(MAINBG_IMAGE, DISPLAY_RES)
        self.SCREEN.blit(background_surf, (0, 0))

        # determine winners (may be a tie)
        winners = self.__determine_winners()

        # blit winners
        for i in range(len(winners)):
            char_surf = winners[i].char_surface
            if winners[i].playing: self.SCREEN.blit(
                pygame.transform.scale(char_surf, (char_surf.get_width() * 3, char_surf.get_height() * 3)),
                (i * 300, 200))

        self.SCREEN.blit(gen.text_surface("CONGRATULATIONS!!!"), (0, -200))

    def __determine_winners(self):

        winners = [self.players[0]]
        for player in self.players[1:]:
            if player.score > winners[0].score:
                winners = [player]
            elif player.score == winners[0].score:
                winners.append(player)

        return winners

    def __blit_all_characters(self, screen):

        active_players = []

        # get list of active players
        for player in self.players:
            if player.playing:
                active_players.append(player)

        # width interval dependant on number of active players
        width_interval = DISPLAY_RES[0] / len(active_players)

        # blit all characters
        for i in range(len(active_players)):

            # calculate location
            blit_loc = (((width_interval * i) + width_interval / 2) - active_players[i].char_surface.get_width() / 2,
						DISPLAY_RES[1] - active_players[i].char_surface.get_height())

            # blit alpha depending on state
            if (self.state.if_state(FINAL_BET_STATE) and active_players[i].bet_set) or (
                    self.state.if_state(FINAL_CHECK_STATE) and active_players[i].check_set):
                util.blit_alpha(screen, active_players[i].char_surface, blit_loc, 25)

            # blit character surface
            else:
                screen.blit(active_players[i].char_surface, blit_loc)

    # UPDATE CURSON BASED ON BUTTON DIRECTION
    def __update_cursor_loc(self, direction):

        # up
        if direction == 'up':
            if self.cursor_loc[1] > 0:
                self.cursor_loc[1] -= 1
            else:
                self.cursor_loc[1] = 4

        # right
        elif direction == 'right':
            if self.cursor_loc[0] < 5:
                self.cursor_loc[0] += 1
            else:
                self.cursor_loc[0] = 0

        # left
        elif direction == 'left':
            if self.cursor_loc[0] > 0:
                self.cursor_loc[0] -= 1
            else:
                self.cursor_loc[0] = 5

        # down
        elif direction == 'down':
            if self.cursor_loc[1] < 4:
                self.cursor_loc[1] += 1
            else:
                self.cursor_loc[1] = 0

    def __set_dailydoubles(self):

        # for both rounds
        for round in self.LIB[:-1]:

            # choose random locations
            dd1 = [random.randint(0, 5), random.randint(0, 4)]
            dd2 = [random.randint(0, 5), random.randint(0, 4)]

            # asserts that locations are different
            while dd1[0] == dd2[0]: dd2[0] = random.randint(0, 5)

            # set daily double
            round[dd1[0]][dd1[1]].set_dailydouble(True)
            round[dd2[0]][dd2[1]].set_dailydouble(True)

    # check to see if current round is over
    def __check_round(self):

        for category in self.LIB[self.cur_round]:
            for block in category:
                if not block.clue_completed(): return False

        return True

    def __clean_input(self, dirty_input):

        clean_input = dirty_input

        # number of buzzers per device
        for i in range(4):

            # number of buttons per buzzer
            for j in range(5):

                if not self.players[i].playing: clean_input[i][j] = 0

        return clean_input

    # by default ADD points
    def __update_points(self, add=True):

        player = self.players[self.state.buzzed_player]

        # determine points to add/sub
        if self.state.dailydouble or self.state.final:
            points = player.cur_bet
        else:
            points = POINT_VALUES[self.cur_round][self.cursor_loc[1]]

        if add:
            player.add_to_score(points)
        else:
            player.sub_from_score(points)

            if self.SFX_ON:
                # self.currently_playing = self.players[self.state.buzzed_player].get_wrong()
                # self.currently_playing.play()
                self.currently_playing = self.players[
                    self.state.buzzed_player].play_wrong()  # play "wrong" catch phrase
                if self.players[self.state.buzzed_player].num == 11: self.__set_toasty()

        player.reset_bet()

    # play toasty animation for jeremy character
    def __run_toasty(self):

        self.toasty_step += 1

        # offset = self.toasty_step

        # if self.toasty_step > 200: offset = 200 - (self.toasty_step % 200)

        # toasty_y = DISPLAY_RES[1] - offset

        self.SCREEN.blit(self.toasty, (self.toasty_x * 180, DISPLAY_RES[1] - 200))

        if self.toasty_step >= 10: self.__reset_toasty()

    def __set_toasty(self):

        self.toasty_x = random.randrange(0, int(DISPLAY_RES[0] / 180))  # sprite width is 180
        self.toasty_step = 0
        self.play_toasty = True  # play toasty animation if jeremy

    def __reset_toasty(self):

        self.toasty_x = 0
        self.toasty_step = 0
        self.play_toasty = False
        self.__update_display()

    # read words using ttsx engine
    def __ttsx_speak(self, words):

        if self.SPEECH_ON:
            self.speech_popen = subprocess.Popen(["say", str(words).decode('utf-8')])

        self.clear_events_flag = True
        self.clue_read = True

    def __init_final(self):

        # set-up state object
        self.state.set_final_jeopardy()

        # set current block to final jeopardy block
        self.cur_block = self.LIB[2][0][0]
