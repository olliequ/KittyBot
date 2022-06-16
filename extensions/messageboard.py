import re
from datetime import datetime
from itertools import chain
from emoji import emoji_list, replace_emoji
import hikari, lightbulb
import db
import numpy as np
import matplotlib.pyplot as plt

plugin = lightbulb.Plugin("MessageBoard.")

async def show_message_stats(ctx: lightbulb.Context, plot_type) -> None:
    guild = ctx.get_guild()
    cursor = db.cursor()
    cursor.execute("""
        SELECT user, count FROM message_counts
        ORDER BY count DESC
        LIMIT 10""")
    data = cursor.fetchall()
    if len(data) == 0:
        await ctx.respond("No one has said anything. How bizarre.")
        return
    max_messages = data[0][1]
    max_messages_width = len(str(max_messages))
    max_name_length = 0
    users_counts = []

    # Luke's native horizontal block graph.
    if plot_type == 1:
        print("Luke's graph requested.")
        for (user_id, message_count) in data:
            user = guild.get_member(user_id)
            if not user:
                display_name = str(user_id)
            else:
                display_name = replace_emoji(user.display_name, '')
            max_name_length = max(max_name_length, len(display_name))
            users_counts.append((display_name, message_count))
        MAX_BAR_LENGTH = 30
        SLICES_PER_CHAR = 8
        BLOCK_CODEPOINT = 0x2588
        message = ['**Messages Tally** :cat:```']
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
        print("Lightmode graph requested.")
        for (user_id, message_count) in data:
            user = guild.get_member(user_id)
            if not user:
                display_name = str(user_id)
            else:
                display_name = user.display_name
            max_name_length = max(max_name_length, len(display_name))
            users_counts.append((display_name, message_count))
        users = [pair[0] for pair in users_counts]
        counts = [pair[1] for pair in users_counts]
        print(f'{users}\n{counts}')

        fig, ax = plt.subplots(figsize=(11,5))
        bars = ax.bar(users, counts, color=['#C9B037', '#D7D7D7', '#6A3805', '#9fdbed', '#9fdbed', '#9fdbed', '#9fdbed', '#9fdbed', '#9fdbed', '#9fdbed'], edgecolor='black')
        ax.bar_label(bars)
        # ax.set_xlabel('Members', labelpad=10, color='#333333', fontsize='12')
        ax.set_ylabel('Total Messages', labelpad=15, color='#333333', fontsize='12')
        ax.set_title('Messages Tally!', pad=15, color='#333333', weight='bold', fontsize='15')
        ax.set_facecolor('#f5f5f5')
        plt.yticks(fontsize=8)
        plt.xticks(fontsize=(95/max_name_length))

        from io import BytesIO
        buffer = BytesIO()
        plt.savefig(buffer, format='png')
        await ctx.respond(hikari.Bytes(buffer.getvalue(), 'leaderboard.png'))

    # Light mode graph.
    elif plot_type == 3:
        print("Darkmode graph requested.")
        """
        DuckDivinity write your darkmode code here!
        """
        await ctx.message.respond("Message.")

@plugin.command
@lightbulb.add_cooldown(10, 1, lightbulb.UserBucket)
@lightbulb.option("type", "Which type of graph to show!", choices=["lightmode", "darkmode", "native"], required=False)
@lightbulb.command("messageboard", "Display top 10 'messagers'.")
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def main(ctx: lightbulb.Context) -> None:
    if ctx.options.type == "native":
        await show_message_stats(ctx, 1)
    elif ctx.options.type == "darkmode":
        await show_message_stats(ctx, 3)
    else:
        await show_message_stats(ctx, 2)
    
def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)