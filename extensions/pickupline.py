import lightbulb
import requests

plugin = lightbulb.Plugin("Pickup Line")


@plugin.command
@lightbulb.option("type", "Which type of lines to show", choices=["pickup", "breakup"], required=False,
                  default="pickup")
@lightbulb.command(
    "pickupline", "Print a pick up / break up line."
)
@lightbulb.implements(lightbulb.SlashCommand)
async def main(ctx: lightbulb.Context) -> None:
    await ctx.respond(get_random_pickup_line(ctx.options.type))


def get_random_pickup_line(type) -> str:
    response = requests.get(f"https://api.jcwyt.com/{type}")
    return response.text


def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)
