import os
from operator import itemgetter
from random import Random

import hikari
import lightbulb
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from matplotlib import cm
from pilmoji import Pilmoji  # Used to generate decent Unicode emoji

import db
import emoji_cache

plugin = lightbulb.Plugin("EmojiCloud")


@plugin.command
@lightbulb.add_cooldown(10, 1, lightbulb.UserBucket)
@lightbulb.option(
    "target", "The member to get an emojicloud for.", hikari.User, required=True
)
@lightbulb.option(
    "max_emojis", "The number of emojis to include in EmojiCloud", type=int, required=False, default=20
)
@lightbulb.command("emojicloud", "Get an emojicloud for a user!",
                   auto_defer=True)  # auto_defer to allowed delay in uploading
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def main(ctx: lightbulb.Context) -> None:
    # Need some Initial response to safely defer so why not show whose emojicloud it is
    await ctx.respond(f"*Generating EmojiCloud for **{ctx.options.target.display_name}**, gimme a couple seconds:*")
    cursor = db.cursor()

    user_id = ctx.options.target.id
    max_emojis = ctx.options.max_emojis

    counts = cursor.execute(
        "select emoji, count from emoji_counts where user = ? order by count desc limit ?",
        (user_id, max_emojis),
    ).fetchall()

    # Cache all used emojis to use later. Remove Deleted Emojis from the data
    counts = [i for i in counts if await emoji_cache.download_emoji(i[0], ctx.bot) != "Not Found"]

    if len(counts) == 0:
        await ctx.respond(
            f"{ctx.options.target.display_name} has not used any emoji."
        )
        return

    all_thumbnails: list[(Image.Image, str)] = []  # List of Image and type (Custom or Unicode)
    max_num_frames = 1
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # 150 max size from trial-error. Can change
    listofimages = generate_from_frequencies(counts, max_words=max_emojis, max_font_size=150)
    for p in listofimages:
        if p[3][0] == "<":  # Custom Emoji have "<" in the beginning
            thumbnail = Image.open(os.path.join(script_dir, "..", emoji_cache.get_file_name_if_cached(p[3])))
            max_num_frames = max(max_num_frames, thumbnail.n_frames)
            all_thumbnails.append((thumbnail, "custom"))
        else:  # Regular Unicode Emoji
            e_code = p[3].strip()
            # Using NotoEmoji to generate as estimated size for the emoji
            font = ImageFont.truetype('fonts/NotoEmoji-Regular.ttf', p[2])

            thumbnail = Image.new('RGB', get_text_dimensions(e_code, font), '#37393E')

            with Pilmoji(thumbnail) as pilmoji:
                pilmoji.text((10, 10), e_code, (0, 0, 0), font)
            all_thumbnails.append((thumbnail, "unicode"))

    frames = []
    for fi in range(max_num_frames):
        new_im = Image.new('RGB', (512, 512), '#37393E')
        for j in range(len(listofimages)):
            p = listofimages[j] # Image with it's dimensions // rgb?
            ti = all_thumbnails[j] # the actual image and whether it's custom or unicode.
            width, height = ti[0].size
            width_factor = height/width # Over 1 if longer than taller
            if ti[1] == "custom":
                ti[0].seek(fi % ti[0].n_frames)
            resized_img = ti[0].resize((p[2], int(p[2]*width_factor))).convert('RGBA')
            new_im.paste(resized_img, (p[0], p[1]), resized_img.convert('RGBA'))
            frames.append(new_im)

    # loop=0 means infinite looping | duration=0.02 means 50fps, the default for discord (Source: Trust me bro)
    frames[0].save('assets/output.gif', save_all=True, append_images=frames, loop=0, duration=0.02)

    await ctx.respond(hikari.File('assets/output.gif'))
    # await ctx.respond(hikari.Bytes(BytesIO(open("output.gif", "rb").read()).getvalue(), "emojicloud.png"))


def get_text_dimensions(text_string, font):
    """

    """
    ascent, descent = font.getmetrics()

    text_width = font.getmask(text_string).getbbox()[2]
    text_height = font.getmask(text_string).getbbox()[3] + descent
    return text_width, text_height


width, height = (512, 512)
relative_scaling = 0.5
prefer_horizontal = 0.2
margin = 2
min_image_size = 10
random_state = Random()


