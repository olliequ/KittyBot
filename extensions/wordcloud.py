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

    text = ""
    for emoji, count in counts:
        text += emoji * count

    # the regex used to detect words is a combination of normal words, ascii art, and emojis
    # 2+ consecutive letters (also include apostrophes), e.x It's
    normal_word = r"(?:\w[\w']+)"
    # 2+ consecutive punctuations, e.x. :)
    ascii_art = r"(?:[{punctuation}][{punctuation}]+)".format(
        punctuation=string.punctuation
    )
    # a single character that is not alpha_numeric or other ascii printable
    emoji = r"(?:[^\s])(?<![\w{ascii_printable}])".format(
        ascii_printable=string.printable
    )
    regexp = r"{normal_word}|{ascii_art}|{emoji}".format(
        normal_word=normal_word, ascii_art=ascii_art, emoji=emoji
    )

    # Generate a word cloud image
    # The Symbola font includes most emoji
    font_path = os.path.join(d, "fonts", "NotoEmoji-Regular.ttf")
    wc = WordCloud(
        font_path=font_path,
        regexp=regexp,
        background_color="#37393E",  # the colour of discord's dark theme background
        mask=imp_mask,
        collocations=False,
    ).generate(text)

    # Display the generated image:
    # the matplotlib way:
    plt.imshow(wc)
    plt.axis("off")

    buffer = BytesIO()
    plt.savefig(buffer, format="png", bbox_inches="tight", pad_inches=0)
    await ctx.respond(hikari.Bytes(buffer.getvalue(), "emojicloud.png"))


def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)
