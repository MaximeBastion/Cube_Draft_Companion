from Archeytpe import Archetype
import pandas as pd

class Archetypes:

    def __init__(self):
        self.list = [
            Archetype("White Weenie", ["W"], "Aggro", "Flood the opponent with small creatures",
                      difficulty="easy", land_count=15),
            Archetype("Blink", ["W", "U"], "Midrange", "Abuse creatures enter the battlefield effects",
                      difficulty="hard", land_count=16),
            Archetype("Azorius Control", ["W", "U"], "Control", "Answer everything",
                      difficulty="hard", land_count=18),
            Archetype("Dimir Control", ["U", "B"], "Control", "Mess with your opponent",
                      difficulty="hard", land_count=17),
            Archetype("Dimir Reanimator", ["U", "B"], "Control", "Reanimate big baddies",
                      difficulty="hard", land_count=17),
            Archetype("Spellslinger", ["U", "R"], "Midrange", "Spam some lightning bolts and cantrips until they’re dead",
                      difficulty="medium", land_count=16),
            Archetype("Wildfire", ["U", "R"], "Control", "Blow up all the lands, but only your opponent needs them",
                      difficulty="hard", land_count=17),
            Archetype("Kiki Combo", ["U", "R"], "Combo", "Exodia, obliterate!",
                      difficulty="hard", land_count=17),
            Archetype("Simic Ramp", ["U", "G"], "Ramp", "Build your mana really fast and cast huge baddies",
                      difficulty="easy", land_count=16),
            Archetype("Monoblack", ["B"], "Midrange", "Disrupt, remove, pull ahead with efficiency and card advantage",
                      difficulty="medium", land_count=17),
            Archetype("Aristocrats", ["B", "R"], "Aggro", "Build a powerful slaughterhouse",
                      difficulty="hard", land_count=16),
            Archetype("Monored", ["R"], "Aggro", "Race to the face with small creatures and direct damage",
                      difficulty="easy", land_count=15),
            Archetype("Monogreen", ["G"], "Ramp", "Build your mana really fast and cast huge baddies",
                      difficulty="easy", land_count=16)
        ]

    def get_available(self, locked_colors):
        available = [a for a in self.list if a.is_available(locked_colors)]
        return available

    def get_archetype_by_name(self, name):
        for a in self.list:
            if a.name == name:
                return a
        return None

    def get_names(self):
        return [a.name for a in self.list]

    @staticmethod
    def difficulty_to_int(difficulty):
        if difficulty == "easy":
            return 1
        if difficulty == "medium":
            return 2
        return 3

    def get_archetype_sums(self, picks, ratings, sort=True, archetype_column_names=False):
        """
        What archetype do my picks have the most score towards?
        :param archetype_column_names: keys in series are column names?
        :param sort: Sort descending?
        :param picks:
        :param ratings:
        :return: Series archetype_name: sum, descending
        """
        if archetype_column_names:
            rating_sums = {a.get_feature_name(): a.get_rating_sum(picks, ratings) for a in self.list}
        else:
            rating_sums = {a.name: a.get_rating_sum(picks, ratings) for a in self.list}

        s = pd.Series(rating_sums)
        if sort:
            s = s.sort_values(ascending=False)
        return s

    def get_archetype_status(self, picks, ratings, commit_threshold_prop=.1, debug=False):
        """
        Is there an archetype I have enough ratings towards?
        :param picks:
        :param ratings:
        :param commit_threshold_prop: minimum amount of ratings to have towards the archetype as a proportion of the sum
         of ratings for this archetype
        :return: None, or Archetype obj
        """
        archetype_ratings = self.get_archetype_sums(picks=picks, ratings=ratings)
        best_archetype = archetype_ratings[archetype_ratings == archetype_ratings.max()]
        best_score = best_archetype.values[0]
        archetype = self.get_archetype_by_name(best_archetype.index[0])
        absolute_threshold = ratings[archetype.get_feature_name()].sum() * commit_threshold_prop
        if best_score >= absolute_threshold:
            if debug:
                print("Commiting with a score of " + str(best_score))
            # committing to the best archetype
            return archetype
        else:
            return None

    def get_color_coeffs(self):
        """
        Computes a coefficient for each archetype to compute a general rating per card
        This coefficient aims to take into account that some colors have many archetypes, making each of these
        archetypes less common, so give a lower general rating
        :return: dictionary a.feature_name: coef
        """
        colors = ["W", "U", "B", "R", "G"]
        n_archetypes_per_color = {color: 1 for color in colors}
        for color in colors:
            archetypes_of_color = self.get_available(locked_colors=[color])
            n_archetypes_per_color[color] = sum([1/len(a.colors) for a in archetypes_of_color]) #mono counts for 1, bicolor .5, tricolor .33
        coef_per_archetype = {a.get_feature_name(): 1 for a in self.list}
        for a in self.list:
            feature_name = a.get_feature_name()
            coef = sum([1/(n_archetypes_per_color[color]*len(a.colors)) for color in a.colors])
            coef_per_archetype[feature_name] = coef
        return coef_per_archetype

    def get_archetype_names(self, as_feature_names=False):
        if as_feature_names:
            return [a.get_feature_name() for a in self.list]
        else:
            return [a.name for a in self.list]

"""

    def get_average_difficulties(self):
        return {color: round(pd.Series([Archetypes.difficulty_to_int(a.difficulty)
                                        for a in self.get_available([color])]).mean(), 1) for color in colors}
"""
