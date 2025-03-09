import lightbulb
import requests

plugin = lightbulb.Plugin("Advice")


@plugin.command
@lightbulb.command("advice", "Prints a piece of good advice.")
@lightbulb.implements(lightbulb.SlashCommand)
async def main(ctx: lightbulb.Context) -> None:
    await ctx.respond(advice())


def advice() -> str:
    return get_random_advice()


def get_random_advice() -> str:
    response = requests.get("https://api.adviceslip.com/advice")
    return response.json()["slip"]["advice"]


def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)
