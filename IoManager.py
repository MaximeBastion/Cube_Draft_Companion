import ast
import os
from os import listdir
from os.path import isfile, join
import requests
import shutil
import pandas as pd
from pathlib import Path
import time
import numpy as np

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
    base_infos_data = None

    def __init__(self, archetypes, download_missing_images=True):
        self.archetypes = archetypes
        self.cube_list = IoManager.get_cube_list()
        self.non_basics = self.get_nonbasic_lands_list()
        self.base_infos_df = IoManager.get_cards_base_info()
        IoManager.base_infos_data = self.base_infos_df
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
        Path(path).mkdir(parents=True, exist_ok=True)
        file_names_en = [f for f in listdir(path) if
                         isfile(join(path, f))]
        card_names = [f[:-4] for f in file_names_en]
        card_names = [c.replace("__", "//") for c in card_names]  # to handle double-faced cards
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
            output_file_path = output_file_path.replace('//', '__')
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


class DataFetcher:
    """
    Used to get base card data from cube_list.txt using Scryfall api
    """

    @staticmethod
    def update_base_data():
        cube_list_file_name = "cube_list.txt"
        output_csv_name = "cube_list_base_data.csv"
        #DataFetcher.clean_double_faced_from_cube_list(cube_list_file_name=cube_list_file_name)
        new_base_data = DataFetcher.fetch_clean_save(cube_list_file_name=cube_list_file_name, output_csv_name=output_csv_name)
        if new_base_data is not None:
            print(new_base_data.tail(10))

    @staticmethod
    # Returns the infos for a card in english, with its fr img urls too
    def get_card_data(card_name):
        card_name = "\"" + card_name + "\""
        time.sleep(0.1)
        en_data = requests.get("https://api.scryfall.com/cards/search?q=!" + card_name).json()
        time.sleep(0.1)
        fr_data = requests.get("https://api.scryfall.com/cards/search?q=!" + card_name + "+lang%3Afr").json()
        en_output = en_data["data"][0]
        fr_output = fr_data["data"][0] if "data" in fr_data else None  # fr version my not exist
        if fr_output is None:
            print("French missing for " + card_name)

        # handling double-faced cards
        if "card_faces" in en_output and en_output["layout"] == "modal_dfc":
            full_name = en_output["name"]
            en_output = {**en_output, **en_output["card_faces"][0]}
            en_output["name"] = full_name
            if fr_output is not None:
                fr_output = fr_output["card_faces"][0]
        return en_output, fr_output

    @staticmethod
    # Returns a Dataframe containing the relevant fields of the cards in the list
    def get_cards_data(card_names):
        relevant_fields_en = [
            "name",
            "highres_image",
            "image_uris",
            "mana_cost",
            "cmc",
            "type_line",
            "power",
            "toughness",
            "colors",
            "color_identity"
        ]
        relevant_fields_fr = [
            "image_uris"
        ]
        raw_data = [DataFetcher.get_card_data(card_name) for card_name in card_names]
        df_content = {}
        for field in relevant_fields_en:
            df_content[field] = [data[0][field] if field in data[0] else np.nan for data in raw_data]
        for field in relevant_fields_fr:
            df_content[field + "_fr"] = [data[1][field] if data[1] is not None and field in data[1] else np.nan for data in
                                         raw_data]
        df = pd.DataFrame(df_content)
        return df

    @staticmethod
    def clean_double_faced_from_cube_list(cube_list_file_name):
        # removes the second face name for each double faced card
        f = open("data/" + cube_list_file_name, "r")
        lines = f.readlines()
        f.close()

        def rm_second_face(line):
            if "//" in line:
                return line.split(" //")[0] + "\n"
            return line

        lines = [rm_second_face(l) for l in lines]
        f = open("data/" + cube_list_file_name, "w")
        f.write("".join(lines))
        f.close()

    @staticmethod
    def get_cube_list(cube_list_file_name):
        f = open("data/" + cube_list_file_name, "r")
        lines = f.readlines()
        f.close()
        # removing '\n' at then end of each name
        lines = [card_name[:-1] for card_name in lines]
        return lines

    @staticmethod
    def infer_new_cards(cube_list, output_csv_name):
        prev_ratings = pd.read_csv("data/" + output_csv_name)
        new_cards = [c for c in cube_list if c not in prev_ratings.name.to_list()]
        print("There are {} new cards: \n{}".format(len(new_cards), new_cards))
        return new_cards

    @staticmethod
    # gets the cube list, fetches the data for each card, and saves the data as a csv
    def fetch_cube_data(cube_list_file_name, output_csv_name):
        cube_list = DataFetcher.get_cube_list(cube_list_file_name)
        new_cards = DataFetcher.infer_new_cards(cube_list, output_csv_name=output_csv_name)
        if not new_cards:
            return pd.DataFrame()
        cube_data = DataFetcher.get_cards_data(new_cards)
        return cube_data

    @staticmethod
    # creates seperate features to store each img url
    def clean_image_urls(cube_data):
        for lang in ["en", "fr"]:
            for image_type in ["small", "normal", "large", "png"]:
                feature_name = "img_" + lang + "_" + image_type
                current_feature = "image_uris" if lang == "en" else "image_uris_fr"
                cube_data[feature_name] = cube_data[current_feature].apply(
                    lambda d: d[image_type] if type(d) != float and d != None and image_type in d else np.nan)

    @staticmethod
    def clean_colors(cube_data):
        colors = ["W", "U", "B", "R", "G"]
        color_pairs = ["WU", "WB", "WR", "WG", "UB", "UR", "UG", "BR", "BR", "RG"]
        for color in colors:
            cube_data[color] = cube_data["color_identity"].apply(lambda l: 1 if color in l else 0)
        for c, c2 in color_pairs:
            cube_data[c + c2] = cube_data["color_identity"].apply(lambda l: 1 if c in l and c2 in l else 0)

    @staticmethod
    def clean_type_line(cube_data):
        cube_data["type_line"] = cube_data["type_line"].str.replace(' —', ':')

    @staticmethod
    def clean_cmc(cube_data):
        cube_data["cmc"] = cube_data["cmc"].astype(int)

    @staticmethod
    def remove_old_columns(cube_data):
        old_columns = ["image_uris", "image_uris_fr"]
        valid_columns = [c for c in cube_data.columns if c not in old_columns]
        return cube_data[valid_columns]

    @staticmethod
    def clean_booleans(cube_data):
        cube_data["highres_image"] = cube_data["highres_image"].astype(int)

    @staticmethod
    def clean_cube_data(cube_data):
        DataFetcher.clean_image_urls(cube_data)
        DataFetcher.clean_colors(cube_data)
        DataFetcher.clean_type_line(cube_data)
        DataFetcher.clean_cmc(cube_data)
        DataFetcher.clean_booleans(cube_data)
        return DataFetcher.remove_old_columns(cube_data)

    @staticmethod
    def save_csv(cube_data, output_csv_name, cube_list_file_name):
        current_data = pd.read_csv("data/" + output_csv_name)
        new_cards = DataFetcher.infer_new_cards(cube_list=DataFetcher.get_cube_list(cube_list_file_name=cube_list_file_name), output_csv_name=output_csv_name)
        new_rows = cube_data[cube_data.name.isin(new_cards)]
        new_cube_data = current_data.append(new_rows).reset_index(drop=True)
        new_cube_data.to_csv("data/" + output_csv_name, index=False)
        return new_cube_data

    @staticmethod
    # does it all
    def fetch_clean_save(cube_list_file_name, output_csv_name):
        cube_data = DataFetcher.fetch_cube_data(cube_list_file_name=cube_list_file_name, output_csv_name=output_csv_name)
        if len(cube_data.index) == 0:
            return None
        cube_data_clean = DataFetcher.clean_cube_data(cube_data)
        return DataFetcher.save_csv(cube_data=cube_data, output_csv_name=output_csv_name, cube_list_file_name=cube_list_file_name)


