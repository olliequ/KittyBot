import os
import re
from itertools import chain
from typing import Sequence
from emoji import emoji_list
import hikari
import commons.db as db


def get_count_and_rank(cursor: db.Cursor, user_id: str):
    cursor.execute(
        """
        WITH ranks AS (
            SELECT user,
                   count,
                   rank() OVER (ORDER BY count DESC) AS rank
            FROM message_counts
        )
        SELECT count, rank
        FROM ranks
        WHERE user = ?""",
        (user_id,),
    )
    row = cursor.fetchone()
    if row:
        return (row[0], row[1])
    return (None, None)


def add_emoji_count(
    cursor: db.Cursor,
    usages: Sequence[tuple[str | hikari.Snowflake, str | hikari.UnicodeEmoji]],
):
    cursor.execute(
        f"""
        INSERT INTO emoji_counts (user, emoji, count)
        VALUES {','.join(['(?, ?, 1)'] * len(usages))} 
        ON CONFLICT (user, emoji) DO UPDATE
        SET count = emoji_counts.count + 1""",
        tuple(chain.from_iterable(usages)),
    )


def remove_emoji_count(cursor: db.Cursor, user_id: hikari.Snowflake, emoji: str):
    cursor.execute(
        f"""
        UPDATE emoji_counts
        SET count = count - 1
        WHERE user = ? AND emoji = ? AND count > 0""",
        (user_id, emoji),
    )


def add_message_count(cursor: db.Cursor, user_id: str):
    cursor.execute(
        """
        INSERT INTO message_counts (user, count)
        VALUES (?, 1)
        ON CONFLICT (user) DO UPDATE
        SET count = message_counts.count + 1""",
        (user_id,),
    )


def has_rank_changed(cursor: db.Cursor, user_id: str):
    cursor.execute(
        """
        WITH leads AS (
            SELECT user,
                   count - (LEAD(count) OVER (ORDER BY count DESC)) AS lead
            FROM message_counts
            ORDER BY count DESC
            LIMIT ?
        )
        SELECT lead FROM leads WHERE user = ?""",
        (int(os.getenv("RANK_CHANGE_FLOOR", "30")), user_id),
    )
    row = cursor.fetchone()
    if row is None:
        return False
    return row[0] == 1


def get_user_overtaken(cursor: db.Cursor, user_id: str) -> str | None:
    cursor.execute(
        """
        WITH ranked_users AS (
            SELECT user,
                   ROW_NUMBER() OVER (ORDER BY count DESC) AS rank
            FROM message_counts
        ),
        user_current_rank AS (
            SELECT rank
            FROM ranked_users
            WHERE user = ?
        )
        SELECT ru.user
        FROM ranked_users ru
        JOIN user_current_rank ucr ON ru.rank = ucr.rank + 1
        WHERE ru.user != ?;
        """,
        (user_id, user_id),
    )
    row = cursor.fetchone()
    if row is None:
        return None  # No user has fallen a place
    return row[0]  # Returns the ID of the user who fell a place


async def analyse_reaction(event: hikari.GuildReactionAddEvent) -> None:
    if event.emoji_name is None:
        return
    cursor = db.cursor()
    if event.emoji_id is None:
        # Standard unicode emoji character
        add_emoji_count(cursor, [(event.user_id, event.emoji_name)])
    else:
        # Discord specific
        add_emoji_count(
            cursor, [(event.user_id, f"<:{event.emoji_name}:{event.emoji_id}>")]
        )
    db.commit()


async def remove_reaction(event: hikari.GuildReactionDeleteEvent) -> None:
    if not event.emoji_name:
        return
    cursor = db.cursor()
    if event.emoji_id is None:
        # Standard unicode emoji character
        remove_emoji_count(cursor, event.user_id, event.emoji_name)
    else:
        # Discord specific
        remove_emoji_count(
            cursor, event.user_id, f"<:{event.emoji_name}:{event.emoji_id}>"
        )
    db.commit()


async def analyse_message(event: hikari.GuildMessageCreateEvent) -> None:
    if not event.is_human:
        return
    if not (event.content or len(event.message.attachments)):
        return

    user_id = str(event.author_id)
    cursor = db.cursor()
    add_message_count(cursor, user_id)

    if event.content:
        custom_emoji = re.findall(r"<.?:.+?:\d+>", event.content)
        unicode_emoji = emoji_list(event.content)
        emoji = custom_emoji + [x["emoji"] for x in unicode_emoji]
        if len(emoji):
            add_emoji_count(cursor, [(user_id, e) for e in emoji])

    if has_rank_changed(cursor, user_id) and (
        fallen_user := get_user_overtaken(cursor, user_id)
    ):
        await announce_rank_change(cursor, event, user_id, fallen_user)

    db.commit()


async def announce_rank_change(
    cursor: db.Cursor,
    event: hikari.GuildMessageCreateEvent,
    user_id: str,
    fallen_user: str,
):
    (count, rank) = get_count_and_rank(cursor, user_id)
    if count is None or rank is None:
        return
    await event.message.respond(
        f"Congratulations {event.author.mention} -  you've overtaken <@{fallen_user}> and are now ranked `#{rank}` with `{count:,}` messages! <@{fallen_user}>, do better <:kermitsippy:1019863020295442533>",
        user_mentions=True,
    )
