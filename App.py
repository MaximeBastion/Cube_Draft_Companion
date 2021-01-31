import arcade
from Deck import Deck
import pyglet
from IoManager import IoManager
import gc

# set up the screen
SCREEN_NUM = 0  # 0 if you have 1 screen, 1 if you have two and want the app on the second one
SCREENS = pyglet.canvas.Display().get_screens()
SCREEN = SCREENS[SCREEN_NUM]

# Constants
SCREEN_WIDTH = int(1920 * .8)
SCREEN_HEIGHT = int(1080 * .8)
SCREEN_TITLE = "Cube Draft Companion"

# Constants to position card sprites
CARD_WIDTH_BASE = 672
CARD_HEIGHT_BASE = 936
N_DECK_CATEGORIES = 9
MAX_CARDS_PER_CATEGORY = 10

GLOBAL_SCALING = SCREEN_WIDTH / 1920
LEFT_MARGIN = SCREEN_WIDTH * .025
TOP_MARGIN = SCREEN_HEIGHT * .95

DECK_LEFT_X = LEFT_MARGIN
DECK_TOP_Y = TOP_MARGIN

DECK_WIDTH = SCREEN_WIDTH - DECK_LEFT_X * 2

WIDTH_BETWEEN_CATEGORIES = DECK_WIDTH / 120
CARD_WIDTH = (DECK_WIDTH -
              WIDTH_BETWEEN_CATEGORIES * N_DECK_CATEGORIES) / N_DECK_CATEGORIES
CARD_SCALE = CARD_WIDTH / CARD_WIDTH_BASE
CARD_HEIGHT = CARD_HEIGHT_BASE * CARD_SCALE

DECK_HEIGHT = SCREEN_HEIGHT - 2 * (SCREEN_HEIGHT - DECK_TOP_Y)
HEIGHT_BETWEEN_CARDS = (DECK_HEIGHT - CARD_HEIGHT) / (MAX_CARDS_PER_CATEGORY - 1)

CARD_DISPLAY_TOP = DECK_TOP_Y
CARD_DISPLAY_RIGHT = SCREEN_WIDTH * .975
CARD_DISPLAY_WIDTH = 2 * CARD_WIDTH + 3 * WIDTH_BETWEEN_CATEGORIES
CARD_DISPLAY_SCALING = CARD_DISPLAY_WIDTH / CARD_WIDTH_BASE


