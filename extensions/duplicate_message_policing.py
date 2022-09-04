"""
Checks messages such that they are not duplicates of messages sent previously in the discord channel(s).
This is designed to increase the effort required by users. For example, the string 'lol' can only be used
once, and subsequent uses must get more creative (e.g. 'l0l', 'lolz', and so on).
Eventually, some time in the future, all possible strings will have been said, and the database will need to be reset.

Inspired by: https://blog.xkcd.com/2008/01/14/robot9000-and-xkcd-signal-attacking-noise-in-chat/
"""
import os, re
import hikari, lightbulb
import db
import sqlite3
import re

plugin = lightbulb.Plugin("duplicate_message_policing")
@plugin.listener(hikari.GuildMessageCreateEvent)
async def delete_duplicate(event: hikari.GuildMessageCreateEvent) -> None:
    """
    Deletes duplicate messages (excepting some). A duplicate message is simply a matching string
    that has been seen before in the server (and not deleted).
    """

    nodelete_flag = "!"
    # random rules. Probably worth thinking about this some more, if this bot function doesn't get deleted.
    if (
        (
            event.channel_id != os.environ.get("ORIGINALITY_CHANNEL_ID") and os.environ.get("DEBUG") is None
        )  # channel id is for #offtopic
        or event.is_webhook
        or event.content.startswith(nodelete_flag)
        or event.is_bot
        or not event.content
        or "http" in event.content  # allow links
        or "@" in event.content  # allow mentions
        or len(event.content) <= 2  # allow short messages
    ):
        # force the bot to not interact with this message at all e.g. in case of bug or in some other cases
        print("returning")
        return

    cursor = db.cursor()

    # todo: insert message exceptions such as emoji which are allowed to be duplicated
    try:
        cursor.execute(
            "insert into message_hashes values(?, ?, md5(?))",
            (event.author_id, event.message_id, event.content),
        )
        db.commit()
    except sqlite3.IntegrityError as e:
        await event.message.delete()
        await event.message.respond(
            f"Hey {event.author.mention}, your message: ```{event.message.content}``` was deleted as it is **not** unique. Either change your message a bit or add ! to the start of it :)", user_mentions=True
        )

@plugin.listener(hikari.GuildMessageDeleteEvent)
async def delete_hash(event: hikari.GuildMessageDeleteEvent) -> None:
    """
    Deletes a message record such that another user (or the same user) can send this message again.
    """
    cursor = db.cursor()
    cursor.execute("delete from message_hashes where message_id = ?", (event.message_id,))
    db.commit()

def load(bot: lightbulb.BotApp):
    bot.add_plugin(plugin)