import lightbulb
import requests

plugin = lightbulb.Plugin("YoMama")


@plugin.command
@lightbulb.command(
    "yomama", "Print an Yo Mama Joke"
)
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def main(ctx: lightbulb.Context) -> None:
    await ctx.respond(insult())


def insult() -> str:
    return get_random_insult()


def get_random_insult() -> str:
    response = requests.get("https://api.yomomma.info/")
    return response.json()["joke"]


def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)
