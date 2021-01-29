import arcade
from App import App
from IoManager import IoManager, DataFetcher, RatingsInitializer
from Drafter import Drafter
from Archetypes import Archetypes
from Draft import Draft
from Visualizer import Visualizer
import pandas as pd
import Views

SCREEN_WIDTH = int(1920 * .5)
SCREEN_HEIGHT = int(1080 * .5)
SCREEN_TITLE = "Cube Draft Companion"


# Using arcade 2.3.15
def main():
    """ Main method """
    pd.set_option("display.max_columns", 10)
    pd.set_option('precision', 2)
    pd.set_option('expand_frame_repr', False)

    DataFetcher.update_base_data()
    archetypes = Archetypes()
    RatingsInitializer.prepare_new_ratings(archetypes=archetypes)
    io_manager = IoManager(download_missing_images=True, archetypes=archetypes)
    # Visualizer(io_manager=io_manager).visualize_arch_presence_correlations()
    #stats = get_stats_on_card_picks(io_manager=io_manager, archetypes=archetypes, max_amount=500)  # -> which cards should leave?

    players = [
        ("Max", "random"),
        ("Clem", "Aristocrats"),
        ("Cédric", "Dimir Reanimator"),
    ]
    players = []
    draft, n_simulations = draft_usable(players=players, io_manager=io_manager, archetypes=archetypes)
    print("\n" + str(n_simulations) + " drafts were necessary")
    decks = draft.get_decks()
    draft.save_decks_as_txts()

    launch_gui(decks=decks, io_manager=io_manager)


def get_necessary_simulations_stats(players, io_manager, archetypes, samples=100):
    n_s = []
    for i in range(samples):
        print("Sample " + str(i + 1) + "/" + str(samples))
        draft, n_simulations = draft_usable(players=players, io_manager=io_manager, archetypes=archetypes)
        n_s.append(n_simulations)
    mea = pd.Series(n_s).mean()
    print(n_s)
    print(mea)
    return mea


def draft_usable(players, io_manager, archetypes, max_amount=500):
    """
    Will simulates drafts until getting one where all players have a good deck
    :param max_amount:
    :param players:
    :param io_manager:
    :param archetypes:
    :return:
    """
    # Players
    drafters = []
    for name, arch in players:
        strategy = "open" if arch == "random" else "forcing"
        archetype = None if strategy == "open" else archetypes.get_archetype_by_name(name=arch)
        drafter = Drafter(name=name, strategy=strategy, archetype=archetype, archetypes=archetypes, is_ia=False)
        drafters.append(drafter)

    # IAs
    while len(drafters) < 8:
        name = "IA" + str(len(drafters) - len(players) + 1)
        drafter = Drafter(name=name, strategy="open", archetypes=archetypes, is_ia=True)
        drafters.append(drafter)

    draft = Draft(
        drafters=drafters,
        cube_list=io_manager.cube_list,
        ratings=io_manager.ratings,
        nonbasic_list=io_manager.non_basics,
        base_infos=io_manager.base_infos_df
    )

    counts, mean_scores, arch_presence, n_simulations = draft.simulate_multiple_drafts(max_amount=max_amount,
                                                                                       archetypes=archetypes,
                                                                                       stop_when_draft_is_usable=True)
    io_manager.save_arch_presence(arch_presence)
    return draft, n_simulations


def get_stats_on_card_picks(io_manager, archetypes, max_amount=100):
    # IAs
    drafters = []
    for i in range(8):
        name = "IA" + str(i)
        drafter = Drafter(name=name, strategy="open", archetypes=archetypes, is_ia=True)
        drafters.append(drafter)

    draft = Draft(
        drafters=drafters,
        cube_list=io_manager.cube_list,
        ratings=io_manager.ratings,
        nonbasic_list=io_manager.non_basics,
        base_infos=io_manager.base_infos_df
    )

    counts, mean_scores, arch_presence, n_simulations = draft.simulate_multiple_drafts(max_amount=max_amount,
                                                                                       archetypes=archetypes,
                                                                                       stop_when_draft_is_usable=False)

    print()


def launch_gui(decks, io_manager):
    window = App(decks=decks, io_manager=io_manager)
    window.setup(base_infos=io_manager.base_infos_df)
    arcade.run()


if __name__ == "__main__":
    # window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
    # start_view = Views.MenuView()
    # window.show_view(start_view)
    # arcade.run()
    main()
    """
    window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
    start_view = Views.PackView(pack=["Volcanic Island", "Snapcaster Mage", "Young Pyromancer"])
    window.show_view(start_view)
    arcade.run()
    """

    """
    counts, mean_scores, arch_presence = draft.simulate_multiple_drafts(1, archetypes=archetypes)
    print(counts)
    print(mean_scores)
    io_manager.save_arch_presence(arch_presence)
    """
