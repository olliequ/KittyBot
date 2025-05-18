import os
import logging
import asyncio
import hikari

EMOJI_DIR = "assets/appemoji"
MAX_NAME_LEN = 32
FILE_EXTENSION = ".png"

emojidb = dict[str, hikari.KnownCustomEmoji]()


async def sync(bot: hikari.GatewayBot):
    global emojidb
    me = bot.get_me()
    if not me:
        raise ValueError("No sense of self")
    remote_emoji = await bot.rest.fetch_application_emojis(me.id)
    emojidb = {e.name: e for e in remote_emoji}
    remote_emoji_names = set(emojidb.keys())

    local_emoji_names = set[str]()
    for fname in os.listdir(EMOJI_DIR):
        if not fname.endswith(FILE_EXTENSION):
            continue  # skip non-image files
        emoji_name = os.path.splitext(fname)[0]
        if len(emoji_name) > MAX_NAME_LEN:
            logging.warning(f"Name {emoji_name} is too long")
            continue
        local_emoji_names.add(emoji_name)
    to_add = local_emoji_names.difference(remote_emoji_names)
    to_remove = remote_emoji_names.difference(local_emoji_names)
    logging.info(
        f"appemoji: {len(remote_emoji_names)} remote, {len(local_emoji_names)} local, {len(to_add)} to add, {len(to_remove)} to remove"
    )

    async def remove(name: str):
        logging.info(f"Remove appemoji {name}")
        await bot.rest.delete_application_emoji(me.id, emojidb[name])
        del emojidb[name]

    async def add(name: str):
        logging.info(f"Add appemoji {name}")
        emojidb[name] = await bot.rest.create_application_emoji(
            me.id,
            name=name,
            image=hikari.File(os.path.join(EMOJI_DIR, name + FILE_EXTENSION)),
        )

    await asyncio.gather(*map(remove, to_remove))
    await asyncio.gather(*map(add, to_add))


def get(name: str):
    return emojidb[name]
