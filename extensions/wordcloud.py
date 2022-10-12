import re
from datetime import datetime
from itertools import chain
from emoji import emoji_list, replace_emoji
import hikari, lightbulb
import numpy as np
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
import os
from wordcloud import WordCloud
import db
import io
from io import BytesIO
import string
from PIL import Image, ImageFont, ImageDraw, ImageChops, ImageOps

plugin = lightbulb.Plugin("WordCloud")


@plugin.command
@lightbulb.add_cooldown(10, 1, lightbulb.UserBucket)
@lightbulb.option(
    "target", "The member to get an emojicloud for.", hikari.User, required=True
)
@lightbulb.command("wordcloud", "Get an emojicloud for a user!")
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def main(ctx: lightbulb.Context) -> None:

    cursor = db.cursor()

    user_id = ctx.options.target.id
    counts = cursor.execute(
        "select emoji, count from emoji_counts where user = ? and emoji not like '<:%' order by count desc",
        (user_id,),
    ).fetchall()

    if len(counts) == 0:
        await ctx.respond(
            f"{ctx.options.target.display_name} has not used any unicode emoji."
        )
        return

    top_emoji = counts[0]

    d = os.path.dirname(__file__) if "__file__" in locals() else os.getcwd()

    # code credit https://gist.github.com/pbojinov/7f680445d50a9bd5a421

    # calculate mask if it doesn't exist
    if not os.path.isfile(os.path.join(d, "assets", f"{db.md5sum(top_emoji[0])}.png")):
        W, H = (512, 400)  # image size
        txt = top_emoji[0]  # text to render
        background = (255, 255, 255)  # white
        fontsize = 350
        font = ImageFont.truetype(
            os.path.join(d, "fonts", "NotoEmoji-Regular.ttf"), fontsize
        )

        image = Image.new("RGB", (W, H), background)

        draw = ImageDraw.Draw(image)
        # w, h = draw.textsize(txt) # not that accurate in getting font size
        w, h = font.getsize(txt)
        draw.text(((W - w) / 2, (H - h) / 2), txt, fill="black", font=font)

        # flood fill to the edges of an emoji so we can count the black and white pixels
        ImageDraw.floodfill(image, xy=(0, 0), value=(255, 0, 0), thresh=300)

        # count our friendly black and white pixel ratio
        black, white = 0, 0
        for pixel in image.getdata():
            match (pixel):
                case ((255, 255, 255)):
                    white += 1
                case ((0, 0, 0)):
                    black += 1

        if black < white:
            # then the 'white' area is probably the majority of the emoji
            # so invert the mask so the white area becomes black and thus the draw area for
            # the word cloud
            # remove dithering by conversion to pure b&w
            fn = lambda x: 255 if x > 200 else 0
            image = image.convert("L").point(fn, mode="1")
            image = ImageOps.invert(image)
            image = image.convert("RGB")

        # refill the red away from the edges so it doesn't become a word cloud drawing area

        ImageDraw.floodfill(image, xy=(0, 0), value=(255, 255, 255), thresh=0)

        save_location = os.getcwd()
        image.save(save_location + f"/assets/{db.md5sum(top_emoji[0])}.png")

    # code credit: https://amueller.github.io/word_cloud/auto_examples/emoji.html

    img_mask = np.array(
        Image.open(os.path.join(d, "assets", f"{db.md5sum(top_emoji[0])}.png"))
    )

    # Generate a word cloud image
    # The Symbola font includes most emoji
    font_path = os.path.join(d, "fonts", "NotoEmoji-Regular.ttf")
    wc = WordCloud(
        font_path=font_path,
        background_color="#37393E",  # the colour of discord's dark theme background
        mask=img_mask,
        contour_width=3,
        contour_color="steelblue",
    ).generate_from_frequencies(dict(counts))

    # Display the generated image:
    # the matplotlib way:
    plt.imshow(wc, interpolation="none")
    plt.axis("off")

    buffer = BytesIO()
    plt.savefig(buffer, format="png", bbox_inches="tight", pad_inches=0)
    await ctx.respond(hikari.Bytes(buffer.getvalue(), "emojicloud.png"))


def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)