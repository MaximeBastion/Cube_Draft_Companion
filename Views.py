import arcade
from CardGui import CardGui, PackGui
import UI
from IoManager import IoManager
from main import main

SCREEN_WIDTH = 1920 * 0.7
SCREEN_HEIGHT = 1080 * 0.7
SCREEN_TITLE = "Cube Draft Companion"

# Constants to position card sprites
CARD_WIDTH_BASE = 672
CARD_HEIGHT_BASE = 936
N_DECK_CATEGORIES = 8
MAX_CARDS_PER_CATEGORY = 10

GLOBAL_SCALING = SCREEN_WIDTH / 1920
LEFT_MARGIN = SCREEN_WIDTH * .025
TOP_MARGIN = SCREEN_HEIGHT * .95

DECK_LEFT_X = LEFT_MARGIN
DECK_TOP_Y = TOP_MARGIN

DECK_WIDTH = SCREEN_WIDTH - DECK_LEFT_X * 2

WIDTH_BETWEEN_CATEGORIES = DECK_WIDTH / 120
CARD_WIDTH = (DECK_WIDTH - WIDTH_BETWEEN_CATEGORIES * N_DECK_CATEGORIES) / N_DECK_CATEGORIES
CARD_SCALE = CARD_WIDTH / CARD_WIDTH_BASE
CARD_HEIGHT = CARD_HEIGHT_BASE * CARD_SCALE

DECK_HEIGHT = SCREEN_HEIGHT - 2 * (SCREEN_HEIGHT - DECK_TOP_Y)
HEIGHT_BETWEEN_CARDS = (DECK_HEIGHT - CARD_HEIGHT) / (MAX_CARDS_PER_CATEGORY - 1)

CARD_DISPLAY_TOP = DECK_TOP_Y
CARD_DISPLAY_RIGHT = SCREEN_WIDTH * .975
CARD_DISPLAY_WIDTH = 2 * CARD_WIDTH + 3 * WIDTH_BETWEEN_CATEGORIES
CARD_DISPLAY_SCALING = CARD_DISPLAY_WIDTH / CARD_WIDTH_BASE

BUTTON_SCALING = GLOBAL_SCALING * 2


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

    def __init__(self):
        super().__init__()
        self.button_group: UI.ButtonGroupVertical = None

    def go_to_app(self):
        #main()
        game_view = GameOverView()
        self.window.show_view(game_view)

    def on_show(self):
        """ This is run once when we switch to this view """
        arcade.set_background_color(arcade.csscolor.DARK_SLATE_BLUE)

        # Reset the viewport, necessary if we have a scrolling game and we need
        # to reset the viewport back to the start so we can see what we draw.
        arcade.set_viewport(0, SCREEN_WIDTH - 1, 0, SCREEN_HEIGHT - 1)

        # button_sprite.center_y = SCREEN_HEIGHT / 2
        # button_sprite.center_x = SCREEN_WIDTH / 2
        buttons = [
            UI.ManualButton(sprite=self.get_button_sprite(), text="Draft", on_click_func=self.go_to_app),
            UI.ManualButton(sprite=self.get_button_sprite(), text="Test2", on_click_func=lambda: print("Clk2")),
            UI.ManualButton(sprite=self.get_button_sprite(), text="Test3", on_click_func=lambda: print("Clk3")),
            UI.ManualButton(sprite=self.get_button_sprite(), text="Test4", on_click_func=lambda: print("Clk4")),
            UI.ManualButton(sprite=self.get_button_sprite(), text="Quit", on_click_func=lambda: self.window.close())
        ]

        self.button_group = UI.ButtonGroupVertical(manual_buttons=buttons, button_scaling=BUTTON_SCALING, screen_width=SCREEN_WIDTH, screen_height=SCREEN_HEIGHT, height_between_buttons=50)

    @staticmethod
    def get_button_sprite():
        return arcade.Sprite(IoManager.get_sprite_path(sprite_name="blue_button.png"), BUTTON_SCALING)


    def on_draw(self):
        """ Draw this view """
        arcade.start_render()
        self.button_group.draw()

    def on_mouse_press(self, _x, _y, _button, _modifiers):
        """ If the user presses the mouse button, re-start the game. """
        # game_view = GameOverView()
        # self.window.show_view(game_view)
        self.button_group.handle_mouse_press(x=_x, y=_y)
        """
        for sprite in self.button_list:
            if sprite.collides_with_point((_x, _y)):
                button = self.get_button_by_guid(guid=sprite.guid)
                if button:
                    button.on_click_func()
        """


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

        self.pack_gui = PackGui(card_names=pack, lang=lang)
        total_height = self.pack_gui.position_sprites(
            pack_window_left=LEFT_MARGIN,
            pack_window_top=TOP_MARGIN,
            pack_window_width=SCREEN_WIDTH,
            pack_window_height=SCREEN_HEIGHT,
            card_width=CARD_WIDTH,
            card_height=CARD_HEIGHT,
            width_between_cards=WIDTH_BETWEEN_CATEGORIES,
            height_between_cards=HEIGHT_BETWEEN_CARDS,
            card_scale=CARD_SCALE
        )
        print("Total height: " + str(total_height))
        self.sprites = self.pack_gui.get_sprites()
        print("have " + str(len(self.sprites)) + " sprites")

    def on_draw(self):
        """ Draw this view """
        arcade.start_render()
        self.sprites.draw()

    def on_mouse_press(self, _x, _y, _button, _modifiers):
        """ If the user presses the mouse button, re-start the game. """
        for card_gui in self.pack_gui.card_guis:
            if card_gui.sprite.collides_with_point((_x, _y)):
                card_gui.on_click()