class RatingsInitializer:

    @staticmethod
    def prepare_new_ratings(archetypes):
        new_ratings = RatingsInitializer.setup_for_new_cards(RatingsInitializer.load_cards_df(), archetypes)
        if new_ratings is not None:
            RatingsInitializer.save_csv(new_ratings)
        return new_ratings

    @staticmethod
    def load_cards_df():
        df = pd.read_csv("data/cube_list_base_data.csv")
        for list_feature in ["colors", "color_identity"]:
            df[list_feature] = df[list_feature].apply(lambda e: e if type(e) != float else "[]")
            df[list_feature] = df[list_feature].apply(ast.literal_eval)
        return df

    @staticmethod
    def setup_for_new_cards(df, archetypes):
        new_df = pd.DataFrame({"name": df["name"]})
        for arch in archetypes.list:
            feature_name = arch.name.lower().replace(' ', '_')
            new_df[feature_name] = df["color_identity"].apply(lambda l: 9 if arch.is_available(l) else 0)

        # merging with existing ratings
        current_ratings = pd.read_csv("data/archetype_ratings.csv")
        new_cards = [c for c in df.name.to_list() if c not in current_ratings.name.to_list()]
        if new_cards:
            print("Preparing ratings for new cards: {}".format(new_cards))
            print("Make sure to manually replace 9 values by 0-4 values")
            exit()
        else:
            return None

        new_rows = new_df[new_df.name.isin(new_cards)]
        new_ratings = current_ratings.append(new_rows)
        return new_ratings

    @staticmethod
    def save_csv(new_df):
        new_df.to_csv("data/archetype_ratings.csv", index=False)
