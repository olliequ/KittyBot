from datetime import datetime
import hikari, lightbulb
import db

plugin = lightbulb.Plugin("Emoji lovers.")

async def show_emoji_lovers(ctx: lightbulb.Context, emoji) -> None:
    # user_id = ctx.author
    cursor = db.cursor()
    cursor.execute("""
        SELECT user, count FROM emoji_counts
        WHERE emoji = ? AND count > 0
        ORDER BY count DESC
        LIMIT 5""",
        (emoji,))
    users = cursor.fetchall()
    user_list = []
    for rank in range(len(users)):
        user = ctx.get_guild().get_member(users[rank][0]) # Check user is still in server.
        if user is not None:
            user_list.append(f'`#{rank + 1}` {user.display_name} has used {emoji} `{users[rank][1]}` time(s)!')
        else:
            user_list.append(f'`#{rank + 1}` {users[rank][0]} has used {emoji} `{users[rank][1]}` time(s)!')

    embed = (
        hikari.Embed(
            title=f"Biggest users of {emoji}!",
            colour=0x3B9DFF,
            timestamp=datetime.now().astimezone()
            )
            .set_footer(
            text=f"Requested by {ctx.member.display_name}",
            icon=ctx.member.avatar_url,
            )
            .set_thumbnail(hikari.Emoji.parse(emoji).url)
            .add_field(
            "Top 5 lovers:",
            '\n'.join(user_list) if len(user_list) else 'None',
            inline=False
        )
    )
    await ctx.respond(embed)

@plugin.command
@lightbulb.add_cooldown(10, 1, lightbulb.UserBucket)
@lightbulb.option("emoji", "The emoji to show stats about", type=str, required=True)
@lightbulb.command("emojilovers", "Displays the top 5 users of a specific emoji.")
@lightbulb.implements(lightbulb.SlashCommand)
async def main(ctx: lightbulb.Context) -> None:
    await show_emoji_lovers(ctx, ctx.options.emoji)

def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)
