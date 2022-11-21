"""
Cache Custom Emojis Locally for Better Performance
"""

import io
import os

import lightbulb
from PIL import Image
from hikari import NotFoundError

import db


def get_f_name(emoji):
    return f"assets/{emoji.filename}"


async def cache_all_custom(bot: lightbulb.BotApp):
    emojis = await bot.rest.fetch_guild_emojis(int(os.environ["DEFAULT_GUILDS"].split(',')[0]))
    for emoji in emojis:
        await cache_emoji_if_not_present(emoji)


async def download_emoji(e, bot: lightbulb.BotApp):
    if e[0] != "<":
        return "Not Custom"  # Not a Custom Emoji
    # Get '1015917908897054770' from '<:agentjohnson:1015917908897054770>'
    emoji_id = e.replace("<", "").replace(">", "").split(":")[-1]

    # Get Emoji list from the first guild
    try:
        emoji = await bot.rest.fetch_emoji(int(os.environ["DEFAULT_GUILDS"].split(',')[0]), emoji_id)
    except NotFoundError:  # Emoji no longer available. Ignore
        return "Not Found"
    await cache_emoji_if_not_present(emoji)


async def cache_emoji_if_not_present(emoji):
    f_name = get_f_name(emoji)
    cursor = db.cursor()
    cursor.execute("""SELECT emoji FROM emoji_cache WHERE emoji=?""", (str(emoji),))
    if len(cursor.fetchall()) == 0:
        data = await emoji.read()
        image = Image.open(io.BytesIO(data))
        image.save(f_name, save_all=True)  # Required save_all to save in animated format
        cursor.execute("INSERT INTO emoji_cache (emoji,filename) VALUES (?,?)", (str(emoji), emoji.filename))
        db.commit()  # Forgot Commit so potential speed up


def get_file_name(emoji):
    cursor = db.cursor()
    cursor.execute("SELECT filename FROM emoji_cache WHERE emoji=?", (emoji,))
    return cursor.fetchone()[0]
