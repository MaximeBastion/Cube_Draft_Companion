class Archetype:

    def __init__(self, name, colors, style, concept, difficulty="medium", land_count=17):
        self.land_count = land_count
        self.style = style
        self.name = name
        self.colors = colors
        self.concept = concept
        self.difficulty = difficulty

    # is this archetype available given locked_colors?
    # all colors in locked_colors must be in the archetype
    def is_available(self, locked_colors):
        for locked_c in locked_colors:
            if locked_c not in self.colors:
                return False
        return True

    def get_feature_name(self):
        return self.name.lower().replace(' ', '_')

    # Returns the sum of the rating of all the cards in picks towards this archetype
    def get_rating_sum(self, picks, ratings_df):
        pick_rows = ratings_df[ratings_df["name"].isin(picks)][self.get_feature_name()]
        return pick_rows.sum()

    def __repr__(self):
        return self.name
