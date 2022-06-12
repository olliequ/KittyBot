import re
from datetime import datetime
from itertools import chain
from emoji import emoji_list
import hikari, lightbulb
import db

plugin = lightbulb.Plugin("Stats")

def add_emoji_count(cursor, usages):
    cursor.execute(f"""
        INSERT INTO emoji_counts (user, emoji, count)
        VALUES {','.join(['(?, ?, 1)'] * len(usages))} 
        ON CONFLICT (user, emoji) DO UPDATE
        SET count = emoji_counts.count + 1""",
        tuple(chain.from_iterable(usages)))

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

@plugin.listener(hikari.GuildMessageCreateEvent)
async def analyse_message(event) -> None:
    if event.is_bot or not event.content:
        return
    cursor = db.cursor()
    add_message_count(cursor, str(event.author_id))
    custom_emoji = re.findall(r'<:.+?:\d+>', event.content)
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
        WHERE user = ?
        ORDER BY count DESC
        LIMIT 10""",
        (user_id,))
    emoji = cursor.fetchall()
    cursor.execute("""
        SELECT count FROM message_counts
        WHERE user = ?""",
        (user_id,))
    message_count = cursor.fetchone()
    embed = (
        hikari.Embed(
            title=f"User Stats = {user.display_name}",
            description=f"ID: `{user.id}`",
            colour=0x3B9DFF,
            timestamp=datetime.now().astimezone()
        )
        .set_thumbnail(user.avatar_url or user.default_avatar_url)
        .add_field(
            "Messages sent",
            message_count[0] if message_count else 'None',
            inline=False
        )
        .add_field(
            "Top 10 emoji",
            ', '.join([f'{name} ({count})' for (name, count) in emoji]) if len(emoji) else 'None',
            inline=False
        )
    )
    await ctx.respond(embed)

async def show_message_stats(ctx: lightbulb.Context) -> None:
    MAX_BAR_LENGTH = 30
    SLICES_PER_CHAR = 8
    BLOCK_CODEPOINT = 0x2588
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
    for (user_id, message_count) in data:
        user = guild.get_member(user_id)
        if not user:
            display_name = str(user_id)
        else:
            display_name = user.display_name
        max_name_length = max(max_name_length, len(display_name))
        users_counts.append((display_name, message_count))
    message = ['```']
    for (name, count) in users_counts:
        line = f'{name.rjust(max_name_length)} : {str(count).rjust(max_messages_width)} '
        slices = int((MAX_BAR_LENGTH * SLICES_PER_CHAR) * (count / max_messages))
        bar = chr(BLOCK_CODEPOINT) * (slices // SLICES_PER_CHAR)
        if slices % SLICES_PER_CHAR > 0:
            bar += chr(BLOCK_CODEPOINT + SLICES_PER_CHAR - (slices % SLICES_PER_CHAR))
        message.append(line + bar)
    message.append('```')
    await ctx.respond('\n'.join(message))

@plugin.command
@lightbulb.add_cooldown(10, 1, lightbulb.UserBucket)
@lightbulb.option("target", "The member to show stats about.", hikari.User, required=False)
@lightbulb.command("userstats", "Get message stats")
@lightbulb.implements(lightbulb.PrefixCommand,lightbulb.SlashCommand)
async def main(ctx: lightbulb.Context) -> None:
    if ctx.options.target:
        user = ctx.get_guild().get_member(ctx.options.target)
        await show_user_stats(ctx, user)
    else:
        await show_message_stats(ctx)
    
def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)