class App(arcade.Window):
    """
    Main application class.
    """
    basic_names = [
        "Plains",
        "Island",
        "Swamp",
        "Mountain",
        "Forest"
    ]

    def __init__(self, decks: [Deck], io_manager):
        # Call the parent class and set up the window
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
        print(CARD_SCALE)
        print(CARD_WIDTH)
        self.decks = decks
        self.deck = decks[0]
        self.deck_index = 0
        self.io_manager = io_manager

        # These are 'lists' that keep track of our sprites. Each sprite should
        # go into a list.
        self.card_sprites_list = arcade.SpriteList(is_static=True)
        self.card_sprites_list.use_spatial_hash = False
        self.card_display_sprite = None

        self.display_category_sums = True
        self.category_sums = {i: 0 for i in range(N_DECK_CATEGORIES)}
        # self.sprites_per_deck_index = {}
        self.amount_and_pos_per_basic = {}
        self.moused_hover_card_once = False

        arcade.set_background_color(arcade.csscolor.BLACK)

    def setup(self, base_infos):
        """ Set up the game here. Call this function to restart the game. """
        # self.setup_sprites_per_deck_index(base_infos=base_infos)
        # Create the Sprite lists
        self.switch_active_deck(0)
        # Set up the player, specifically placing it at these coordinates.
        """
        self.card_sprites_list = arcade.SpriteList()
        image_source = "d.jpg"
        s = arcade.Sprite(image_source, GLOBAL_SCALING)
        s.center_x = 500
        s.center_y = 500
        self.card_sprites_list.append(s)
        image_source = "f.jpg"
        s = arcade.Sprite(image_source, GLOBAL_SCALING * .4)
        s.center_x = 1300
        s.center_y = 500
        self.card_sprites_list.append(s)
        
        image_source = ":resources:images/animated_characters/female_adventurer/femaleAdventurer_idle.png"
        self.player_sprite = arcade.Sprite(image_source, CHARACTER_SCALING)
        self.player_sprite.center_x = 64
        self.player_sprite.center_y = 128
        self.player_list.append(self.player_sprite)

        # Create the ground
        # This shows using a loop to place multiple sprites horizontally
        for x in range(0, 1250, 64):
            wall = arcade.Sprite(":resources:images/tiles/grassMid.png", TILE_SCALING)
            wall.center_x = x
            wall.center_y = 32
            self.wall_list.append(wall)

        # Put some crates on the ground
        # This shows using a coordinate list to place sprites
        coordinate_list = [[512, 96],
                           [256, 96],
                           [768, 96]]

        for coordinate in coordinate_list:
            # Add a crate on the ground
            wall = arcade.Sprite(":resources:images/tiles/boxCrate_double.png", TILE_SCALING)
            wall.position = coordinate
            self.wall_list.append(wall)
        """

    def setup_sprites_per_deck_index(self, base_infos):
        for index in range(len(self.decks)):
            self.sprites_per_deck_index[index] = self.get_deck_sprites(base_infos=base_infos, deck=self.decks[index])

    def kill_card_sprites(self):
        gc.collect()
        for sprite in self.card_sprites_list:
            sprite.kill()
            sprite.clear_spatial_hashes()

    def switch_active_deck(self, index):
        self.amount_and_pos_per_basic = {}
        self.kill_card_sprites()
        deck = self.decks[index]
        print("\nSwitching to " + deck.archetype.name)
        self.deck = deck
        self.deck_index = index
        self.card_sprites_list = self.get_deck_sprites(base_infos=self.io_manager.base_infos_df, deck=deck)
        self.set_display_card(IoManager.get_img_path("Ponder"))
        print("Switch done")

    def switch_active_deck_2(self, index):
        deck = self.decks[index]
        print("\nSwitching to " + deck.archetype.name)
        self.deck = deck
        self.deck_index = index
        self.card_sprites_list = self.sprites_per_deck_index[index]
        self.set_display_card(IoManager.get_img_path("Ponder"))
        print("Switch done")

    def next_deck(self, direction="right"):
        if direction == "right":
            new_index = (self.deck_index + 1) % len(self.decks)
        else:
            new_index = (self.deck_index - 1) % len(self.decks)
        self.switch_active_deck(new_index)

    def on_draw(self):
        """ Render the screen. """

        # Clear the screen to the background color
        arcade.start_render()

        # Draw our sprites

        self.card_sprites_list.draw()

        if self.card_display_sprite:
            self.card_display_sprite.draw()
            self.draw_deck_title()
        if self.display_category_sums:
            self.draw_category_sums()
        self.draw_basic_counts()

    def draw_category_sums(self):
        y = DECK_TOP_Y + 5
        for category_index, card_count in self.category_sums.items():
            if card_count > 0:
                if category_index < N_DECK_CATEGORIES - 2:  # ignoring sideboard counts
                    x = DECK_LEFT_X + category_index * (WIDTH_BETWEEN_CATEGORIES + CARD_WIDTH) + CARD_WIDTH * .44
                    arcade.draw_text(str(card_count), x, y, arcade.color.WHITE, 25 * GLOBAL_SCALING)

    def draw_deck_title(self):
        font_size = 25 * GLOBAL_SCALING
        title = self.deck.get_name()
        y = 50 * GLOBAL_SCALING
        x = SCREEN_WIDTH / 2 + (len(title) * font_size / 10)
        arcade.draw_text(title, x, y, arcade.color.WHITE, font_size)

    def draw_basic_counts(self):
        for basic in self.amount_and_pos_per_basic.keys():
            count, x, y = self.amount_and_pos_per_basic[basic]
            if count > 0:
                arcade.draw_text(str(count), x, y, arcade.color.BLACK, 34 * GLOBAL_SCALING)

    def on_key_press(self, key, modifiers):
        """Called whenever a key is pressed. """
        if key == arcade.key.F:
            # User hits f. Flip between full and not full screen.
            self.set_fullscreen(not self.fullscreen, screen=SCREEN)
            # Get the window coordinates. Match viewport to window coordinates
            # so there is a one-to-one mapping.
            width, height = self.get_size()
            self.set_viewport(0, width, 0, height)
        if key == arcade.key.H:
            self.card_display_sprite.alpha = 0 if self.card_display_sprite.alpha == 255 else 255
        if key == arcade.key.LEFT:
            self.next_deck(direction="left")
        if key == arcade.key.RIGHT:
            self.next_deck()
        if key == arcade.key.ESCAPE:
            self.close()

    def on_mouse_motion(self, x, y, dx, dy):
        """ Called to update our objects. Happens approximately 60 times per second."""
        for sprite in self.card_sprites_list:
            if sprite.collides_with_point((x, y)):
                self.on_mouse_hovers_card(sprite)

    def on_mouse_hovers_card(self, card_sprite: arcade.Sprite):
        card_path = card_sprite.guid
        self.set_display_card(card_path=card_path)

    def set_display_card(self, card_path, debug=False):
        # checking if it's already displayed
        if self.card_display_sprite and self.card_display_sprite.guid == card_path:
            return

        if debug:
            print("Setting display card to" + card_path)
        old_alpha = 255 if not self.card_display_sprite else self.card_display_sprite.alpha
        self.card_display_sprite = arcade.Sprite(card_path, scale=CARD_DISPLAY_SCALING)
        self.card_display_sprite.top = CARD_DISPLAY_TOP
        self.card_display_sprite.right = CARD_DISPLAY_RIGHT
        self.card_display_sprite.guid = card_path
        self.card_display_sprite.alpha = old_alpha

    def get_deck_sprites(self, base_infos, deck):
        """

        :param deck:
        :param base_infos: DataFrame
        :return: SpriteList containing all card sprites, placed according to their category

        """
        sprites = arcade.SpriteList(is_static=True)
        sprites.use_spatial_hash = False
        cards_per_cmc, nonbasics, side_cards, count_per_basic = deck.get_cards_per_category(base_infos=base_infos, as_paths=True)
        lands = nonbasics + [count[1] for count in count_per_basic.values() if count[0] > 0]
        mid_side_index = int(len(side_cards) / 2)
        side_1, side_2 = side_cards[:mid_side_index + 1], side_cards[mid_side_index + 1:]
        iterator = [(0, "lands", lands)] + [(i, "cmc" + str(i), cards_per_cmc[i]) for i in range(1, 7)] + [
            (7, "sideboard1", side_1), (8, "sideboard2", side_2)]
        for category_index, category, paths in iterator:
            if category_index == "lands":
                self.category_sums[category_index] = len(paths) + sum([count_per_basic[basic_name][0] for basic_name in App.basic_names])
            else:
                self.category_sums[category_index] = len(paths)  # to be able to display the amount of cards per category
            left_x = DECK_LEFT_X + category_index * (WIDTH_BETWEEN_CATEGORIES + CARD_WIDTH)
            for card_index, card_path in enumerate(paths):
                top_y = DECK_TOP_Y - HEIGHT_BETWEEN_CARDS * card_index
                sprite = arcade.Sprite(card_path.replace('//', '__'), CARD_SCALE)
                sprite.guid = card_path
                sprite.left = left_x
                sprite.top = top_y
                sprites.append(sprite)
                is_basic = self.path_is_basic(path=card_path, card_index=card_index)
                if is_basic:
                    x = left_x + CARD_WIDTH/2 - GLOBAL_SCALING*20
                    y = top_y - HEIGHT_BETWEEN_CARDS
                    self.amount_and_pos_per_basic[is_basic] = (count_per_basic[is_basic][0], x, y)
        print("have " + str(len(sprites)) + " sprites")
        return sprites

    def path_is_basic(self, path, card_index):
        basic = None
        for basic_name in App.basic_names:
            if basic_name in path:
                basic = basic_name
        return basic

