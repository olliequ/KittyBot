import lightbulb
import requests

plugin = lightbulb.Plugin("Spam")


@plugin.command
@lightbulb.option("message", "Message to say",
                  required=True)
@lightbulb.option("n", "Number of Times",
                  required=True)
@lightbulb.command(
    "spam", "Prints the same Shit again and again as many times as you want"
)
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def main(ctx: lightbulb.Context) -> None:
    n = ctx.options.n
    message = ctx.options.message
    for i in range(int(n)):
        await ctx.respond(message)


def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)
