from Archeytpe import Archetype
import random
from Deck import Deck
from sklearn import preprocessing


class Drafter:

    def __init__(self, name, archetypes, archetype=None, is_ia=True, strategy="forcing", tie_strategy="random",
                 fallback_strategy="nice"):
        """

        :param name:
        :param archetype: obj
        :param is_ia:
        :param strategy: main strategy: 'forcing'=taking the best card for my archetype;
        'open'=taking the best overall cards until naturally ending up in an archetype
        :param tie_strategy: how to choose when multiple cards have the same rating? random/nice
        :param fallback_strategy: what to pick
        when nothing is interesting for me? 'nice'=take what is less useful to others
        """
        self.archetypes = archetypes
        self.fallback_strategy = fallback_strategy
        self.tie_strategy = tie_strategy
        self.archetype = archetype
        self.strategy = strategy
        self.name = name
        self.is_ia = is_ia
        self.picks = []
        self.historic = []
        self.pack = []
        self.deck: Deck = Deck(self.archetype)
        self.starting_strategy = strategy
        self.starting_archetype = archetype

    def select_pick(self, pack, ratings, debug=False):
        """

        :param pack: list of card names
        :param ratings: DataFrame containing the ratings of each card for each archetype
        :return: name of the card to pick according to the strategy
        """
        # what's my status?
        if self.strategy == "open" and not self.archetype:  # I started with an 'open' strategy
            new_arch = self.archetypes.get_archetype_status(picks=self.picks, ratings=ratings)
            if new_arch:  # But I now have found an archetype, pivoting to forcing it
                self.archetype = new_arch
                self.deck = Deck(new_arch)
                self.strategy = "forcing"
                if debug:
                    print(self.name + " is now forcing " + new_arch.name)
                    print(self.picks)

        pack_rows = ratings[ratings["name"].isin(pack)]

        if self.strategy == "open":

            if len(self.picks) == 0:
                max_general_rating = pack_rows["general"].max()
                max_general_rating_rows = pack_rows[pack_rows["general"] == max_general_rating]
                if max_general_rating == 0:
                    # pack is bad
                    return self.apply_fallback_strategy(max_general_rating_rows)
                else:
                    return self.apply_tie_strategy(max_general_rating_rows)

            # bumping up archetype ratings for which I have some points already, to progressively pivot
            sum_per_archetype = self.archetypes.get_archetype_sums(picks=self.picks, ratings=ratings, sort=False,
                                                                   archetype_column_names=True)
            sum_per_archetype = sum_per_archetype * len(self.archetypes.list) / sum_per_archetype.sum()
            # WOULD LIKE TO add smth to make extremes more extreme while preserving the sum

            pack_rows_copy = pack_rows.copy()
            for archetype in self.archetypes.list:
                c_name = archetype.get_feature_name()
                pack_rows_copy[c_name] = pack_rows_copy[c_name].apply(lambda rating: rating * sum_per_archetype[c_name])

            general_coef = 1 - .2*len(self.picks)
            if general_coef < 0:
                general_coef = 0
            forcing_coef = 1 - general_coef
            archetype_cols = [a.get_feature_name() for a in self.archetypes.list]
            coef_per_archetype = self.archetypes.get_color_coeffs()
            pack_rows_copy["instant_status_rating"] = pack_rows_copy[archetype_cols].apply(
                lambda row: sum([row[c] * coef_per_archetype[c] for c in archetype_cols]), axis=1)

            pack_rows_copy["instant_rating"] = pack_rows_copy.apply(
                lambda row: row["general"] * general_coef + row["instant_status_rating"] * forcing_coef, axis=1)
            max_rating = pack_rows_copy["instant_rating"].max()
            best_rows = pack_rows_copy[pack_rows_copy["instant_rating"] == max_rating]
            p = self.apply_tie_strategy(best_rows)

            if self.name == "j1" and debug:
                print(general_coef)
                print(forcing_coef)
                print(self.picks)
                print(sum_per_archetype.sort_values(ascending=False))
                """
                sum_per_archetype = sum_per_archetype * sum_per_archetype  # makes extremes more extreme
                sum_per_archetype = (sum_per_archetype - sum_per_archetype.min()) / (sum_per_archetype.max() - sum_per_archetype.min())
                print(sum_per_archetype)
                """
                print(pack_rows_copy[["name", "general_raw", "general", "instant_status_rating", "instant_rating"]].sort_values(by="instant_rating", ascending=False))
                print("->" + p)
            return p

        if self.strategy == "forcing":
            archetype_col_name = self.archetype.get_feature_name()
            max_rating = pack_rows[archetype_col_name].max()
            best_rows = pack_rows[pack_rows[archetype_col_name] == max_rating]
            # cards_of_max_rating = list(pack_rows[pack_rows[archetype_col_name] == max_rating]["name"])
            if max_rating == 0:
                # pack is bad for me
                return self.apply_fallback_strategy(best_rows)
            else:
                return self.apply_tie_strategy(best_rows)

    def apply_tie_strategy(self, tied_rows):
        if self.tie_strategy == "random":
            return random.choice(list(tied_rows["name"]))
        elif self.tie_strategy == "nice":
            nice_rows = Drafter.get_rows_of_min_general(tied_rows)
            return random.choice(list(nice_rows["name"]))

    def apply_fallback_strategy(self, tied_rows):
        if self.fallback_strategy == "random":
            return random.choice(list(tied_rows["name"]))
        elif self.fallback_strategy == "nice":
            nice_rows = Drafter.get_rows_of_min_general(tied_rows)
            return random.choice(list(nice_rows["name"]))

    @staticmethod
    def get_rows_of_min_general(rows):
        min_general_rating = rows["general"].min()
        rows_of_min_general_rating = rows[rows["general"] == min_general_rating]
        return rows_of_min_general_rating

    def pick(self, ratings):
        """
        Picks a card according to the strategy and removes it from the pack
        :param ratings: DataFrame containing the ratings of each card for each archetype
        :return: tuple: new pack, name of the pick
        """
        pick_name = self.select_pick(self.pack, ratings)
        self.picks.append(pick_name)
        historic_entry = (self.pack.copy(), pick_name)
        self.historic.append(historic_entry)
        del self.pack[self.pack.index(pick_name)]
        return self.pack, pick_name

    def build_deck(self, ratings, nonbasic_list):
        self.deck.build(picks=self.picks, ratings=ratings, nonbasic_list=nonbasic_list)
        return self.deck

    def reset(self):
        """
        Resets this drafter to its original state
        :return:
        """
        self.strategy = self.starting_strategy
        self.archetype = self.starting_archetype
        self.picks = []
        self.historic = []
        self.pack = []


