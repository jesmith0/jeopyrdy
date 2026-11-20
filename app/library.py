import constants
import pygame
import gen


class Block:

    def __init__(self, category, clue, response, resource, response_resource=None):

        self.category = category
        self.clue = clue
        self.response = response

        # image that is part of the clue (shown while the clue is up)
        self.resource = resource

        # image looked up from the correct response; shown only once the
        # response is revealed, since it would give the answer away (#30)
        self.response_resource = response_resource or Resource(None)

    def cat_board_surface(self):
        return self.category.board_surface

    def cat_display_surface(self):
        return self.category.display_surface

    def category_completed(self):
        return self.category.completed

    def clue_completed(self):
        return self.clue.completed

    def set_dailydouble(self, bool):
        self.clue.dailydouble = True

    def is_dailydouble(self):
        return self.clue.dailydouble

    def see_clue(self):
        self.clue.completed = True

    def complete_category(self):
        self.category.completed = True

    def if_resource(self):

        if self.resource:
            return True
        else:
            return False


class Category:

    def __init__(self, text):
        # data
        self.text = text
        self.board_surface = None
        self.display_surface = None

        # state
        self.completed = False

        self.board_surface = gen.text_surface(self.text, constants.BOARD_SIZE[0] // 6 - 20,
                                              constants.BOARD_SIZE[0] // 6 - 20, 20, constants.YELLOW, "helvetica",
                                              constants.DARK_BLUE)

    def __str__(self): return self.text


class Clue:

    def __init__(self, text, dailydouble=False):
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

        if res:

            try:
                return pygame.image.load(res)
            except Exception as e:
                print(e)
                print("image load failed for: " + res)
                return None

        else:
            return None

    def __str__(self):
        return self.res
