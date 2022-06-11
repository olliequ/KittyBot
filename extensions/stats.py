import re
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
        add_emoji_count(cursor, [(event.user_id, str(event.emoji_id))])
    db.commit()

@plugin.listener(hikari.GuildMessageCreateEvent)
async def analyse_message(event) -> None:
    if event.is_bot or not event.content:
        return
    cursor = db.cursor()
    add_message_count(cursor, str(event.author_id))
    custom_emoji = re.findall(r'<:.+?:(\d+)>', event.content)
    unicode_emoji = emoji_list(event.content)
    emoji = custom_emoji + [x['emoji'] for x in unicode_emoji]
    if len(emoji):
        add_emoji_count(cursor, [(str(event.author_id), e) for e in emoji])
    db.commit()

def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)
