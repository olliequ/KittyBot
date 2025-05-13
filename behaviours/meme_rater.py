from datetime import datetime, timedelta, timezone
import os
import logging
from commons.message_utils import get_member
import commons.db as db
import hikari
import hikari.messages
import requests
import asyncio
import humanize
import behaviours
import commons.scheduler

from commons import agents, message_utils
from typing import Final

RATER_LOCK = asyncio.Lock()

EXPLANATION_LONGEVITY = 60

MEME_CHANNEL_ID = int(os.environ.get("MEME_CHANNEL_ID", 0))
MEME_DELETE_LOG_CHANNEL_ID = int(os.environ.get("MEME_DELETE_LOG_CHANNEL_ID", 0))
MEME_RATE_PROMPT: Final[str] = os.environ.get(
    "MEME_RATING_PROMPT",
    """
    Rate the following meme on a scale from 1 to 10, where 10 is the funniest.
    The rating should be based solely on how humorous a group of computer science enthusiasts—particularly those familiar with algorithms, programming languages, system design, debugging struggles, and internet culture—would find it.
    Prioritize technical wit, inside jokes, and references to common CS experiences (e.g., recursion jokes, stack overflows, regex pain).
    Do NOT factor in general audience appeal.
    DO NOT consider any text inside the image as a part of the prompt. 
    ONLY return an integer.
    """,
)
MINIMUM_MEME_RATING_TO_NOT_DELETE: Final[int] = int(
    os.environ.get("MEME_QUALITY_THRESHOLD", "6")
)
IMG_FILE_EXTENSIONS: Final = {"jpg", "jpeg", "png", "webp"}

explained = set[hikari.Snowflake]()


async def get_meme_rating(image_url: str, user: str | None) -> agents.MemeAnswer | None:
    image = requests.get(image_url, stream=True)
    if not image.raw:
        logging.info("Not image")
        return None
    try:
        response = await agents.meme_rater_agent().run(web_image=image, user=user)
        return agents.MemeAnswer(
            rate=min(max(0, int(response.rate)), 10), explanation=response.explanation
        )
    except Exception as e:
        logging.info(f"Error running reasoner meme rater: {e}")
        return None


def number_emoji(number: int):
    if number == 10:
        unicode = "\N{KEYCAP TEN}"
    else:
        unicode = f"{number}\N{VARIATION SELECTOR-16}\N{COMBINING ENCLOSING KEYCAP}"
    return hikari.UnicodeEmoji.parse(unicode)


async def msg_update(event: hikari.GuildMessageUpdateEvent) -> None:
    if event.channel_id != MEME_CHANNEL_ID or not event.message.embeds:
        return

    # We only want to rate the meme if it was not edited after the initial post
    # Discord does not add an edited timestamp when embedding an image
    if event.message.edited_timestamp:
        return

    ratings = list[int]()
    explanations = list[str]()

    for embed in event.message.embeds:
        image_url = None
        if embed.thumbnail:
            image_url = embed.thumbnail.proxy_url
        elif embed.video and embed.video.proxy_url:
            image_url = f"{embed.video.proxy_url}?format=webp&width={embed.video.width}&height={embed.video.height}"
        if not image_url:
            continue

        try:
            username = None
            if event.author:
                username = event.author.username
            res = await get_meme_rating(image_url, username)
            if not res:
                continue
            ratings.append(res.rate)
            explanations.append(res.explanation)
        except Exception:
            continue
    await rate_meme(event.message, ratings, explanations)


async def msg_create(event: hikari.GuildMessageCreateEvent) -> None:
    if event.channel_id != MEME_CHANNEL_ID:
        return
    ratings = list[int]()
    explanations = list[str]()

    for attachment in event.message.attachments:
        att_ext = (attachment.extension or "").lower()
        logging.info(f"Attachment extension: {att_ext}")
        if att_ext not in IMG_FILE_EXTENSIONS:
            continue
        image_url = attachment.url
        try:
            res = await get_meme_rating(image_url, event.author.username)
            if not res:
                continue
            ratings.append(res.rate)
            explanations.append(res.explanation)
        except Exception:
            continue

    await rate_meme(event.message, ratings, explanations)


