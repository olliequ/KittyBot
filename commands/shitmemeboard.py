from emoji import replace_emoji
import hikari, lightbulb
import commons.db as db
import matplotlib.font_manager as fm
import matplotlib.image as image
import matplotlib.pyplot as plt
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from io import BytesIO
import toolbox
from .messageboard import graph_shit

plugin = lightbulb.Plugin("Shitmemeboard.")


def get_shitmeme_data(set_num):
    cursor = db.cursor()
    cursor.execute(
        """
        SELECT user, count FROM shit_meme_deletes
        ORDER BY count DESC
        LIMIT {},{}""".format(
            set_num * 10, 10
        )
    )
    data = cursor.fetchall()
    return data


async def show_message_stats(ctx: lightbulb.Context, plot_type, set_num) -> None:
    data = get_shitmeme_data(set_num)
    await graph_shit(ctx, plot_type, set_num, data)


@plugin.command
@lightbulb.add_cooldown(10, 1, lightbulb.UserBucket)
@lightbulb.option(
    "type",
    "Which type of graph to show!",
    choices=["lightmode", "darkmode", "native"],
    required=False,
)
@lightbulb.option(
    "set",
    "Which set of ranks to show (0 is 1-10, 1 is 11-20, 2 is 21-30...)!",
    type=int,
    required=False,
    default=0,
)
@lightbulb.command(
    "shitmemeboard", "Displays Jimmy and 9 other users who had the most memes deleted."
)
@lightbulb.implements(lightbulb.SlashCommand)
async def main(ctx: lightbulb.Context) -> None:
    if ctx.options.type == "native":
        await show_message_stats(ctx, 1, ctx.options.set)
    elif ctx.options.type == "lightmode":
        await show_message_stats(ctx, 2, ctx.options.set)
    else:
        await show_message_stats(ctx, 3, ctx.options.set)


def load(bot: lightbulb.BotApp) -> None:
    fm.fontManager.addfont("fonts/NotoEmoji-Regular.ttf")
    plt.rcParams["font.family"].append("Noto Emoji")
    bot.add_plugin(plugin)
