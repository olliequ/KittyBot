import os
import hikari, lightbulb
from PIL import Image
import requests
from snark import model
from google.generativeai.generative_models import GenerativeModel
from typing import Final

plugin = lightbulb.Plugin("MemeRater")

MEMES_CHANNEL_ID = os.environ.get("MEME_CHANNEL_ID")

# Make this envs if you want
MEME_RATE_PROMPT: Final[str] = (
    "Rate this meme out of 10, with 10 being the funniest. Rate is solely on how funny a bunch of computer science nerds would find it. ONLY Return an integer."
)
MINIMUM_MEME_RATING_TO_NOT_DELETE: Final[int] = 6
IMG_FILE_EXTENSIONS: Final = ["jpg", "jpeg", "png", "webp"]


async def get_meme_rating(image_url: str, model: GenerativeModel):
    response = model.generate_content(
        contents=[MEME_RATE_PROMPT, Image.open(requests.get(image_url).raw)]
    )
    return response.text


@plugin.listener(hikari.GuildMessageCreateEvent)
async def main(event: hikari.GuildMessageCreateEvent) -> None:
    if event.channel_id == MEMES_CHANNEL_ID:
        # Don't handle messages from bots or without content
        if event.is_bot:
            return
        for attachment in event.message.attachments:
            # removed uncommon formats for testing - don't tell Jimmy plx
            # "tiff",  "bmp", "gif <-- idk if these are supported
            att_ext = attachment.extension
            if att_ext in IMG_FILE_EXTENSIONS:
                image_url = attachment.url
                res = await get_meme_rating(image_url, model)
                if res:
                    try:
                        int_res = int(res)
                        if int_res >= MINIMUM_MEME_RATING_TO_NOT_DELETE:
                            await event.message.add_reaction(emoji="👍")
                            await event.message.add_reaction(emoji="🐱")
                            await event.message.add_reaction(emoji=f":number_{res}:")
                        else:
                            await event.message.respond(
                                f"This meme is garbage 💩💩💩. I rate it {res}/10. Send something better.",
                                user_mentions=True,
                                reply=True,
                            )
                            # meme is shit - delete?
                            # await event.message.delete()
                            return  # just doing first attachment rating response
                    except ValueError:
                        return


def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)
