"""
Cache Custom Emojis Locally for Better Performance
"""

import os
import hikari
import lightbulb
from hikari import CustomEmoji, NotFoundError
import requests


async def get_file_name(emoji: str, bot: lightbulb.BotApp) -> str | None:
    """
    Return a path to the image file for the specified custom emoji. Returns None
    if emoji does not exist or is not a custom emoji.
    """
    try:
        emoji_id = CustomEmoji.parse(emoji).id
    except ValueError:
        return None

    cache_result = _get_cached_file_name(emoji_id)
    if cache_result:
        return cache_result

    await _download_emoji(emoji_id, bot)
    cache_result = _get_cached_file_name(emoji_id)
    if cache_result:
        return cache_result


def _get_cached_file_name(emoji_id: hikari.Snowflake) -> str | None:
    for ext in (
        "gif",
        "png",
        "jpg",
    ):  # Emoji can be cached in any format. So need to check all possible
        tp = f"assets/{emoji_id}.{ext}"
        if os.path.exists(tp):
            return tp


async def _download_emoji(emoji_id: hikari.Snowflake, bot: lightbulb.BotApp):
    try:
        info = await bot.rest.fetch_emoji(
            int(os.environ["DEFAULT_GUILDS"].split(",")[0]), emoji_id
        )
    except NotFoundError:  # Emoji no longer available. Ignore
        return

    print("Downloading New Emoji", info, info.url)
    r = requests.get(info.url)
    with open(f"assets/{info.filename}", "wb") as outfile:
        outfile.write(r.content)
