import random

from Deck import Deck
from Drafter import Drafter
import pandas as pd

class Draft:

    def __init__(self, drafters: [Drafter], cube_list, ratings, base_infos, nonbasic_list, pack_size=15, packs_per_player=3):
        self.base_infos = base_infos
        self.packs_per_player = packs_per_player
        self.pack_size = pack_size
        self.drafters = drafters
        self.cube_list = cube_list
        self.n_players = len(drafters)
        self.packs = []
        self.ratings = ratings
        self.nonbasic_list = nonbasic_list

    def generate_packs(self):
        """
        Generate all necessary packs for the draft
        :return: list of packs, which are list of cards
        """
        print("\nGenerating packs")
        cube_list_copy = [card for card in self.cube_list]
        n_packs = self.n_players * self.packs_per_player

        packs = []
        for i in range(n_packs):
            random_pack = []
            for j in range(self.pack_size):
                random_card = random.choice(cube_list_copy)
                random_pack.append(random_card)
                del cube_list_copy[cube_list_copy.index(random_card)]
            packs.append(random_pack)
        return packs

    def launch(self):
        print("\nLaunching the draft")
        self.packs = self.generate_packs()
        for round_index in range(self.packs_per_player):
            print("Round " + str(round_index + 1) + " starts")
            self.distribute_packs()
            for pick_index in range(self.pack_size):

                # make each drafter pick
                new_packs = []
                for drafter in self.drafters:
                    new_pack, pick = drafter.pick(ratings=self.ratings)
                    new_packs.append(new_pack)

                # make each drafter give its pack to the next drafter
                for i, drafter in enumerate(self.drafters):
                    next_drafter_index = i+1 if i < len(self.drafters)-1 else 0
                    next_drafter = self.drafters[next_drafter_index]
                    next_drafter.pack = new_packs[i]

        self.build_decks()

    def distribute_packs(self):
        """
        Give a pack taken at random from the pool to each player
        """
        random_pack_indexes = random.sample(range(len(self.packs)), self.n_players)
        packs_to_distribute = [self.packs[i] for i in random_pack_indexes]
        for i, drafter in enumerate(self.drafters):
            drafter.pack = packs_to_distribute[i]

        # removing these packs from the pool
        self.packs = [self.packs[pack_index] for pack_index in range(len(self.packs)) if pack_index not in random_pack_indexes]

    def build_decks(self):
        for drafter in self.drafters:
            drafter.build_deck(ratings=self.ratings, nonbasic_list=self.nonbasic_list, base_infos=self.base_infos)

    def get_decks(self):
        return [d.deck for d in self.drafters]

    def get_drafter_scores(self):
        """

        :return: [(arch name, score(=prop of sum of ratings)]
        """
        drafter_scores = [(drafter.archetype.name if drafter.archetype else "Fail", drafter.deck.get_deck_metrics(ratings=self.ratings)[1]) for drafter in self.drafters]
        return drafter_scores

    def get_archetype_counts(self, archetypes):
        decks = self.get_decks()
        count_per_archetype = {a.name: len([deck for deck in decks if deck.archetype.name == a.name]) for a in archetypes.list}
        return count_per_archetype

    def reset(self):
        """
        Resets the drafters to their original state
        :return:
        """
        for drafter in self.drafters:
            drafter.reset()

    def simulate_multiple_drafts(self, max_amount, archetypes, stop_when_draft_is_usable=True):
        historic = []
        arch_presence = []
        arch_names = archetypes.get_archetype_names()
        n_simulations = 0
        n_drafts = 0
        pick_ranks = []
        mains = []
        sides = []
        for i in range(max_amount):
            print("\nDraft n°" + str(i+1) + "/" + str(max_amount))
            n_drafts += 1
            self.launch()
            counts = self.get_archetype_counts(archetypes=archetypes)
            historic_entry = (self.get_drafter_scores(), counts)
            historic.append(historic_entry)
            pick_ranks.append(self.get_pick_rank_per_card_for_one_draft())

            mains_one_draft = self.drafters[0].deck.main
            sides_one_draft = self.drafters[0].deck.sideboard
            for drafter in self.drafters[1:]:
                mains_one_draft += drafter.deck.main
                sides_one_draft += drafter.deck.sideboard
            mains += mains_one_draft
            sides += sides_one_draft

            arch_presence.append([1 if counts[a] > 0 else 0 for a in arch_names])
            if stop_when_draft_is_usable and self.draft_is_usable():
                print("\nThis draft is suitable!")
                n_simulations = i + 1
                break
            self.reset()

        counts_per_archetype = {}
        scores_per_archetype = {}
        for drafter_scores, archetype_counts in historic:
            for arch_name in arch_names:
                if arch_name in counts_per_archetype:
                    counts_per_archetype[arch_name] += archetype_counts[arch_name]
                else:
                    counts_per_archetype[arch_name] = archetype_counts[arch_name]

                scores_of_archetype = [entry[1] for entry in drafter_scores if entry[0] == arch_name]
                if arch_name in scores_per_archetype:
                    scores_per_archetype[arch_name] += scores_of_archetype
                else:
                    scores_per_archetype[arch_name] = scores_of_archetype

        data_per_archetype = {}
        for arch_name in arch_names:
            count = counts_per_archetype[arch_name]
            mean_score = pd.Series(scores_per_archetype[arch_name]).mean()
            data_per_archetype[arch_name] = (count, mean_score)

        counts = pd.Series(counts_per_archetype)
        counts = counts.sort_values(ascending=False) / counts.sum()
        mean_scores = {a: data_per_archetype[a][1] for a in data_per_archetype.keys()}
        mean_scores = pd.Series(mean_scores).sort_values(ascending=False)

        # mean pick ranks to evaluate cards
        mean_pick_ranks = self.get_card_stats(pick_ranks=pick_ranks, n_drafts=n_drafts, mains=mains, sides=sides)

        return counts, mean_scores, arch_presence, n_simulations

    def draft_is_usable(self):
        """
        Weather or not player decks are not failures
        :return:
        """
        for drafter in self.drafters:
            if not drafter.is_ia and drafter.deck.is_failure(ratings=self.ratings):
                print(drafter.name + " failed")
                return False
        return True

    def get_pick_rank_per_card_for_one_draft(self) -> {}:
        """
        Compiles a dictionary with {card: pick_rank} for one draft
        :return: {card: pick_rank}
        """
        pick_rank_per_card = {}
        for drafter in self.drafters:
            pick_rank_per_card_drafter = drafter.get_rank_per_pick_made()
            pick_rank_per_card = {**pick_rank_per_card, **pick_rank_per_card_drafter}
        return pick_rank_per_card

    def get_card_stats(self, pick_ranks, mains, sides, n_drafts) -> pd.DataFrame:
        """
        Compiles a df giving various stats on card picks and main/side
        -> which ones should leave?
        Saves it as a local csv
        :return: df
        """
        # mean pick ranks
        total_pick_rank = {card: 0 for card in self.cube_list}
        for pick_rank in pick_ranks:
            total_pick_rank = Draft.sum_dictionaries(total_pick_rank, pick_rank)
        # ranking
        df = pd.DataFrame({"card": list(total_pick_rank.keys()), "pick_rank_sum": list(total_pick_rank.values())})
        df["mean_pick_rank"] = df.pick_rank_sum / n_drafts
        df = df.sort_values("mean_pick_rank").reset_index(drop=True)
        df["mean_pick_rank_rank"] = df.apply(lambda row: int(row.name) + 1, axis=1)

        # main VS side
        vc_main = pd.Series(mains).value_counts().to_frame(name="main_count")
        vc_side = pd.Series(sides).value_counts().to_frame(name="side_count")
        main_v_side_df = vc_main.merge(vc_side, how="outer", left_index=True, right_index=True).fillna(0)
        main_v_side_df = main_v_side_df[  # removes basics
            main_v_side_df.apply(lambda row: row.name not in list(Deck.basic_names.values()), axis=1)
        ]
        main_v_side_df["main_ratio"] = main_v_side_df.main_count / (main_v_side_df.main_count + main_v_side_df.side_count)
        main_v_side_df["card"] = main_v_side_df.index
        # ranking
        main_v_side_df = main_v_side_df.sort_values("main_ratio", ascending=False).reset_index(drop=True)
        main_v_side_df["main_ratio_rank"] = main_v_side_df.apply(lambda row: int(row.name) + 1, axis=1)

        # taking into account the max rating a card has among all archetypes -> not remove those that are a 4 somewhere
        base_ratings = pd.read_csv("data/archetype_ratings.csv")
        base_ratings["max_rating"] = base_ratings.max(axis=1)
        '''
        three_plus_cards = base_ratings[
            base_ratings.apply(lambda row: sum([1 for value in row[1:] if value >= 3]) > 0, axis=1)
        ].name
        df = df[~df.card.isin(three_plus_cards)]
        '''

        # merging
        df = df\
            .merge(main_v_side_df, how="outer", on="card")\
            .merge(base_ratings[["name", "max_rating"]], how="left", left_on="card", right_on="name")

        # Equity = how late is it taken * how often does it make the main (counts for .3) * max single rating
        # Equity = 1 / Equity
        # Equity = Equity / max(Equity) -> this equity is only 5% of the max equity
        df["equity"] = ((df.mean_pick_rank_rank + df.main_ratio_rank * .3) / 1.3) / df.max_rating.apply(lambda n: .1 if n == 0 else n)
        df.equity = 1 / df.equity
        max_equity = df.equity.max()
        df.equity = df.equity / max_equity * 100
        df = df.sort_values("equity", ascending=False).reset_index(drop=True)
        important_cols = ["card", "mean_pick_rank_rank", "main_ratio_rank", "max_rating", "equity"]
        cols_sorted = important_cols + [c for c in df.columns if c not in important_cols]
        df = df[cols_sorted]

        # saving as local csv
        df.to_csv("data/card_stats.csv", index=False)

        return df

    @staticmethod
    def sum_dictionaries(d, d2):
        d3 = {}

        common_keys = [k for k in d.keys() if k in d2.keys()]
        for key in common_keys:
            d3[key] = d[key] + d2[key]

        # unique keys
        for key in [k for k in d.keys() if k not in common_keys]:
            d3[key] = d[key]
        for key in [k for k in d2.keys() if k not in common_keys]:
            d3[key] = d2[key]

        return d3



