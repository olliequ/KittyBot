"""
Checks messages such that they are not duplicates of messages sent previously in the discord channel(s).
This is designed to increase the effort required by users. For example, the string 'lol' can only be used
once, and subsequent uses must get more creative (e.g. 'l0l', 'lolz', and so on).
Eventually, some time in the future, all possible strings will have been said, and the database will need to be reset.

Inspired by: https://blog.xkcd.com/2008/01/14/robot9000-and-xkcd-signal-attacking-noise-in-chat/
"""

import os, re
import hashlib
import hikari
import behaviours
from commons.message_utils import get_member
import db
import sqlite3
import humanize
from datetime import datetime, timezone
import asyncio
import unicodedata


async def delete_duplicate(event: hikari.GuildMessageCreateEvent) -> None:
    """
    Deletes duplicate messages (excepting some). A duplicate message is simply a matching string
    that has been seen before in the server (and not subsequently deleted).
    """

    DELETION_NOTIFICATION_LONGEVITY = 15
    match (
        event.channel_id
        in [int(id) for id in os.environ.get("ORIGINALITY_CHANNEL_ID", "0").split(",")],
        os.environ.get("DEBUG", "false") in ("true", "1"),
    ):
        case (True, _):
            # handle all messages in defined channels
            pass
        case (_, True):
            # handle all messages when debug flag is set to True
            pass
        case (False, False):
            # don't handle any messages that are not in the originality channel when debug flag is not set
            return

    # allow these messages by default
    if (
        not event.content
        or event.is_webhook
        or event.is_bot
        or event.content.startswith("http")  # allow links
        or re.match(r"<@\d+>", event.content)  # allow mentions
        or re.fullmatch(
            r"<a?:[A-Za-z]+:\d+>", event.content
        )  # allow custom Discord 'emoji' in the format <:catswag:989147563854823444>
    ):
        # force the bot to not interact with this message at all
        return

    cursor = db.cursor()
    normalised_message_content = (
        unicodedata.normalize("NFKD", event.content).casefold().replace(" ", "")
    )

    try:
        cursor.execute(
            "insert into message_hashes values(?, ?, md5(?), ?)",
            (
                event.author_id,
                event.message_id,
                normalised_message_content,
                event.message.timestamp,
            ),
        )
        db.commit()
    except sqlite3.IntegrityError:
        await event.message.delete()
        previous = cursor.execute(
            "select user, message_id, time_sent from message_hashes where message_hash = md5(?)",
            (normalised_message_content,),
        ).fetchone()

        original_time_sent = datetime.fromisoformat(previous[2])

        response = await event.message.respond(
            f"Hey {event.author.mention}! Unfortunately,"
            f" your message: `{event.message.content}`"
            f" (first sent {humanize.naturaltime(datetime.now(timezone.utc) - original_time_sent)} by {get_member(event, previous[0]).display_name})"
            f" was deleted as it is ***NOT*** unique. Add some creativity to your message :robot:",
            user_mentions=True,
        )
        # delete deletion message after defined number of seconds (second best, due to inability to send ephemeral message directly)
        await asyncio.sleep(DELETION_NOTIFICATION_LONGEVITY)
        await response.delete()
        raise behaviours.EndProcessing()


async def delete_hash(event: hikari.GuildMessageDeleteEvent) -> None:
    """
    Deletes a message record such that another user (or the same user) can send this message again.
    """
    cursor = db.cursor()
    cursor.execute(
        "delete from message_hashes where message_id = ?", (event.message_id,)
    )
    db.commit()


def load():
    def md5(v: str) -> str:
        return hashlib.md5(v.encode("utf-8")).hexdigest()

    db.create_function("md5", 1, md5)
