import arcade
from CardGui import CardGui, PackGui

SCREEN_WIDTH = 2560
SCREEN_HEIGHT = 1440
SCREEN_TITLE = "Cube Draft Companion"

# Constants to position card sprites
CARD_WIDTH_BASE = 672
CARD_HEIGHT_BASE = 936
N_DECK_CATEGORIES = 10
MAX_CARDS_PER_CATEGORY = 18

GLOBAL_SCALING = SCREEN_WIDTH / 1920
LEFT_MARGIN = SCREEN_WIDTH * .025
TOP_MARGIN = SCREEN_HEIGHT * .95

DECK_LEFT_X = LEFT_MARGIN
DECK_TOP_Y = TOP_MARGIN

DECK_WIDTH = SCREEN_WIDTH - DECK_LEFT_X*2

WIDTH_BETWEEN_CATEGORIES = DECK_WIDTH / 120
CARD_WIDTH = (DECK_WIDTH - WIDTH_BETWEEN_CATEGORIES*N_DECK_CATEGORIES) / N_DECK_CATEGORIES
CARD_SCALE = CARD_WIDTH / CARD_WIDTH_BASE
CARD_HEIGHT = CARD_HEIGHT_BASE * CARD_SCALE

DECK_HEIGHT = SCREEN_HEIGHT - 2*(SCREEN_HEIGHT-DECK_TOP_Y)
HEIGHT_BETWEEN_CARDS = (DECK_HEIGHT - CARD_HEIGHT) / (MAX_CARDS_PER_CATEGORY - 1)

CARD_DISPLAY_TOP = DECK_TOP_Y
CARD_DISPLAY_RIGHT = SCREEN_WIDTH * .975
CARD_DISPLAY_WIDTH = 2*CARD_WIDTH + 3*WIDTH_BETWEEN_CATEGORIES
CARD_DISPLAY_SCALING = CARD_DISPLAY_WIDTH / CARD_WIDTH_BASE


class MyTextButton(arcade.gui.TextButton):
    """
    To capture a button click, subclass the button and override on_click.
    """

    def __init__(self, center_x, center_y, width, height, text, on_click_func=lambda: print("Clicking")):
        super().__init__(center_x, center_y, width, height, text)
        self.on_click_func = on_click_func

    def on_click(self):
        """ Called when user lets off button """
        print("Click flat button. ")
        self.on_click_func()


class MenuView(arcade.View):

    def on_show(self):
        """ This is run once when we switch to this view """
        arcade.set_background_color(arcade.csscolor.DARK_SLATE_BLUE)

        # Reset the viewport, necessary if we have a scrolling game and we need
        # to reset the viewport back to the start so we can see what we draw.
        arcade.set_viewport(0, SCREEN_WIDTH - 1, 0, SCREEN_HEIGHT - 1)

        button = MyTextButton(
            text='UILabel',
            center_x=100,
            center_y=100,
            width=50,
            height=50,
            on_click_func=lambda: print("HI")
        )

    def on_draw(self):
        """ Draw this view """
        arcade.start_render()
        arcade.draw_text("Instructions Screen", SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2,
                         arcade.color.WHITE, font_size=50, anchor_x="center")
        arcade.draw_text("Click to advance", SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 75,
                         arcade.color.WHITE, font_size=20, anchor_x="center")

    def on_mouse_press(self, _x, _y, _button, _modifiers):
        """ If the user presses the mouse button, re-start the game. """
        game_view = GameOverView()
        self.window.show_view(game_view)


class GameOverView(arcade.View):
    """ View to show when game is over """

    def __init__(self):
        """ This is run once when we switch to this view """
        super().__init__()

        # Reset the viewport, necessary if we have a scrolling game and we need
        # to reset the viewport back to the start so we can see what we draw.
        arcade.set_viewport(0, SCREEN_WIDTH - 1, 0, SCREEN_HEIGHT - 1)

    def on_draw(self):
        """ Draw this view """
        arcade.start_render()

    def on_mouse_press(self, _x, _y, _button, _modifiers):
        """ If the user presses the mouse button, re-start the game. """
        game_view = MenuView()
        self.window.show_view(game_view)


class PackView(arcade.View):
    """ View to show when game is over """

    def __init__(self, pack, drafter=None, lang="en"):
        """ This is run once when we switch to this view """
        super().__init__()

        # Reset the viewport, necessary if we have a scrolling game and we need
        # to reset the viewport back to the start so we can see what we draw.
        arcade.set_viewport(0, SCREEN_WIDTH - 1, 0, SCREEN_HEIGHT - 1)

        self.pack = pack
        self.drafter = drafter

        pack_gui = PackGui(card_names=pack, lang=lang)
        total_height = pack_gui.position_sprites(
            pack_window_left=50,
            pack_window_top=50,
            pack_window_width=SCREEN_WIDTH*.8,
            pack_window_height=SCREEN_HEIGHT*.8,
            card_width=CARD_WIDTH,
            card_height=CARD_HEIGHT,
            width_between_cards=WIDTH_BETWEEN_CATEGORIES,
            height_between_cards=HEIGHT_BETWEEN_CARDS
        )
        print("Total height: " + str(total_height))
        self.sprites = arcade.SpriteList()
        for s in pack_gui.card_guis:
            self.sprites.append(s)

    def on_draw(self):
        """ Draw this view """
        arcade.start_render()
        self.sprites.draw()

    def on_mouse_press(self, _x, _y, _button, _modifiers):
        """ If the user presses the mouse button, re-start the game. """
        game_view = MenuView()
        self.window.show_view(game_view)
