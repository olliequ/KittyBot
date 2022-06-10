import random, re
import requests
from bs4 import BeautifulSoup
import lightbulb

plugin = lightbulb.Plugin("Fact")
randomFacts = []

def init():
    misconceptionsURL = "https://en.wikipedia.org/wiki/List_of_common_misconceptions"
    page = requests.get(misconceptionsURL) 
    soup = BeautifulSoup(page.content, "html.parser") 
    results = soup.find(class_="mw-parser-output")
    lists = results.find_all("ul") # Returns an iterable of all lists on the page.
    for i in range(13, 79):
        for line in lists[i]:
            if line != '\n':
                line = re.sub(r"\[.*?\]", "", line.text)
                randomFacts.append(line)

@plugin.command
@lightbulb.add_cooldown(10, 1, lightbulb.UserBucket)
@lightbulb.command("fact", description="Gives a random fact!")
@lightbulb.implements(lightbulb.PrefixCommand)
async def main(ctx: lightbulb.Context) -> None:
    target = ctx.get_guild().get_member(ctx.user)
    fact = random.choice(randomFacts)
    await ctx.respond(f"---> {ctx.author.mention}, did you know this?  :cat:\n\n{fact}", user_mentions=[target, True])

def load(bot: lightbulb.BotApp) -> None:
    init()
    bot.add_plugin(plugin)
