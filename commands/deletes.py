from datetime import datetime
import hikari, lightbulb
import db

plugin = lightbulb.Plugin("deletesinquiry")


async def show_deletes(ctx: lightbulb.Context) -> None:
    cursor = db.cursor()
    cursor.execute(
        """
        SELECT user, count FROM message_deletes
        ORDER BY count DESC
        LIMIT 5"""
    )
    deletes = cursor.fetchall()
    top_deleter = ctx.get_guild().get_member(deletes[0][0])
    delete_list = []
    for rank in range(len(deletes)):
        rank_str = f"`#{rank + 1}` {ctx.get_guild().get_member(deletes[rank][0]).display_name} has `{deletes[rank][1]}` message(s) deleted!"
        delete_list.append(rank_str)

    embed = (
        hikari.Embed(
            title=f"Sneaky Deleters ;)",
            colour=0x3B9DFF,
            timestamp=datetime.now().astimezone(),
        )
        .set_footer(
            text=f"Requested by {ctx.member.display_name}",
            icon=top_deleter.avatar_url or top_deleter.default_avatar_url,
        )
        .set_thumbnail(ctx.member.avatar_url or ctx.member.default_avatar_url)
        .add_field(
            "Top 5 deleters:",
            "\n".join(delete_list) if len(delete_list) else "None",
            inline=False,
        )
    )
    await ctx.respond(embed)


@plugin.command
@lightbulb.add_cooldown(10, 1, lightbulb.UserBucket)
@lightbulb.command("deletesinquiry", "Details the top deleters ;)")
@lightbulb.implements(lightbulb.SlashCommand)
async def main(ctx: lightbulb.Context) -> None:
    await show_deletes(ctx)


def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)
