import arcade
from IoManager import IoManager


class CardGui:

    def __init__(self, card_name, on_click, lang="en"):
        self.card_name = card_name
        self.card_path = IoManager.get_img_path(card_name=card_name, lang=lang)
        self.on_click = on_click
        self.sprite = None


class PackGui:

    def __init__(self, card_names, lang="en"):
        self.card_names = card_names
        self.card_guis: [CardGui] = self.setup_card_guis(lang=lang)

    def setup_card_guis(self, lang="en"):
        card_guis = []
        for card_name in self.card_names:
            card_gui = CardGui(
                card_name=card_name,
                on_click=lambda: print("Clicked " + card_name),
                lang=lang
            )
            card_guis.append(card_gui)
        return card_guis

    def get_sprites(self):
        sprites = arcade.SpriteList()
        for c_gui in self.card_guis:
            sprites.append(c_gui.sprite)
        return sprites

    def position_sprites(self, pack_window_left, pack_window_top, pack_window_width, pack_window_height, card_width,
                         card_height, card_scale, width_between_cards, height_between_cards):
        """
        Positions the sprites in a grid. Fills it row-wise
        :param card_scale:
        :param pack_window_left:
        :param pack_window_top:
        :param pack_window_width:
        :param pack_window_height:
        :param card_width:
        :param card_height:
        :param width_between_cards:
        :param height_between_cards:
        :return: height of the view: px
        """
        n_cards = len(self.card_names)
        max_cards_per_row = int(pack_window_width / (card_width + width_between_cards))
        max_cards_per_column = int(pack_window_height / (card_height + height_between_cards))
        if max_cards_per_row * max_cards_per_column < n_cards:
            print("Can't fit that many cards")
            return None

        card_i = 0
        for row_i in range(max_cards_per_row):
            top = pack_window_top - row_i * (card_height + height_between_cards)
            for col_i in range(max_cards_per_column):
                left = pack_window_left + col_i * (card_width + width_between_cards)
                card_gui = self.card_guis[card_i]
                sprite = arcade.Sprite(card_gui.card_path, card_scale)
                sprite.top = top
                sprite.left = left
                card_gui.sprite = sprite
                card_i += 1
                if card_i >= n_cards:
                    total_height = top + card_height + height_between_cards
                    return total_height

        return None
