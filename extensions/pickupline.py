import random
import lightbulb
import os

import json
from datetime import datetime

import requests
from bs4 import BeautifulSoup

PICKUPLINE_CONFIG_DIR = "assets"
CONFIG_FILEPATH = os.path.join(PICKUPLINE_CONFIG_DIR, "pickuplinesgalore.json")
print(CONFIG_FILEPATH)
CATEGORY_CACHE_KEY = "{}-results"
LIST_OF_CATEGORIES_CACHE_KEY = "categories-list"

plugin = lightbulb.Plugin("PickUpLine")


@plugin.command
@lightbulb.option("keyword", "Category of Pickup Line to show", default="NA", type=str)
@lightbulb.command(
    "pickupline", "Prints a pick up line."
)
@lightbulb.implements(lightbulb.SlashCommand)
async def main(ctx: lightbulb.Context) -> None:
    await ctx.respond(PickupLinesGalore().get_pickupline(ctx.options.keyword))


class DiskCache:
    """
    A wrapper class to handle cache get/set on disk
    """

    def __init__(self, config_filepath):
        self.config_filepath = config_filepath
        self.config_dir = os.path.dirname(self.config_filepath)
        self.last_modified_at = None
        self.last_modified_days_ago = None
        # create config directory
        if not os.path.exists(self.config_dir):
            os.mkdir(self.config_dir)
        self.update_config_file_stat()

    def update_config_file_stat(self):
        if os.path.exists(self.config_filepath):
            last_modified_time = os.path.getmtime(self.config_filepath)
            self.last_modified_at = datetime.fromtimestamp(last_modified_time)
            self.last_modified_days_ago = (datetime.now() - self.last_modified_at).days

    def is_empty(self):
        return True if self.last_modified_at is None else False

    def get_json_data(self):
        if not os.path.exists(self.config_filepath):
            return {}
        with open(self.config_filepath, "r") as fp:
            return json.load(fp)

    def set_json_data(self, data):
        # overwrite everything in config_filepath with incoming data
        with open(self.config_filepath, "w") as fp:
            json.dump(data, fp)
        self.update_config_file_stat()

    def get(self, key):
        data = self.get_json_data()
        return data.get(key)

    def set(self, key, val):
        data = self.get_json_data()
        data[key] = val
        self.set_json_data(data)


def cache_to_disk(config_filepath):
    """
    Decorator to cache json results of funcs on a given filepath
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            data = func(*args, **kwargs)
            cache = DiskCache(config_filepath)
            cache.set_json_data(data)
            return data

        return wrapper

    return decorator


class PickupLinesGalore:

    def __init__(self, keyword=None):
        self.keyword = keyword
        self.cache = DiskCache(CONFIG_FILEPATH)

    @property
    def source_url(self):
        return "https://www.pickuplinesgalore.com/"

    def clean_line(self, line):
        return "\n".join(filter(lambda x: len(x.strip()) > 0, line.split("\n")))

    def get_list_of_categories(self):
        return self.cache.get(LIST_OF_CATEGORIES_CACHE_KEY) or []

    def parse_category(self, category, category_url):
        cat_cache_key = CATEGORY_CACHE_KEY.format(category)
        if self.cache.get(cat_cache_key) and self.cache.last_modified_days_ago < 100:
            return self.cache.get(cat_cache_key)
        resp = requests.get(category_url)
        if resp.status_code != 200:
            raise Exception("Error in fetching from {}".format(self.source_url))
        soup = BeautifulSoup(resp.content, "html.parser")
        lines = "\n".join(
            [self.clean_line(line.text.strip()) for line in soup.select("main > p.action-paragraph.paragraph > span")])
        result = [line.strip() for line in lines.split("\n") if line.strip()]
        self.cache.set(cat_cache_key, result)
        return result

    @cache_to_disk(CONFIG_FILEPATH)
    def _parse_index_page(self):
        resp = requests.get(self.source_url)
        if resp.status_code != 200:
            raise Exception("Error in fetching from {}".format(self.source_url))
        soup = BeautifulSoup(resp.content, "html.parser")
        a_tags = soup.findAll("a", {"class": "responsive-picture picture-link-1"})
        data = self.cache.get_json_data()
        categories = []
        for tag in a_tags:
            category_url = tag.attrs.get("href")
            category = category_url.replace(".html", "")
            data[category] = self.source_url + category_url
            categories.append(category)
        data[LIST_OF_CATEGORIES_CACHE_KEY] = categories
        return data

    def parse_index_page(self):
        if self.cache.is_empty() or self.cache.last_modified_days_ago > 100:
            return self._parse_index_page()
        return self.cache.get_json_data()

    def search(self, keyword):
        data = self.parse_index_page()
        if keyword == "na":
            keyword = random.choice(list(data.keys()))
        print(keyword)
        for category in data.keys():
            if keyword in category:
                return self.parse_category(category, data[category])
        return []

    def get_pickupline(self, keyword):

        lines = self.search(keyword.lower())
        if lines:
            return lines[random.randrange(1, len(lines) - 2)]


def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)