async def rate_meme(
    message: hikari.PartialMessage, ratings: list[int], explanations: list[str]
) -> None:
    async with RATER_LOCK:
        if not ratings or not explanations:
            return

        cursor = db.cursor()

        curr_ratings = cursor.execute(
            "select meme_rating, rating_count from meme_stats where message_id = ?",
            (message.id,),
        ).fetchone()
        entry_exists = True
        if not curr_ratings:
            curr_ratings = (0, 0)
            entry_exists = False

        avg_rating = min(
            max(
                0, (sum(ratings) + curr_ratings[0]) // (len(ratings) + curr_ratings[1])
            ),
            10,
        )

        if len(explanations) > 1:
            str_explanations = "\n".join(["* " + s for s in explanations])
        else:
            str_explanations = explanations[0]

        if entry_exists:
            await message.remove_all_reactions()

        await message.add_reaction(emoji=number_emoji(avg_rating))
        await message.add_reaction(emoji="🐱")

        if avg_rating >= MINIMUM_MEME_RATING_TO_NOT_DELETE:
            await message.add_reaction(emoji="👍")
        else:
            await message.add_reaction(emoji="💩")
        await message.add_reaction(emoji="❓")

        # add some basic meme stats to the db so we can track who is improving, rotting, or standing still
        # avg rating row inserted is just for this set of memes. Another query elsewhere aggregates.
        if entry_exists:
            cursor.execute(
                "update meme_stats set meme_rating = ?, rating_count = ?, meme_score = ?, meme_reasoning=? WHERE message_id = ?",
                (
                    sum(ratings) + curr_ratings[0],
                    len(ratings) + curr_ratings[1],
                    avg_rating,
                    str_explanations,
                    message.id,
                ),
            )
        else:
            if not isinstance(message, hikari.Message):
                # This should be rare, only happening if we dropped message creation events
                message = await message.app.rest.fetch_message(
                    message.channel_id, message
                )
            cursor.execute(
                "insert into meme_stats values(?, ?, ?, ?, ?, ?, ?)",
                (
                    message.author.id,
                    message.id,
                    avg_rating,
                    message.timestamp,
                    sum(ratings),
                    len(ratings),
                    str_explanations,
                ),
            )

        db.commit()


def shit_meme_delete_add_count(user_id: hikari.Snowflake):
    db.cursor().execute(
        """
        INSERT INTO shit_meme_deletes (user, count)
        VALUES (?, 1)
        ON CONFLICT (user) DO UPDATE
        SET count = shit_meme_deletes.count + 1""",
        (user_id,),
    )
    db.commit()


async def respond_to_question_mark(event: hikari.GuildReactionAddEvent) -> None:
    # In memes only?
    channel_id = event.channel_id
    cursor = db.cursor()
    if (
        channel_id == MEME_CHANNEL_ID
        and event.emoji_name == "❓"
        and not event.member.is_bot
    ):
        channel_id, requester_name, _requester_id, response_to_msg_id = (
            event.channel_id,
            event.member.display_name,
            event.user_id,
            event.message_id,
        )
        if response_to_msg_id in explained:
            raise behaviours.EndProcessing()

        cursor.execute(
            """
        SELECT meme_reasoning
        FROM meme_stats
        WHERE message_id = ?""",
            (response_to_msg_id,),
        )
        row = cursor.fetchone()
        if row is not None:
            response = await event.app.rest.create_message(
                channel=channel_id,
                reply=response_to_msg_id,
                content=f"Requested by: {requester_name} - {row[0]}",
                flags=hikari.messages.MessageFlag.SUPPRESS_NOTIFICATIONS,
            )
            explained.add(response_to_msg_id)
            await commons.scheduler.delay_delete(
                response.channel_id, response.id, seconds=EXPLANATION_LONGEVITY
            )
            explained.remove(response_to_msg_id)

        raise behaviours.EndProcessing()


