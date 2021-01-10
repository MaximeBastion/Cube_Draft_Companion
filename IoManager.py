import ast
import os
from os import listdir
from os.path import isfile, join
import requests
import shutil
import pandas as pd


class IoManager:
    """
    Handles every input/output of the program
    Currently:
    * loads cube list and cards base data of startup
    * checks/downloads missing card images (en/fr) on startup
    """
    CUBE_LIST_FILE_PATH = "data/cube_list.txt"
    CARD_INFOS_FILE_PATH = "data/cube_list_base_data.csv"
    CARD_RATINGS_FILE_PATH = "data/archetype_ratings.csv"
    ARCH_PRESENCE_PATH = "data/archetype_presence.csv"
    CARD_IMAGES_PATH = "data/imgs"
    CARD_IMAGES_PATH_EN = CARD_IMAGES_PATH + "/en"
    CARD_IMAGES_PATH_FR = CARD_IMAGES_PATH + "/fr"
    SPRITE_DIR_PATH = "data/imgs/sprites/"
    BASIC_LANDS = ["Plains", "Island", "Swamp", "Mountain", "Forest"]
    BASIC_LANDS_URLS = {
        "Plains": "https://img.scryfall.com/cards/large/front/a/9/a9891b7b-fc52-470c-9f74-292ae665f378.jpg?1581719749",
        "Island": "https://img.scryfall.com/cards/large/front/a/c/acf7b664-3e75-4018-81f6-2a14ab59f258.jpg?1582126055",
        "Swamp": "https://img.scryfall.com/cards/large/front/0/2/02cb5cfd-018e-4c5e-bef1-166262aa5f1d.jpg?1582126067",
        "Mountain": "https://img.scryfall.com/cards/large/front/5/3/53fb7b99-9e47-46a6-9c8a-88e28b5197f1.jpg?1582126072",
        "Forest": "https://img.scryfall.com/cards/large/front/3/2/32af9f41-89e2-4e7a-9fec-fffe79cae077.jpg?1582126077"
    }

    def __init__(self, archetypes, download_missing_images=True):
        self.archetypes = archetypes
        self.cube_list = IoManager.get_cube_list()
        self.non_basics = self.get_nonbasic_lands_list()
        self.base_infos_df = IoManager.get_cards_base_info()
        self.ratings = self.get_ratings()
        if download_missing_images:
            self.download_missing_images()
        if not IoManager.arch_presence_exists():
            self.init_arch_presence()

    @staticmethod
    def get_cube_list():
        """

        :return: list of card names, cube list
        """
        f = open(IoManager.CUBE_LIST_FILE_PATH, "r")
        lines = f.readlines()
        f.close()
        # removing '\n' at then end of each name
        lines = [card_name[:-1] for card_name in lines]
        return lines

    @staticmethod
    def get_cards_base_info():
        """

        :return: DataFrame containing data for each card, such as power, toughness, urls...
        """
        df = pd.read_csv(IoManager.CARD_INFOS_FILE_PATH)
        for list_feature in ["colors", "color_identity"]:
            df[list_feature] = df[list_feature].apply(lambda e: e if type(e) != float else "[]")
            df[list_feature] = df[list_feature].apply(ast.literal_eval)
        return df

    def get_ratings(self):
        """
        Loads, scales, add sum and returns the card's ratings per archetype
        :return: DataFrame containing each archetype rating for each card
        """
        df = pd.read_csv(IoManager.CARD_RATINGS_FILE_PATH)
        df = IoManager.scale_ratings(df)
        df = IoManager.normalize_ratings_per_archetype(df)
        df = self.add_ratings_sum(df)
        #    print(df[["name", "monogreen", "simic_ramp", "general"]].tail(60))
        #    print(df[["name", "general"]].sort_values(ascending=False, by="general").head(50))
        return df

    @staticmethod
    def scale_ratings(ratings):
        """
        The gap between a 3 and a 4 is wider than 1/3 better
        :param ratings: df
        :return: updated df
        """
        mapping = {
            2: 3,
            3: 8,
            4: 30
        }
        ratings = ratings.applymap(lambda e: mapping[e] if e in mapping else e)
        return ratings

    @staticmethod
    def normalize_ratings_per_archetype(ratings):
        """
        Divides each rating by a value proportional to the sum of all the ratings in the archetype
        :param ratings:
        :return:
        """
        archetype_cols = [c for c in ratings.columns if c != "name"]
        n_cards = len(ratings["monored"])
        for arch_col in archetype_cols:
            ratings[arch_col] = ratings[arch_col] / (ratings[arch_col].sum() / n_cards)
        return ratings

    def add_ratings_sum(self, ratings):
        """
        Adds a column to the ratings DataFrame: 'general'
        :return: the updated DataFrame
        """
        rate_columns = [c for c in ratings.columns if c != "name"]

        coef_per_archetype = self.archetypes.get_color_coeffs()
        ratings["general"] = ratings[rate_columns].apply(lambda row: sum([row[c]*coef_per_archetype[c] for c in rate_columns]), axis=1)

        ratings["general_raw"] = ratings[rate_columns].sum(axis=1)
        return ratings

    def get_nonbasic_lands_list(self):
        """
        :return: a list of land names
        """
        return self.cube_list[320:]

    @staticmethod
    def get_downloaded_images(lang="en"):
        """
        Returns which cards we have downloaded images for (of the specified language, en or fr)
        :return: list of card names
        """
        path = IoManager.CARD_IMAGES_PATH_EN if lang == "en" else IoManager.CARD_IMAGES_PATH_FR
        file_names_en = [f for f in listdir(path) if
                         isfile(join(path, f))]
        card_names = [f[:-4] for f in file_names_en]
        return card_names

    def get_missing_images(self):
        """
        Returns which cards we miss images for
        :return: tuple: list of en missing, list of fr missing
        """
        downloaded_images_en = IoManager.get_downloaded_images(lang="en")
        downloaded_images_fr = IoManager.get_downloaded_images(lang="fr")
        complete_list = self.cube_list + IoManager.BASIC_LANDS
        missing_images_en = [card for card in complete_list if card not in downloaded_images_en]
        missing_images_fr = [card for card in complete_list if card not in downloaded_images_fr]
        return missing_images_en, missing_images_fr

    def download_card_images(self, card_names, lang="en"):
        """
        Downloads the en and fr card image of each card
        :param lang: en or fr
        :param card_names: list of card names
        :return:
        """
        for card_name in card_names:
            print("Dowloading card imgs for \'" + card_name + "\' (" + lang + ")")
            output_file_name = card_name + ".jpg"
            output_file_path = IoManager.CARD_IMAGES_PATH_EN + "/" + output_file_name if lang == "en" else IoManager.CARD_IMAGES_PATH_FR + "/" + output_file_name
            en_url, fr_url = self.get_card_urls(card_name)
            url = en_url if lang == "en" else fr_url
            # Open the url image, set stream to True, this will return the stream content.
            resp = requests.get(url, stream=True)
            # Open a local file with wb ( write binary ) permission.
            local_file = open(output_file_path, 'wb')
            # Set decode_content value to True, otherwise the downloaded image file's size will be zero.
            resp.raw.decode_content = True
            # Copy the response stream raw data to local image file.
            shutil.copyfileobj(resp.raw, local_file)
            # Remove the image url response object.
            del resp

    def get_card_urls(self, card_name):
        """
        :param card_name:
        :return: tuple: en url, fr url
        """
        if card_name in IoManager.BASIC_LANDS:
            return IoManager.BASIC_LANDS_URLS[card_name], IoManager.BASIC_LANDS_URLS[card_name]

        urls_df = self.base_infos_df[["name", "img_en_large", "img_fr_large"]]
        card_row = urls_df[urls_df["name"] == card_name]
        print(card_name)
        en_url = card_row["img_en_large"].iloc[0]
        fr_url = card_row["img_fr_large"].iloc[0]
        return en_url, fr_url

    def download_missing_images(self):
        """
        Checks for missing images, and downloads them if any are found
        :return:
        """
        print("\nChecking for missing images")
        missing_images_en, missing_images_fr = self.get_missing_images()
        for card_names, lang in [(missing_images_en, "en"), (missing_images_fr, "fr")]:
            if card_names:
                self.download_card_images(card_names, lang)

    @staticmethod
    def get_img_path(card_name, lang="en"):
        """

        :param card_name:
        :param lang: en or fr
        :return: path to the img
        """
        imgs_folder = IoManager.CARD_IMAGES_PATH_EN if lang == "en" else IoManager.CARD_IMAGES_PATH_FR
        return imgs_folder + "/" + card_name + ".jpg"

    @staticmethod
    def get_sprite_path(sprite_name):
        return IoManager.SPRITE_DIR_PATH + sprite_name


    @staticmethod
    def arch_presence_exists():
        return os.path.isfile(IoManager.ARCH_PRESENCE_PATH)

    def init_arch_presence(self):
        print("Initialising arch presence")
        df = pd.DataFrame(columns=self.archetypes.get_archetype_names(as_feature_names=True))
        df.to_csv(IoManager.ARCH_PRESENCE_PATH)
        return df

    @staticmethod
    def get_arch_presence():
        return pd.read_csv(IoManager.ARCH_PRESENCE_PATH, index_col=[0])

    def save_arch_presence(self, arch_presence_entries):
        """
        Adds the new entries to the db
        :param arch_presence_entries: [[1, 0, 0, 1, 1, 0], [1, 0, 1...]...] 1 for archetype was present at the draft
        :return: new_df
        """
        df = IoManager.get_arch_presence()
        print(len(arch_presence_entries[0]))
        df2 = pd.DataFrame(data=arch_presence_entries, columns=self.archetypes.get_archetype_names(as_feature_names=True))
        new_df = pd.concat([df, df2], sort=False)
        new_df = pd.concat([df, df2], sort=False)
        new_df.to_csv(IoManager.ARCH_PRESENCE_PATH)
        return new_df

