# Cube Draft Companion

## Concept
GUI Python program allowing, using a cube list having cards manually rated for each archetype:
* Simulate bot drafts. Bots can either force a given archetype, or stay open until they have enough to commit to an archetype. Decks are automatically built after the draft.
* Visualize decks.
* Have stats about the average score of a given archetype, the average amount of them per table

# Technology
* Python
* Arcade library (GUI)
* pandas, numpy, matplotlib

# To self: how to update cube list
* Replace cube_list.txt by new CubeTutor txt export
* Anaconda: execute Data_Fetcher
* Anaconda: execute Companion
* Update last rows of archetype_ratings.csv: replace '9's with number from 0-4