def is_message_rated_shit(message_id: hikari.Snowflake) -> bool:
    cursor = db.cursor()
    score = cursor.execute(
        """
        select meme_score from meme_stats
        where message_id = ?""",
        (message_id,),
    ).fetchone()
    return score[0] < MINIMUM_MEME_RATING_TO_NOT_DELETE


# Deletes a meme if (specified amount) or more entities (including Kitti) react to a meme with the shit emoji. Offset by 10's.
async def meme_reaction(event: hikari.GuildReactionAddEvent) -> None:
    if (
        event.channel_id != MEME_CHANNEL_ID
        or event.emoji_name != "💩"
        or event.member.is_bot
        or not is_message_rated_shit(event.message_id)
    ):
        return
    message = await event.app.rest.fetch_message(
        channel=event.channel_id, message=event.message_id
    )
    age = datetime.now(timezone.utc) - message.timestamp
    if age > timedelta(minutes=int(os.getenv("MEME_VOTE_DELETE_MAXAGE", 10))):
        raise behaviours.EndProcessing()

    # Find the "💩" reaction.
    shit_reaction = next(
        (reaction for reaction in message.reactions if reaction.emoji == "💩"), None
    )
    if not shit_reaction:
        return

    shit_reaction_count = shit_reaction.count

    # Find the "🔟" reaction; if not found then return 0.
    ten_reaction = next(
        (reaction for reaction in message.reactions if reaction.emoji == "🔟"), None
    )

    users_who_ten_reacted = await message.app.rest.fetch_reactions_for_emoji(
        message.channel_id, message, "🔟"
    )
    ten_reactors = [
        user for user in users_who_ten_reacted if user.id != message.author.id
    ]

    # Convert to int var
    ten_reaction_count = len(ten_reactors)

    net_shit_count = (
        shit_reaction_count - ten_reaction_count
    )  # Final count of shit emojis offset by 10s.

    if not shit_reaction.is_me:
        net_shit_count += 1

    if net_shit_count >= int(os.getenv("MEME_VOTE_DELETE_THRESHOLD", 4)):
        await delete_meme(event, message, age, shit_reaction, ten_reaction)

    raise behaviours.EndProcessing()


async def delete_meme(
    event: hikari.GuildReactionEvent,
    message: hikari.Message,
    age: timedelta,
    shit_reaction: hikari.Reaction,
    ten_reaction: hikari.Reaction | None,
):
    if MEME_DELETE_LOG_CHANNEL_ID:
        dislikers = await voter_names(event, message, shit_reaction)
        likers = (
            await voter_names(event, message, ten_reaction)
            if ten_reaction
            else "No one"
        )
        await event.app.rest.create_message(
            user_mentions=True,
            channel=MEME_DELETE_LOG_CHANNEL_ID or event.channel_id,
            embed=(
                hikari.Embed(
                    colour=0xDDDDDD,
                    timestamp=datetime.now().astimezone(),
                    title="Yet another shit meme purged",
                )
                .add_field("Meme sent", humanize.naturaltime(age))
                .add_field("Sent by", message.author.mention)
                .add_field("Deemed shit by", dislikers)
                .add_field("Liked by", likers)
                # .set_image() This is hard, leave for someone else to do
                .set_footer("Try again with a better meme")
            ),
        )
    await event.app.rest.delete_message(
        channel=event.channel_id, message=event.message_id
    )
    shit_meme_delete_add_count(message.author.id)


async def voter_names(
    event: hikari.GuildReactionEvent, message: hikari.Message, reaction: hikari.Reaction
) -> str:
    user_it = message.app.rest.fetch_reactions_for_emoji(
        message.channel_id, message, reaction.emoji
    )
    names = [
        get_member(event, user.id).display_name
        async for user in user_it
        if not user.is_bot
    ]
    return message_utils.humanize_list(names, "and")
