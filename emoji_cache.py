"""
Cache Custom Emojis Locally for Better Performance
"""

import io
import os

import lightbulb
from PIL import Image
from hikari import NotFoundError


async def cache_all_custom(bot: lightbulb.BotApp):
    emojis = await bot.rest.fetch_guild_emojis(int(os.environ["DEFAULT_GUILDS"].split(',')[0]))
    for emoji in emojis:
        await cache_emoji(emoji)


async def download_emoji(e, bot: lightbulb.BotApp):
    """
    Downloads Emoji if not present in Cache
    e: String emoji of form <:agentjohnson:1015917908897054770> or unicode
    """
    if e[0] != "<":
        return "Not Custom"  # Not a Custom Emoji

    # Get '1015917908897054770' from '<:agentjohnson:1015917908897054770>'
    emoji_id = e.replace("<", "").replace(">", "").split(":")[-1]
    if get_file_name_if_cached(emoji_id) is not None:
        return "Found"

    try:
        emoji = await bot.rest.fetch_emoji(int(os.environ["DEFAULT_GUILDS"].split(',')[0]), emoji_id)
    except NotFoundError:  # Emoji no longer available. Ignore
        return "Not Found"
    await cache_emoji(emoji)


async def cache_emoji(emoji):
    """
    emoji: hikari.emojis.CustomEmoji
    """
    if get_file_name_if_cached(emoji.id) is not None:
        return

    print("Downloading New Emoji", emoji)
    data = await emoji.read()
    image = Image.open(io.BytesIO(data))
    image.save(f"assets/{emoji.filename}", save_all=True)  # Required save_all to save in animated format


def get_file_name_if_cached(emoji):
    # Filters out the ID if in <> form. Doesn't affect if in int form
    emoji_id = str(emoji).replace("<", "").replace(">", "").split(":")[-1]

    for ext in ("gif", "png", "jpg"):  # Emoji can be cached in any format. So need to check all possible
        tp = f"assets/{emoji_id}.{ext}"
        if os.path.exists(tp):
            return tp
