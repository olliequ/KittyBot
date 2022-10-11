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
from PIL import Image

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
        "select emoji, count from emoji_counts where user = ?", (user_id,)
    ).fetchall()

    # code credit: https://amueller.github.io/word_cloud/auto_examples/emoji.html

    # get data directory (using getcwd() is needed to support running example in generated IPython notebook)
    d = os.path.dirname(__file__) if "__file__" in locals() else os.getcwd()
    imp_mask = np.array(Image.open(os.path.join(d, "assets", "imp_map_smaller.png")))

    if len(counts) == 0:
        await ctx.respond(
            f"{ctx.options.target.display_name} has not used any unicode emoji."
        )
        return

    # Generate a word cloud image
    # The Symbola font includes most emoji
    font_path = os.path.join(d, "fonts", "NotoEmoji-Regular.ttf")
    wc = WordCloud(
        font_path=font_path,
        background_color="#37393E",  # the colour of discord's dark theme background
        mask=imp_mask,
    ).generate_from_frequencies(dict(counts))

    # Display the generated image:
    # the matplotlib way:
    plt.imshow(wc)
    plt.axis("off")

    buffer = BytesIO()
    plt.savefig(buffer, format="png", bbox_inches="tight", pad_inches=0)
    await ctx.respond(hikari.Bytes(buffer.getvalue(), "emojicloud.png"))


def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)
