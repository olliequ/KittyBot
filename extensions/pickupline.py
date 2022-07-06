import lightbulb
import requests

plugin = lightbulb.Plugin("PickUpLine")

@plugin.command
@lightbulb.command(
    "pickupline", "Prints a pick up line."
)
@lightbulb.implements(lightbulb.SlashCommand)
async def main(ctx: lightbulb.Context) -> None:
    await ctx.respond(pickupline())

def pickupline() -> str:
    return get_random_pickup_line()

def get_random_pickup_line() -> str:
    response = requests.get("http://getpickuplines.herokuapp.com/lines/random")
    return response.json()["line"]


def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)