def generate_from_frequencies(layout, max_words, max_font_size=None):  # noqa: C901
    """Create a layout plan from words and frequencies.
    Throughout this function, font_size = image_size :P
    Parameters
    ----------
    layout : list of tuple(emoji,frequency)
    max_font_size : int
        Use this font-size instead of max_font_size
    Returns
    -------
    output : list of tuple (size, x-coord, y-coord, emoji)
    """
    frequencies = dict(layout)

    # make sure frequencies are sorted and normalized
    frequencies = sorted(frequencies.items(), key=itemgetter(1), reverse=True)
    if len(frequencies) <= 0:
        raise ValueError("We need at least 1 word to plot a word cloud, "
                         "got %d." % len(frequencies))
    frequencies = frequencies[:max_words]

    # largest entry will be 1
    max_frequency = float(frequencies[0][1])

    frequencies = [(word, freq / max_frequency)
                   for word, freq in frequencies]

    occupancy = IntegralOccupancyMap(width, height, None)

    # create greyscale image
    img_grey = Image.new("L", (height, width))
    draw = ImageDraw.Draw(img_grey)

    last_freq = 1.

    if max_font_size is None:
        # figure out a good font size by trying to draw with
        # just the first two words
        if len(frequencies) == 1:
            # we only have one word. We make it big!
            font_size = height
        else:
            generate_from_frequencies(dict(frequencies[:2]),
                                      max_font_size=height, max_words=max_words)
            # find font sizes
            sizes = [x[1] for x in layout]
            try:
                font_size = int(2 * sizes[0] * sizes[1]
                                / (sizes[0] + sizes[1]))
            # quick fix for if layout_ contains less than 2 values
            # on very small images it can be empty
            except IndexError:
                try:
                    font_size = sizes[0]
                except IndexError:
                    raise ValueError(
                        "Couldn't find space to draw. Either the Canvas size"
                        " is too small or too much of the image is masked "
                        "out.")
    else:
        font_size = max_font_size

    output = []
    # start drawing grey image
    for word, freq in frequencies:
        if freq == 0:
            continue
        # select the font size
        rs = relative_scaling
        if rs != 0:
            font_size = int(round((rs * (freq / float(last_freq))
                                   + (1 - rs)) * font_size))
        while True:
            # try to find a position

            # get size of resulting emoji
            box_size = [font_size, font_size]
            # find possible places using integral image:
            result = occupancy.sample_position(box_size[1] + margin,
                                               box_size[0] + margin,
                                               random_state)
            if result is not None or font_size < min_image_size:
                # either we found a place or font-size went too small
                break
            # if we didn't find a place, make font smaller
            font_size -= 1

        if font_size < min_image_size:
            # we were unable to draw anymore
            break

        x, y = np.array(result) + margin // 2
        draw.rectangle((y, x, y + font_size, x + font_size), fill="white")

        # img_grey.show()
        output.append((x, y, font_size, word))
        img_array = np.asarray(img_grey)

        # print(occupancy)
        # recompute bottom right
        # the order of the cumsum's is important for speed ?!
        occupancy.update(img_array, x, y)
        last_freq = freq

    # print(output)
    return output


class IntegralOccupancyMap(object):
    def __init__(self, height, width, mask):
        self.height = height
        self.width = width
        if mask is not None:
            # the order of the cumsum's is important for speed ?!
            self.integral = np.cumsum(np.cumsum(255 * mask, axis=1),
                                      axis=0).astype(np.uint32)
        else:
            self.integral = np.zeros((height, width), dtype=np.uint32)

    def sample_position(self, size_x, size_y, random_state):
        return query_integral_image(self.integral, size_x, size_y,
                                    random_state)

    def update(self, img_array, pos_x, pos_y):
        partial_integral = np.cumsum(np.cumsum(img_array[pos_x:, pos_y:],
                                               axis=1), axis=0)
        # paste recomputed part into old image
        # if x or y is zero it is a bit annoying
        if pos_x > 0:
            if pos_y > 0:
                partial_integral += (self.integral[pos_x - 1, pos_y:]
                                     - self.integral[pos_x - 1, pos_y - 1])
            else:
                partial_integral += self.integral[pos_x - 1, pos_y:]
        if pos_y > 0:
            partial_integral += self.integral[pos_x:, pos_y - 1][:, np.newaxis]

        self.integral[pos_x:, pos_y:] = partial_integral

    def show(self):
        im = Image.fromarray(np.uint8(cm.gist_earth(self.integral) * 255))
        im.show()


def query_integral_image(integral_image, size_x, size_y, random_state):
    x = integral_image.shape[0]
    y = integral_image.shape[1]
    hits = 0

    # count how many possible locations
    for i in range(x - size_x):
        for j in range(y - size_y):
            area = integral_image[i, j] + integral_image[i + size_x, j + size_y]
            area -= integral_image[i + size_x, j] + integral_image[i, j + size_y]
            if not area:
                hits += 1
    if not hits:
        # no room left
        return None
    # pick a location at random
    goal = random_state.randint(0, hits)
    hits = 0
    for i in range(x - size_x):
        for j in range(y - size_y):
            area = integral_image[i, j] + integral_image[i + size_x, j + size_y]
            area -= integral_image[i + size_x, j] + integral_image[i, j + size_y]
            if not area:
                hits += 1
                if hits == goal:
                    return i, j


def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)
