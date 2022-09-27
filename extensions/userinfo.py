import re
from datetime import datetime
from itertools import chain
from emoji import emoji_list, replace_emoji
import hikari, lightbulb
import db
import numpy as np
import matplotlib.pyplot as plt

plugin = lightbulb.Plugin("userstats")

def add_emoji_count(cursor, usages):
    cursor.execute(f"""
        INSERT INTO emoji_counts (user, emoji, count)
        VALUES {','.join(['(?, ?, 1)'] * len(usages))} 
        ON CONFLICT (user, emoji) DO UPDATE
        SET count = emoji_counts.count + 1""",
        tuple(chain.from_iterable(usages)))

def remove_emoji_count(cursor, user_id, emoji):
    cursor.execute(f"""
        UPDATE emoji_counts
        SET count = count - 1
        WHERE user = ? AND emoji = ? AND count > 0""",
        (user_id, emoji))

def add_message_count(cursor, user_id):
    cursor.execute("""
        INSERT INTO message_counts (user, count)
        VALUES (?, 1)
        ON CONFLICT (user) DO UPDATE
        SET count = message_counts.count + 1""",
        (user_id,))

@plugin.listener(hikari.GuildReactionAddEvent)
async def analyse_reaction(event) -> None:
    cursor = db.cursor()
    if event.emoji_id is None:
        # Standard unicode emoji character
        add_emoji_count(cursor, [(event.user_id, event.emoji_name)])
    else:
        # Discord specific
        add_emoji_count(cursor, [(event.user_id, f'<:{event.emoji_name}:{event.emoji_id}>')])
    db.commit()

@plugin.listener(hikari.GuildReactionDeleteEvent)
async def remove_reaction(event) -> None:
    cursor = db.cursor()
    if event.emoji_id is None:
        # Standard unicode emoji character
        remove_emoji_count(cursor, event.user_id, event.emoji_name)
    else:
        # Discord specific
        remove_emoji_count(cursor, event.user_id, f'<:{event.emoji_name}:{event.emoji_id}>')
    db.commit()

@plugin.listener(hikari.GuildMessageCreateEvent)
async def analyse_message(event) -> None:
    if event.is_bot or not event.content:
        return
    cursor = db.cursor()
    add_message_count(cursor, str(event.author_id))
    custom_emoji = re.findall(r'<.?:.+?:\d+>', event.content)
    unicode_emoji = emoji_list(event.content)
    emoji = custom_emoji + [x['emoji'] for x in unicode_emoji]
    if len(emoji):
        add_emoji_count(cursor, [(str(event.author_id), e) for e in emoji])
    db.commit()

async def emoji_stats(ctx: lightbulb.Context, user) -> None:
    user_id = user.id
    cursor = db.cursor()
    cursor.execute("""
        SELECT emoji, count FROM emoji_counts
        WHERE user = ? AND count > 0
        ORDER BY count DESC
        LIMIT 5""",
        (user_id,))
    emoji = cursor.fetchall()
    emoji_list = []
    for rank in range(len(emoji)):
        emoji_list.append(f'`#{rank + 1}` {emoji[rank][0]} used `{emoji[rank][1]}` time(s)!')
    cursor.execute("""
        SELECT count FROM message_counts
        WHERE user = ?""",
        (user_id,))
    message_count = cursor.fetchone()
    if message_count:
        cursor.execute("""
            SELECT COUNT(*) + 1 FROM message_counts
            WHERE count > ?""",
            (message_count[0],))
        rank = cursor.fetchone()[0]

    embed = (
        hikari.Embed(
            title=f"{user.display_name}'s Message Stats",
            colour=0x3B9DFF,
            timestamp=datetime.now().astimezone()
        )
        .set_footer(
            text=f"Requested by {ctx.member.display_name}",
            icon=ctx.member.avatar_url or ctx.member.default_avatar_url,
        )
        .set_thumbnail(user.avatar_url or user.default_avatar_url)
        .add_field(
            "Total messages sent:",
            f'{"{:,}".format(message_count[0])} (#{rank})' if message_count else 'None',
            inline=False
        )
        .add_field(
            "Top 5 emojis:",
            '\n'.join(emoji_list) if len(emoji_list) else 'None',
            inline=False
        )
    )
    await ctx.respond(embed)

async def general_info(ctx: lightbulb.Context, target) -> None:
    target = ctx.get_guild().get_member(ctx.options.target or ctx.user)

    if not target:
        await ctx.respond("That user is not in the server.")
        return

    created_at = int(target.created_at.timestamp())
    joined_at = int(target.joined_at.timestamp())

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
        .add_field(
            "Joined server on",
            f"<t:{joined_at}:d>\n(<t:{joined_at}:R>)",
            inline=True,
        )
        .add_field(
            "Roles",
            ", ".join(r.mention for r in roles),
            inline=False,
        )
    )
    await ctx.respond(embed) # Respond to the interaction with the embed.

@plugin.command
@lightbulb.add_cooldown(10, 1, lightbulb.UserBucket)
@lightbulb.option("target", "The member to get information about.", hikari.User, required=True)
@lightbulb.option("type", "Which type of stats to show.", choices=["emoji", "general"], required=False)
@lightbulb.command("userinfo", "Get information about someone specific!")
@lightbulb.implements(lightbulb.PrefixCommand,lightbulb.SlashCommand)
async def main(ctx: lightbulb.Context) -> None:
    user = ctx.get_guild().get_member(ctx.options.target)
    if ctx.options.target and ctx.options.type == "general":
        await general_info(ctx, user)
    elif (ctx.options.target and ctx.options.type == "emoji") or not ctx.options.type:
        await emoji_stats(ctx, user)
    
def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)
