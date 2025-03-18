import re
from itertools import chain
from typing import Sequence
from emoji import emoji_list
import hikari
import db


def decrement_emoji_count(cursor: db.Cursor, usages: Sequence[tuple[str, str]]):
    cursor.execute(
        f"""
        INSERT INTO emoji_counts (user, emoji, count)
        VALUES {','.join(['(?, ?, 0)'] * len(usages))} 
        ON CONFLICT (user, emoji) DO UPDATE
        SET count = emoji_counts.count - 1""",
        tuple(chain.from_iterable(usages)),
    )


async def delete_increment(event: hikari.GuildMessageDeleteEvent) -> None:
    """
    User has deleted a message -- update the count.
    """
    message_object = event.old_message
    if (
        message_object is None
    ):  # Then the message is really old and we can't retrieve its contents. Return to avoid exception.
        return

    user_id = (
        message_object.author.id
    )  # ID of the message author (not neccessarily the deleter).
    content = message_object.content  # Contents of message.
    if message_object.author.is_bot:
        return

    cursor = db.cursor()
    if content:
        custom_emoji = re.findall(r"<.?:.+?:\d+>", content)
        unicode_emoji = emoji_list(content)
        emoji = custom_emoji + [x["emoji"] for x in unicode_emoji]

        if len(emoji):
            decrement_emoji_count(cursor, [(str(user_id), e) for e in emoji])

    cursor.execute(
        """
        INSERT INTO message_deletes (user, count)
        VALUES (?, 1)
        ON CONFLICT (user) DO UPDATE
        SET count = message_deletes.count + 1""",
        (user_id,),
    )
    db.commit()
