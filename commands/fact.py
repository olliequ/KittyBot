import random, re
import requests
from bs4 import BeautifulSoup
import lightbulb

plugin = lightbulb.Plugin("Fact")
randomFacts = list[str]()


def init():
    misconceptionsURL = "https://en.wikipedia.org/wiki/List_of_common_misconceptions"
    page = requests.get(misconceptionsURL)
    soup = BeautifulSoup(page.content, "html.parser")
    lists = soup.select('.mw-parser-output ul')
    for i in range(13, 79 if len(lists) >= 79 else len(lists)):
        for line in lists[i]:
            if line.text != "\n":
                line = re.sub(r"\[.*?\]", "", line.text)
                randomFacts.append(line)


@plugin.command
@lightbulb.add_cooldown(10, 1, lightbulb.UserBucket)
@lightbulb.command("fact", description="Gives a random fact!")
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def main(ctx: lightbulb.Context) -> None:
    fact = random.choice(randomFacts)
    await ctx.respond(f"{fact}")


def load(bot: lightbulb.BotApp) -> None:
    init()
    bot.add_plugin(plugin)
