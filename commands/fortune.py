import os
import re
import random
import lightbulb
from fortune import get_random_fortune

plugin = lightbulb.Plugin("Fortune")


@plugin.command
@lightbulb.command("fortune", "Gives a fortune -- beware!")
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def main(ctx: lightbulb.Context) -> None:
    message = fortune()
    str2 = message.replace("\n", " ")
    new = re.sub(r"(?:(?!\n)\s)+", " ", str2)
    await ctx.respond(new)


def fortune() -> str:
    return get_random_fortune(choose_file())


def choose_file() -> str:
    basedir = os.environ["FORTUNE_DIRECTORY"]
    files = [
        f
        for f in os.listdir(basedir)
        if os.path.isfile(os.path.join(basedir, f)) and re.match("^[^.]+$", f)
    ]
    if "FORTUNE_WHITELIST" in os.environ:
        whitelist = os.environ["FORTUNE_WHITELIST"].split()
        files = filter(lambda f: f in whitelist, files)
    if "FORTUNE_BLACKLIST" in os.environ:
        blacklist = os.environ["FORTUNE_BLACKLIST"].split()
        files = filter(lambda f: f not in blacklist, files)
    return os.path.join(basedir, random.choice(list(files)))


def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)
