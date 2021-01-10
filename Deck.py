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

    def __init__(self, archetype: Archetype, drafter):
        self.archetype = archetype
        self.main = []
        self.sideboard = []
        self.basics = []
        basics = Deck.basic_names.values()
        self.count_per_basic = {basic: [0, IoManager.get_img_path(card_name=basic, lang="en")] for basic in basics}
        self.drafter = drafter

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

    @staticmethod
    def any_is_in(test_l, in_l):
        """
        :param test_l:
        :param in_l:
        :return: True if any of the e in test_l is in in_l
        """
        for e in test_l:
            if e in in_l:
                return True
        return False

    @staticmethod
    def all_are_in(test_l, in_l):
        """

        :param test_l:
        :param in_l:
        :return: True if all e in test_l are in in_l
        """
        for e in test_l:
            if e not in in_l:
                return False
        return True

    @staticmethod
    def card_is_playable_2(base_row, deck_colors):
        """
        Return True if a card is playable given its colors (is colorless or any of its colors is in deck colors)
        + not a land
        :param card_colors:
        :param deck_colors:
        :return:
        """
        card_colors, card_type = base_row["colors"], base_row["type_line"]
        color_playable = card_colors == [] or Deck.all_are_in(card_colors, deck_colors)
        is_land = card_type and "land" in card_type
        output = color_playable and not is_land
        return output

    @staticmethod
    def card_is_playable(card_colors, deck_colors):
        """
        Return True if a card is playable given its colors (is colorless or any of its colors is in deck colors)
        + not a land?
        :param card_colors:
        :param deck_colors:
        :return:
        """
        return card_colors == [] or Deck.all_are_in(card_colors, deck_colors)

    def build(self, picks, ratings, base_infos, nonbasic_list, debug=False):
        """
        Builds a deck simply, from the picks
        :param base_infos:
        :param picks:
        :param ratings:
        :param nonbasic_list:
        :return: main, sideboard
        """
        if debug:
            print("Building deck: " + self.archetype.name + " (" + str(self.archetype.colors) + ")")
        basic_count = self.archetype.land_count
        deck = []
        picks_left = picks.copy()
        archetype_column = self.archetype.get_feature_name()
        pick_rows = ratings[ratings["name"].isin(picks)].copy()
        pick_rows_base = base_infos[base_infos["name"].isin(picks)]
        playable_picks = list(pick_rows_base[
                                  pick_rows_base["colors"].apply(
                                      lambda colors: Deck.card_is_playable(colors, self.archetype.colors))][
                                  "name"])  ### !! OFF color lands are considered playable
        bad_but_playable_picks = list(
            pick_rows[(pick_rows[archetype_column] == 0) & (pick_rows["name"].isin(playable_picks))]["name"])

        if debug:
            print("Bad but playable picks: " + str(bad_but_playable_picks))

        while len(deck) + basic_count < 40:
            max_rating = pick_rows[archetype_column].max()
            best_options = list(pick_rows[pick_rows[archetype_column] == max_rating]["name"])
            if max_rating == 0:
                bad_but_playable_picks_left = [e for e in bad_but_playable_picks if e not in deck]
                # no good cards left to put in, will take cards of my color if possible though
                if len(bad_but_playable_picks_left) > 0:
                    chosen_card = random.choice(bad_but_playable_picks_left)
                    if debug:
                        print("trash, taking " + chosen_card)
                else:
                    chosen_card = random.choice(best_options)
            else:
                chosen_card = random.choice(best_options)

            if chosen_card in nonbasic_list:
                basic_count -= 1
            deck.append(chosen_card)
            picks_left = [n for n in list(pick_rows["name"]) if n not in deck]
            pick_rows = pick_rows[pick_rows["name"].isin(picks_left)]

        self.basics, self.count_per_basic = self.get_basics(basic_count)
        self.main = deck + self.basics
        self.sideboard = picks_left
        return self.main, self.sideboard, self.count_per_basic

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

        # Translates the list basics to dictio
        for color in self.archetype.colors:
            basic_name = Deck.basic_names[color]
            count = basics.count(basic_name)
            self.count_per_basic[basic_name][0] = count

        return basics, self.count_per_basic

    def get_cards_per_category(self, base_infos, as_paths=True, lang="en"):
        """
        Returns card names or urls seperated per categories: per cmc [1-6+], land, sideboard
        :param base_infos: DataFrame
        :param as_paths: card names or paths?
        :param lang: en or fr
        :return: cards_per_cmc, lands, side_cards
        """
        print("Deck size: " + str(len(self.main) + len(self.sideboard)))
        main_rows = base_infos[base_infos["name"].isin(self.main)]

        land_rows = main_rows[main_rows["type_line"].apply(lambda t: t[:4] == "Land")]
        nonbasics = list(land_rows["name"])

        cards_per_cmc = {}
        for cmc in range(1, 7):
            if cmc in [2, 3, 4, 5]:
                rows_of_cmc = main_rows[main_rows["cmc"] == cmc]
            elif cmc == 1:
                rows_of_cmc = main_rows[main_rows["cmc"] <= cmc]
            else:
                rows_of_cmc = main_rows[main_rows["cmc"] >= cmc]
            cards = list(rows_of_cmc["name"])
            cards_per_cmc[cmc] = [c for c in cards if c not in nonbasics]

        side_rows = base_infos[base_infos["name"].isin(self.sideboard)]
        side_cards = list(side_rows["name"])

        if as_paths:
            cards_per_cmc = {
                i: [IoManager.get_img_path(card_name=card_name, lang=lang) for card_name in cards_per_cmc[i]] for i in
                range(1, 7)}
            nonbasics = [IoManager.get_img_path(card_name=card_name, lang=lang) for card_name in nonbasics]
            side_cards = [IoManager.get_img_path(card_name=card_name, lang=lang) for card_name in side_cards]
        return cards_per_cmc, nonbasics, side_cards, self.count_per_basic

    def get_deck_metrics(self, ratings):
        c = self.archetype.get_feature_name()
        main_rows = ratings[ratings["name"].isin(self.main)]
        main_ratings = main_rows[c]
        return main_ratings.sum(), main_ratings.sum() / ratings[c].sum(), main_ratings.mean(), main_ratings.min()

    def get_name(self):
        return self.drafter.name + ": " + self.archetype.name

    def is_failure(self, ratings):
        """
        Deck is a failure if it contains at least one card of rating 0
        :param ratings:
        :return:
        """
        return self.get_deck_metrics(ratings=ratings)[3] < 1
