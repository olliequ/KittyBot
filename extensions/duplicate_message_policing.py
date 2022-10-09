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
import humanize
from datetime import datetime, timezone
import asyncio

plugin = lightbulb.Plugin("duplicate_message_policing")


@plugin.listener(hikari.GuildMessageCreateEvent)
async def delete_duplicate(event: hikari.GuildMessageCreateEvent) -> None:
    """
    Deletes duplicate messages (excepting some). A duplicate message is simply a matching string
    that has been seen before in the server (and not deleted).
    """

    NODELETE_FLAG = "!"
    DELETION_NOTIFICATION_LONGEVITY = 15
    match (
        event.channel_id == int(os.environ.get("ORIGINALITY_CHANNEL_ID")),
        os.environ.get("DEBUG", "false") in ("true", "1"),
    ):
        case (True, _):
            # handle all messages in originality channel
            pass
        case (_, True):
            # handle all messages when debug flag is set to True
            pass
        case (False, False):
            # don't handle any messages that are not in the originality channel when debug flag is not set
            return

    # random rules. Probably worth thinking about this some more, if this bot function doesn't get deleted.
    if (
        not event.content
        or event.is_webhook
        or event.is_bot
        or event.content.startswith(NODELETE_FLAG)
        or len(event.content) <= 2  # allow short messages
        or "http" in event.content  # allow links
        or re.match(r"<@\d+>", event.content)  # allow mentions
        or re.fullmatch(
            r"<a?:[a-z]+:\d+>", event.content
        )  # allow custom Discord 'emoji' in the format <:catswag:989147563854823444>
    ):
        # force the bot to not interact with this message at all
        return

    cursor = db.cursor()

    # todo: insert message exceptions such as emoji which are allowed to be duplicated
    try:
        cursor.execute(
            "insert into message_hashes values(?, ?, md5(?), ?)",
            (event.author_id, event.message_id, event.content, event.message.timestamp),
        )
        db.commit()
    except sqlite3.IntegrityError as e:
        await event.message.delete()
        previous = cursor.execute(
            "select user, message_id, time_sent from message_hashes where message_hash = md5(?)",
            (event.content,),
        ).fetchone()

        original_time_sent = datetime.fromisoformat(previous[2])

        response = await event.message.respond(
            f"Hey {event.author.mention}! Unfortunately,"
            f" your message: `{event.message.content}`"
            f" (first sent {humanize.naturaltime(datetime.now(timezone.utc) - original_time_sent)} by {event.get_guild().get_member(previous[0]).display_name})"
            f" was deleted as it is ***NOT*** unique. Add some creativity to your message :robot:",
            user_mentions=True,
        )
        # delete deletion message after defined number of seconds (second best, due to inability to send ephemeral message directly)
        await asyncio.sleep(DELETION_NOTIFICATION_LONGEVITY)
        await response.delete()


@plugin.listener(hikari.GuildMessageDeleteEvent)
async def delete_hash(event: hikari.GuildMessageDeleteEvent) -> None:
    """
    Deletes a message record such that another user (or the same user) can send this message again.
    """
    cursor = db.cursor()
    cursor.execute(
        "delete from message_hashes where message_id = ?", (event.message_id,)
    )
    db.commit()


def load(bot: lightbulb.BotApp):
    bot.add_plugin(plugin)
