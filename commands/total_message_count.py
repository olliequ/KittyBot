import db
import lightbulb

plugin = lightbulb.Plugin("messagecount")


@plugin.command
@lightbulb.command(
    "messagecount",
    "Returns total server message count & the requesting user's message count.",
)
@lightbulb.implements(lightbulb.SlashCommand)
async def main(ctx: lightbulb.Context) -> None:
    if not ctx.member:
        return
    cursor = db.cursor()
    cursor.execute(
        """SELECT user, count FROM message_counts 
                      WHERE user = ?""",
        (ctx.member.id,),
    )
    data = cursor.fetchall()
    user_message_count = data[0][1]

    cursor.execute("""select sum(count) from message_counts""")
    data = cursor.fetchall()
    total_message_count = data[0][0]
    percentage = round(user_message_count * 100 / total_message_count, 2)

    response = f"""Total Server Messages: **{total_message_count:,}**\nMessages From {ctx.member.mention}: **{user_message_count:,}** ({percentage}%)"""
    await ctx.respond(response, user_mentions=True)


def load(bot: lightbulb.BotApp):
    bot.add_plugin(plugin)
