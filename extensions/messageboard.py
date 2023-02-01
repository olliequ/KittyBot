import re
from datetime import datetime
from itertools import chain
from emoji import emoji_list, replace_emoji
import hikari, lightbulb
import db
import numpy as np
import matplotlib.font_manager as fm
import matplotlib.image as image
import matplotlib.pyplot as plt
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from io import BytesIO
import toolbox

plugin = lightbulb.Plugin("MessageBoard.")


async def show_message_stats(ctx: lightbulb.Context, plot_type, set_num) -> None:
    guild = ctx.get_guild()
    cursor = db.cursor()
    cursor.execute("""
        SELECT user, count FROM message_counts
        ORDER BY count DESC
        LIMIT {},{}""".format(set_num * 10, 10))
    data = cursor.fetchall()
    if len(data) == 0:
        await ctx.respond("The set you have requested is out of bounds <:catthink:985820328603299871>")
        return
    max_messages = data[0][1]
    max_messages_width = len(str(max_messages))
    max_name_length = 0
    users_counts = []

    default_colors = ['#FFD700', '#C0C0C0', '#CD7F32', '#00ffff', '#ff2525', '#ffe53b', '#fdecef', '#e55646',
                      '#7756a7', '#28B463']

    # Extracted redundant code outside the condition
    ghost_count = 0
    for i, (user_id, message_count) in enumerate(data):
        user = guild.get_member(user_id)
        if not user:
            display_name = f"Ghost{'!' * (ghost_count + 1)}"
            color = default_colors[i]
            ghost_count += 1
        else:
            display_name = replace_emoji(user.display_name, '')
            # Toolbox contains the utility function to get color
            color = toolbox.members.get_member_color(user).hex_code
            if not color:
                color = default_colors[i]
        max_name_length = max(max_name_length, len(display_name))
        users_counts.append((display_name, message_count, color))

    # Luke's native horizontal block graph.
    if plot_type == 1:
        MAX_BAR_LENGTH = 30
        SLICES_PER_CHAR = 8
        BLOCK_CODEPOINT = 0x2588

        message = ['**Messages Tally from {} to {}** :cat:```'.format(set_num * 10 + 1, set_num * 10 + 10)]
        for (name, count) in users_counts:
            line = f'{name.rjust(max_name_length)} : {str(count).rjust(max_messages_width)} '
            slices = int((MAX_BAR_LENGTH * SLICES_PER_CHAR) * (count / max_messages))
            bar = chr(BLOCK_CODEPOINT) * (slices // SLICES_PER_CHAR)
            if slices % SLICES_PER_CHAR > 0:
                bar += chr(BLOCK_CODEPOINT + SLICES_PER_CHAR - (slices % SLICES_PER_CHAR))
            message.append(line + bar)
        message.append('```')
        await ctx.respond('\n'.join(message))

    # Light mode graph.
    elif plot_type == 2:
        users = [pair[0] for pair in users_counts]
        counts = [pair[1] for pair in users_counts]

        fig, ax = plt.subplots(figsize=(11, 5))
        bars = ax.bar(users, counts,
                      color=['#C9B037', '#D7D7D7', '#6A3805', '#9fdbed', '#9fdbed', '#9fdbed', '#9fdbed', '#9fdbed',
                             '#9fdbed', '#9fdbed'], edgecolor='black')
        ax.bar_label(bars)
        # ax.set_xlabel('Members', labelpad=10, color='#333333', fontsize='12')
        ax.set_ylabel('Total Messages', labelpad=15, color='#333333', fontsize='12')
        ax.set_title('Messages Tally! from {} to {}'.format(set_num * 10 + 1, set_num * 10 + 10), pad=15,
                     color='#333333', weight='bold', fontsize='15')
        ax.set_facecolor('#f5f5f5')
        plt.yticks(fontsize=8)
        plt.xticks(fontsize=(95 / max_name_length))

        buffer = BytesIO()
        plt.savefig(buffer, format='png')
        await ctx.respond(hikari.Bytes(buffer.getvalue(), 'leaderboard.png'))
        plt.close()

    # Dark mode graph.
    elif plot_type == 3:
        users = [pair[0] for pair in users_counts]
        counts = [pair[1] for pair in users_counts]
        colors = [pair[2] for pair in users_counts]

        fig, ax = plt.subplots(figsize=(11, 5))
        bars = ax.bar(users, counts, color=colors)
        ax.bar_label(bars, color='#fff')
        # ax.set_xlabel('Members', labelpad=10, color='#333333', fontsize='12')
        ax.set_ylabel(r'Total Messages', labelpad=15, color='#e6e7e7', fontsize='12')
        ax.set_title('Messages Tally! (from {} to {})'.format(set_num * 10 + 1, set_num * 10 + 10), pad=15,
                     color='#e6e7e7', weight='bold', fontsize='15')

        # Set Background Colour to default Discord Background
        ax.set_facecolor('#36393f')
        fig.patch.set_facecolor('#36393f')

        # Set the color of borders
        ax.spines['bottom'].set_color('#7289da')
        ax.spines['top'].set_color('#7289da')
        ax.spines['left'].set_color('#7289da')
        ax.spines['right'].set_color('#7289da')

        # Set color for ticks
        ax.tick_params(axis='x', colors='#fff')
        ax.tick_params(axis='y', colors='#fff')

        plt.yticks(fontsize=8)
        plt.xticks(fontsize=(95 / max_name_length))

        # Crown Images from Flaticon.com :bulbylove:
        crowns = ["images/gold_crown.png", "images/silver_crown.png", "images/bronze_crown.png", "images/potato.png"]
        crown_images = list(map(image.imread, crowns))

        def offset_image(coord, ax):
            if coord >= 4:
                # No Crown for More than rank 4
                return
            img = crown_images[coord]
            im = OffsetImage(img, zoom=0.05)  # Zoom Controls the Size of the Crown
            im.image.axes = ax

            # xybox controls the position of crown. Greater the value, lower the crown
            ab = AnnotationBbox(im, (coord, 0), xybox=(0., -27.), frameon=False,
                                xycoords='data', boxcoords="offset points", pad=0)

            ax.add_artist(ab)

        if set_num == 0:
            for i, c in enumerate(users):
                offset_image(i, ax)

        buffer = BytesIO()
        plt.savefig(buffer, format='png')
        await ctx.respond(hikari.Bytes(buffer.getvalue(), 'leaderboard.png'))
        plt.close()


@plugin.command
@lightbulb.add_cooldown(10, 1, lightbulb.UserBucket)
@lightbulb.option("type", "Which type of graph to show!", choices=["lightmode", "darkmode", "native"], required=False)
@lightbulb.option("set", "Which set of ranks to show (0 is 1-10, 1 is 11-20, 2 is 21-30...)!", type=int, required=False,
                  default=0)
@lightbulb.command("messageboard", "Displays the top 10 'messagers' of all-time.")
@lightbulb.implements(lightbulb.SlashCommand)
async def main(ctx: lightbulb.Context) -> None:
    if ctx.options.type == "native":
        await show_message_stats(ctx, 1, ctx.options.set)
    elif ctx.options.type == "lightmode":
        await show_message_stats(ctx, 2, ctx.options.set)
    else:
        await show_message_stats(ctx, 3, ctx.options.set)


def load(bot: lightbulb.BotApp) -> None:
    fm.fontManager.addfont('fonts/NotoEmoji-Regular.ttf')
    plt.rcParams['font.family'].append('Noto Emoji')
    bot.add_plugin(plugin)
