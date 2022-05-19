import lightbulb
import requests

plugin = lightbulb.Plugin("Advice")


@plugin.command
@lightbulb.command(
    "advice", "Prints a Good Advice"
)
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def main(ctx: lightbulb.Context) -> None:
    await ctx.respond(insult())


def insult() -> str:
    return get_random_insult()


def get_random_insult() -> str:
    response = requests.get("https://api.adviceslip.com/advice")
    return response.json()["slip"]["advice"]


def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)
