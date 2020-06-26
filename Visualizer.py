import pandas as pd
from IoManager import IoManager
import seaborn as sns
import matplotlib.pyplot as plt


class Visualizer:

    def __init__(self, io_manager: IoManager):
        self.io_manager = io_manager

    @staticmethod
    def visualize_arch_presence_correlations():
        arch_presence = IoManager.get_arch_presence()
        corr = arch_presence.corr()
        ax = sns.heatmap(
            corr,
            vmin=-1, vmax=1, center=0,
            cmap=sns.diverging_palette(20, 220, n=200),
            square=True
        )
        ax.set_xticklabels(
            ax.get_xticklabels(),
            rotation=45,
            horizontalalignment='right'
        )
        plt.show()

    @staticmethod
    def get_arch_combination_prob(archetype_names, archetypes):
        arch_presence = IoManager.get_arch_presence()
        feature_names = [archetypes.get_archetype_by_name(name).get_feature_name() for name in archetype_names]
        successes = arch_presence[arch_presence.apply(lambda row: row[feature_names].mean() == 1, axis=1)]
        return len(successes) / len(arch_presence)
