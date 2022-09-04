from datetime import datetime
import hikari, lightbulb
import db

plugin = lightbulb.Plugin("Emoji stats.")

async def show_emoji_stats(ctx: lightbulb.Context, user, emoji) -> None:
    user_id = user.id
    cursor = db.cursor()
    cursor.execute("""
        SELECT count FROM emoji_counts
        WHERE user = ? AND emoji = ?
        """, (user_id, emoji))

    count = 0
    row = cursor.fetchone()
    if row is None:     # If the emoji isn't in the db for this user.
        await ctx.respond(f'{user.display_name} hasn\'t used {emoji} yet.')
        return
    else:
        count = row[0]  # Count of the emoji?

    cursor.execute("""
        SELECT COUNT(*) + 1 FROM emoji_counts
        WHERE count > ?
    """, (count,))
    rank = cursor.fetchone()[0]
    embed = (
        hikari.Embed(
            title=f"{user.display_name}'s usage of {emoji}:",
            colour=0x3B9DFF,
            timestamp=datetime.now().astimezone()
            )
            .set_footer(
            text=f"Requested by {ctx.member.display_name}",
            icon=ctx.member.avatar_url or ctx.member.default_avatar_url,
            )
            .set_thumbnail(user.avatar_url or user.default_avatar_url)
            .add_field(
            f"Stats:",
            f"""{emoji} has been used `{count}` time(s)!
            Across the server, {user.display_name} ranks `#{rank}` in using {emoji}.""",
            inline=False
            )
    )
    await ctx.respond(embed)

@plugin.command
@lightbulb.add_cooldown(10, 1, lightbulb.UserBucket)
@lightbulb.option("target", "The member to get information about.", hikari.User, required=True)
@lightbulb.option("emoji", "The Emoji to show Stats about", type=str, required=True)
@lightbulb.command("emojiusage", "Displays the usage of a specific Emoji for target user.")
@lightbulb.implements(lightbulb.SlashCommand)
async def main(ctx: lightbulb.Context) -> None:
    await show_emoji_stats(ctx, ctx.options.target, ctx.options.emoji)

def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)
