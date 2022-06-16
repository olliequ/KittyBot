import re
from datetime import datetime
from itertools import chain
from emoji import emoji_list, replace_emoji
import hikari, lightbulb
import db
import numpy as np
import matplotlib.pyplot as plt

plugin = lightbulb.Plugin("Stats")

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
    # print(event.content)
    custom_emoji = re.findall(r'<.?:.+?:\d+>', event.content)
    unicode_emoji = emoji_list(event.content)
    emoji = custom_emoji + [x['emoji'] for x in unicode_emoji]
    if len(emoji):
        add_emoji_count(cursor, [(str(event.author_id), e) for e in emoji])
    db.commit()

async def show_user_stats(ctx: lightbulb.Context, user) -> None:
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
            f'{message_count[0]} (#{rank})' if message_count else 'None',
            inline=False
        )
        .add_field(
            "Top 5 emojis:",
            '\n'.join(emoji_list) if len(emoji_list) else 'None',
            inline=False
        )
    )
    await ctx.respond(embed)

async def show_message_stats(ctx: lightbulb.Context, plot_type) -> None:
    guild = ctx.get_guild()
    cursor = db.cursor()
    cursor.execute("""
        SELECT user, count FROM message_counts
        ORDER BY count DESC
        LIMIT 10""")
    data = cursor.fetchall()
    if len(data) == 0:
        await ctx.respond("No one has said anything. How bizarre.")
        return
    max_messages = data[0][1]
    max_messages_width = len(str(max_messages))
    max_name_length = 0
    users_counts = []

    if plot_type == 1:
        for (user_id, message_count) in data:
            user = guild.get_member(user_id)
            if not user:
                display_name = str(user_id)
            else:
                display_name = replace_emoji(user.display_name, '')
            max_name_length = max(max_name_length, len(display_name))
            users_counts.append((display_name, message_count))
        MAX_BAR_LENGTH = 30
        SLICES_PER_CHAR = 8
        BLOCK_CODEPOINT = 0x2588
        message = ['**Messages Tally** :cat:```']
        for (name, count) in users_counts:
            line = f'{name.rjust(max_name_length)} : {str(count).rjust(max_messages_width)} '
            slices = int((MAX_BAR_LENGTH * SLICES_PER_CHAR) * (count / max_messages))
            bar = chr(BLOCK_CODEPOINT) * (slices // SLICES_PER_CHAR)
            if slices % SLICES_PER_CHAR > 0:
                bar += chr(BLOCK_CODEPOINT + SLICES_PER_CHAR - (slices % SLICES_PER_CHAR))
            message.append(line + bar)
        message.append('```')
        await ctx.respond('\n'.join(message))

    elif plot_type == 2:
        for (user_id, message_count) in data:
            user = guild.get_member(user_id)
            if not user:
                display_name = str(user_id)
            else:
                display_name = user.display_name
            max_name_length = max(max_name_length, len(display_name))
            users_counts.append((display_name, message_count))
        users = [pair[0] for pair in users_counts]
        counts = [pair[1] for pair in users_counts]
        print(f'{users}\n{counts}')

        fig, ax = plt.subplots(figsize=(11,5))
        bars = ax.bar(users, counts, color=['#C9B037', '#D7D7D7', '#6A3805', '#9fdbed', '#9fdbed', '#9fdbed', '#9fdbed', '#9fdbed', '#9fdbed', '#9fdbed'], edgecolor='black')
        ax.bar_label(bars)
        # ax.set_xlabel('Members', labelpad=10, color='#333333', fontsize='12')
        ax.set_ylabel('Total Messages', labelpad=15, color='#333333', fontsize='12')
        ax.set_title('Messages Tally!', pad=15, color='#333333', weight='bold', fontsize='15')
        ax.set_facecolor('#f5f5f5')
        plt.yticks(fontsize=8)
        plt.xticks(fontsize=(95/max_name_length))

        from io import BytesIO
        buffer = BytesIO()
        plt.savefig(buffer, format='png')
        await ctx.respond(hikari.Bytes(buffer.getvalue(), 'leaderboard.png'))

@plugin.command
@lightbulb.add_cooldown(10, 1, lightbulb.UserBucket)
@lightbulb.option("target", "The member to show stats about!", hikari.User, required=False)
@lightbulb.option("prettify", "Which graph to show!", type=bool, required=False)
@lightbulb.command("userstats", "Get message stats")
@lightbulb.implements(lightbulb.PrefixCommand,lightbulb.SlashCommand)
async def main(ctx: lightbulb.Context) -> None:
    if ctx.options.target:
        user = ctx.get_guild().get_member(ctx.options.target)
        await show_user_stats(ctx, user)
    elif ctx.options.prettify:
        await show_message_stats(ctx, 2)
    else:
        await show_message_stats(ctx, 1)
    
def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)
