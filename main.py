import arcade
from App import App
from IoManager import IoManager
from Drafter import Drafter
from Archetypes import Archetypes
from Draft import Draft
from Visualizer import Visualizer
import pandas as pd
import Views
SCREEN_WIDTH = 2560
SCREEN_HEIGHT = 1440
SCREEN_TITLE = "Cube Draft Companion"

def main():
    """ Main method """


if __name__ == "__main__":
    pd.set_option("display.max_columns", 10)
    pd.set_option('precision', 2)
    pd.set_option('expand_frame_repr', False)
    archetypes = Archetypes()
    io_manager = IoManager(download_missing_images=True, archetypes=archetypes)
    vis = Visualizer(io_manager)

    drafters = [
        Drafter(name="j1", strategy="open", archetypes=archetypes),
        Drafter(name="j2", strategy="open", archetypes=archetypes),
        Drafter(name="j3", strategy="open", archetypes=archetypes),
        Drafter(name="j4", strategy="open", archetypes=archetypes),
        Drafter(name="j5", strategy="open", archetypes=archetypes),
        Drafter(name="j6", strategy="open", archetypes=archetypes),
        Drafter(name="j7", strategy="open", archetypes=archetypes),
        Drafter(name="j8", strategy="open", archetypes=archetypes)
    ]
    draft = Draft(
        drafters=drafters,
        cube_list=io_manager.cube_list,
        ratings=io_manager.ratings,
        nonbasic_list=io_manager.non_basics
    )

    draft.launch()
    decks = draft.get_decks()
    deck = decks[0]
    print(deck.get_deck_metrics(io_manager.ratings))
    window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
    start_view = Views.PackView(pack=["Volcanic Island", "Snapcaster Mage"])
    window.show_view(start_view)
    #start_view.setup()
    arcade.run()

    """
    window = App(deck=deck, io_manager=io_manager)
    window.setup()
    arcade.run()
    
    counts, mean_scores, arch_presence = draft.simulate_multiple_drafts(1, archetypes=archetypes)
    print(counts)
    print(mean_scores)
    io_manager.save_arch_presence(arch_presence)
    """


    # main()
