import random

from Drafter import Drafter
import pandas as pd

class Draft:

    def __init__(self, drafters: [Drafter], cube_list, ratings, nonbasic_list, pack_size=15, packs_per_player=3):
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
            drafter.build_deck(ratings=self.ratings, nonbasic_list=self.nonbasic_list)

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

    def simulate_multiple_drafts(self, amount, archetypes):
        historic = []
        arch_presence = []
        arch_names = archetypes.get_archetype_names()
        for i in range(amount):
            print("\nDraft n°" + str(i+1) + "/" + str(amount))
            self.launch()
            counts = self.get_archetype_counts(archetypes=archetypes)
            historic_entry = (self.get_drafter_scores(), counts)
            historic.append(historic_entry)
            arch_presence.append([1 if counts[a] > 0 else 0 for a in arch_names])
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
        return counts, mean_scores, arch_presence




