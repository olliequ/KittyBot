import requests
import langcodes
import lightbulb

plugin = lightbulb.Plugin("Translate")


@plugin.command
@lightbulb.option("text", "Text to translate", required=True)
@lightbulb.option(
    "language",
    "Language to translate to (default English)",
    required=False,
    default="en",
)
@lightbulb.command("translate", "Translate text to and from English.")
@lightbulb.implements(lightbulb.SlashCommand)
async def main(ctx: lightbulb.Context) -> None:
    if langcodes.tag_is_valid(ctx.options.language):
        lang = ctx.options.language
    else:
        try:
            lang = langcodes.find(ctx.options.language)
        except LookupError:
            await ctx.respond("Unknown target language")
            return
    url = "https://translate-service.scratch.mit.edu/translate"
    response = requests.get(url, params={"language": lang, "text": ctx.options.text})
    if response.status_code != 200:
        await ctx.respond("Translation error")
    else:
        await ctx.respond(response.json()["result"])


def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)
