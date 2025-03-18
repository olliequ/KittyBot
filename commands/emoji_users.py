from datetime import datetime
import hikari, lightbulb
from commons.message_utils import get_member
import db

plugin = lightbulb.Plugin("Emoji lovers.")


def plural_or_not(number: int):
    if number == 1:
        return "time"
    else:
        return "times"


async def show_emoji_lovers(ctx: lightbulb.Context, emoji: str) -> None:
    if ctx.member is None:
        return
    cursor = db.cursor()
    cursor.execute(
        """
        SELECT user, count FROM emoji_counts
        WHERE emoji = ? AND count > 0
        ORDER BY count DESC
        LIMIT 5""",
        (emoji,),
    )
    users = cursor.fetchall()
    user_list = list[str]()
    for rank in range(len(users)):
        user = get_member(ctx, users[rank][0])  # Check user is still in server.
        if user is not None:
            user_list.append(
                f"`#{rank + 1}` {user.display_name} has used {emoji} `{users[rank][1]}` {plural_or_not(users[rank][1])}!"
            )
        else:  # Handle if user is no longer in the server (and thus doesn't have a display name).
            user_list.append(
                f"`#{rank + 1}` {users[rank][0]} has used {emoji} `{users[rank][1]}` {plural_or_not(users[rank][1])}!"
            )

    embed = (
        hikari.Embed(
            title=f"Biggest users of {emoji}!",
            colour=0x3B9DFF,
            timestamp=datetime.now().astimezone(),
        )
        .set_footer(
            text=f"Requested by {ctx.member.display_name}",
            icon=ctx.member.avatar_url,
        )
        .set_thumbnail(hikari.Emoji.parse(emoji).url)
        .add_field(
            "Top 5 lovers:",
            "\n".join(user_list) if len(user_list) else "None",
            inline=False,
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
