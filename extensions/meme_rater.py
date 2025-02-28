import os
import hikari
import lightbulb
from PIL import Image
import requests
from snark import model
from google.generativeai.generative_models import GenerativeModel
from typing import Final

plugin = lightbulb.Plugin("MemeRater")

MEMES_CHANNEL_ID = os.environ.get("MEME_CHANNEL_ID")

# can be in .env if you prefer
MEME_RATE_PROMPT: Final[str] = (
    "Rate this meme out of 10, with 10 being the funniest. Rate is solely on how funny a bunch of computer science nerds would find it. ONLY Return an integer."
)
MINIMUM_MEME_RATING_TO_NOT_DELETE: Final[int] = 6
DELETE_SHIT: Final[bool] = False
# removed uncommon formats for testing - don't tell Jimmy plx
# "tiff",  "bmp", "gif <-- idk if these are supported
IMG_FILE_EXTENSIONS: Final = {"jpg", "jpeg", "png", "webp"}


async def get_meme_rating(image_url: str, model: GenerativeModel):
    response = model.generate_content(
        contents=[MEME_RATE_PROMPT, Image.open(requests.get(image_url).raw)]
    )
    return response.text


@plugin.listener(hikari.GuildMessageCreateEvent)
async def main(event: hikari.GuildMessageCreateEvent) -> None:
    if event.channel_id != MEMES_CHANNEL_ID:
        return

    ratings = []
    for attachment in event.message.attachments:
        att_ext = attachment.extension
        if att_ext not in IMG_FILE_EXTENSIONS:
            continue
        image_url = attachment.url
        rating = await get_meme_rating(image_url, model)
        try:
            ratings.append(int(rating))
        except ValueError:
            continue
    if not ratings:
        return

    avg_rating = min(max(0, sum(ratings) // len(ratings)), 10)

    await event.message.add_reaction(emoji=f":number_{avg_rating}:")
    await event.message.add_reaction(emoji="🐱")

    if avg_rating >= MINIMUM_MEME_RATING_TO_NOT_DELETE:
        await event.message.add_reaction(emoji="👍")
    else:
        await event.message.respond(
            f"This meme is garbage 💩💩💩. I rate it {avg_rating}/10. Send something better.",
            user_mentions=True,
            reply=True,
        )
        if DELETE_SHIT:
            await event.message.delete()
        else:
            await event.message.add_reaction(emoji="💩")
            await event.message.add_reaction(emoji=f":number_{avg_rating}:")


def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)
