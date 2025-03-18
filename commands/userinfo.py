from datetime import datetime
import hikari, lightbulb
from commons.message_utils import NoEntityError, get_member
import db

plugin = lightbulb.Plugin("userstats")


def plural_or_not(number: int):
    if number == 1:
        return "time"
    else:
        return "times"


def get_count_and_rank(cursor: db.Cursor, user_id: hikari.Snowflake):
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


async def emoji_stats(ctx: lightbulb.Context, user: hikari.Member) -> None:
    if not ctx.member:
        return
    user_id = user.id
    cursor = db.cursor()
    cursor.execute(
        """
        SELECT emoji, count FROM emoji_counts
        WHERE user = ? AND count > 0
        ORDER BY count DESC
        LIMIT 5""",
        (user_id,),
    )
    emoji = cursor.fetchall()
    emoji_list = list[str]()
    for rank in range(len(emoji)):
        emoji_list.append(
            f"`#{rank + 1}` {emoji[rank][0]} used `{emoji[rank][1]}` {plural_or_not(emoji[rank][1])}!"
        )

    (message_count, rank) = get_count_and_rank(cursor, user_id)
    embed = (
        hikari.Embed(
            title=f"{user.display_name}'s Message Stats",
            colour=0x3B9DFF,
            timestamp=datetime.now().astimezone(),
        )
        .set_footer(
            text=f"Requested by {ctx.member.display_name}",
            icon=ctx.member.avatar_url or ctx.member.default_avatar_url,
        )
        .set_thumbnail(user.avatar_url or user.default_avatar_url)
        .add_field(
            "Total messages sent:",
            f'{"{:,}".format(message_count)} (#{rank})' if message_count else "None",
            inline=False,
        )
        .add_field(
            "Top 5 emojis:",
            "\n".join(emoji_list) if len(emoji_list) else "None",
            inline=False,
        )
    )
    await ctx.respond(embed)


async def general_info(ctx: lightbulb.Context, target: hikari.Member) -> None:
    if not ctx.member:
        return

    created_at = int(target.created_at.timestamp())
    joined_at = int(target.joined_at.timestamp()) if target.joined_at else None

    roles = (await target.fetch_roles())[:]  # All but @everyone

    embed = (
        hikari.Embed(
            title=f"User Info - {target.display_name}",
            description=f"ID: `{target.id}`",
            colour=0x3B9DFF,
            timestamp=datetime.now().astimezone(),
        )
        .set_footer(
            text=f"Requested by {ctx.member.display_name}",
            icon=ctx.member.avatar_url or ctx.member.default_avatar_url,
        )
        .set_thumbnail(target.avatar_url or target.default_avatar_url)
        .add_field(
            "Bot?",
            str(target.is_bot),
            inline=True,
        )
        .add_field(
            "Created account on",
            f"<t:{created_at}:d>\n(<t:{created_at}:R>)",
            inline=True,
        )
    )
    if joined_at:
        embed.add_field(
            "Joined server on",
            f"<t:{joined_at}:d>\n(<t:{joined_at}:R>)",
            inline=True,
        )
    embed.add_field(
        "Roles",
        ", ".join(r.mention for r in roles),
        inline=False,
    )
    await ctx.respond(embed)  # Respond to the interaction with the embed.


@plugin.command
@lightbulb.add_cooldown(10, 1, lightbulb.UserBucket)
@lightbulb.option(
    "target", "The member to get information about.", hikari.User, required=True
)
@lightbulb.option(
    "type", "Which type of stats to show.", choices=["emoji", "general"], required=False
)
@lightbulb.command("userinfo", "Get information about someone specific!")
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def main(ctx: lightbulb.Context) -> None:
    try:
        user = get_member(ctx, ctx.options.target)
    except NoEntityError:
        await ctx.respond("That user is not in the server.")
        return
    if ctx.options.type == "general":
        await general_info(ctx, user)
    else:
        await emoji_stats(ctx, user)


def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)
