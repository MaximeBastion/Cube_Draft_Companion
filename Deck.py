import random
from Archeytpe import Archetype
from IoManager import IoManager


class Deck:
    basic_names = {
        "W": "Plains",
        "U": "Island",
        "B": "Swamp",
        "R": "Mountain",
        "G": "Forest"
    }

    def __init__(self, archetype: Archetype):
        self.archetype = archetype
        self.main = []
        self.sideboard = []
        self.basics = []

    @staticmethod
    def get_card_cmc(card_name, card_infos_df):
        cmc_df = card_infos_df[["name", "cmc"]]
        return cmc_df[cmc_df["name"] == card_name]["cmc"].iloc[0]

    def visualize_curve(self, card_infos_df):
        pass
        """
        cmc_df = card_infos_df[["name", "cmc"]]
        cmcs = [Deck.get_card_cmc(card_name, card_infos_df) for card_name in self.card_names]

        cmc_values = [i for i in range(1, 7)]
        cmc_counts = [len([c for c in cmcs if c == j]) for j in range(1, 7)]
        #         plt.hist(x=cmc_values, y=cmc_counts)
        return cmc_counts
        """

    def build(self, picks, ratings, nonbasic_list):
        """
        Builds a deck simply, from the picks
        :param picks:
        :param ratings:
        :param nonbasic_list:
        :return: main, sideboard
        """
        basic_count = self.archetype.land_count
        deck = []
        picks_left = picks.copy()
        pick_rows = ratings[ratings["name"].isin(picks)].copy()
        archetype_column = self.archetype.get_feature_name()
        while len(deck) + basic_count < 40:
            max_rating = pick_rows[archetype_column].max()
            best_options = list(pick_rows[pick_rows[archetype_column] == max_rating]["name"])
            chosen_card = random.choice(best_options)
            if chosen_card in nonbasic_list:
                basic_count -= 1
            deck.append(chosen_card)
            picks_left = [n for n in list(pick_rows["name"]) if n not in deck]
            pick_rows = pick_rows[pick_rows["name"].isin(picks_left)]

        self.basics = self.get_basics(basic_count)
        self.main = deck + self.basics
        self.sideboard = picks_left
        return self.main, self.sideboard

    def get_basics(self, amount):
        """
        :return: list as a base deck containing the basics: ["Forest", "Forest"...]
        """
        basics = []
        # Evenly distributes the basics
        lands_per_color_min = int(amount / len(self.archetype.colors))
        lands_left = amount - (lands_per_color_min * len(self.archetype.colors))
        color_with_additional_land = random.choice(self.archetype.colors)
        for color in self.archetype.colors:
            basic_name = Deck.basic_names[color]
            n_land = lands_per_color_min
            if color == color_with_additional_land:
                n_land += lands_left
            for i in range(n_land):
                basics.append(basic_name)

        return basics

    def get_cards_per_category(self, base_infos, as_paths=True, lang="en"):
        """
        Returns card names or urls seperated per categories: per cmc, land, sideboard
        :param base_infos: DataFrame
        :param as_paths: card names or paths?
        :param lang: en or fr
        :return: cards_per_cmc, lands, side_cards
        """
        print("s")
        print(str(len(self.main) + len(self.sideboard)))
        main_rows = base_infos[base_infos["name"].isin(self.main)]

        land_rows = main_rows[main_rows["type_line"].apply(lambda t: t[:4] == "Land")]
        lands = list(land_rows["name"]) + self.basics

        cards_per_cmc = {}
        for cmc in range(7):
            if cmc != 6:
                rows_of_cmc = main_rows[main_rows["cmc"] == cmc]
            else:
                rows_of_cmc = main_rows[main_rows["cmc"] >= cmc]
            cards = list(rows_of_cmc["name"])
            cards_per_cmc[cmc] = [c for c in cards if c not in lands]

        side_rows = base_infos[base_infos["name"].isin(self.sideboard)]
        side_cards = list(side_rows["name"])

        if as_paths:
            cards_per_cmc = {i: [IoManager.get_img_path(card_name=card_name, lang=lang) for card_name in cards_per_cmc[i]] for i in range(7)}
            lands = [IoManager.get_img_path(card_name=card_name, lang=lang) for card_name in lands]
            side_cards = [IoManager.get_img_path(card_name=card_name, lang=lang) for card_name in side_cards]
        return cards_per_cmc, lands, side_cards

    def get_deck_metrics(self, ratings):
        c = self.archetype.get_feature_name()
        main_rows = ratings[ratings["name"].isin(self.main)]
        main_ratings = main_rows[c]
        return main_ratings.sum(), main_ratings.sum() / ratings[c].sum(), main_ratings.mean()


