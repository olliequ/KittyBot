"""
Displays a graph of meme ratings for a user, grouped by day.
"""

import commons.db as db
import hikari
import lightbulb
import matplotlib.pyplot as plt
from io import BytesIO
import pandas as pd
import datetime

plugin = lightbulb.Plugin("MemeStats")


@plugin.command
@lightbulb.add_cooldown(10, 1, lightbulb.UserBucket)
# todo: expand this


@lightbulb.option(
    "period", "time period.", choices=["month", "year"], default="month", required=False
)
@lightbulb.option(
    "target", "The member to roast (or not?).", hikari.User, required=False
)
@lightbulb.command(
    "memestats", "See the aggregated server or someone's average meme rating over time"
)
@lightbulb.implements(
    lightbulb.PrefixCommand, lightbulb.SlashCommand, lightbulb.UserCommand
)
async def main(ctx: lightbulb.Context | lightbulb.UserContext):
    guild = ctx.get_guild()
    cursor = db.cursor()
    calculate_for_server = True

    target_user = getattr(ctx.options, "target", ctx.author)

    if target_user and guild:
        user = guild.get_member(target_user.id)
        calculate_for_server = False

    time_period = getattr(ctx.options, "period", "month")

    time_period_param = "month" if time_period == "month" else "year"
    # server time UTC offset
    utcoffset_seconds = int(
        datetime.datetime.now().astimezone().tzinfo.utcoffset(None).total_seconds()
    )

    if not calculate_for_server:
        data = cursor.execute(
            f"""
            select 
                strftime('%Y-%m-%d', datetime(time_sent, '{utcoffset_seconds} seconds')) as time_period,
                avg(meme_score) as avg_meme_score
            from
                meme_stats
            where 
                user = ? and time_sent >= date('now', '{-1 * utcoffset_seconds} seconds', '-1 {time_period_param}')
            group by
                time_period
        """,
            (target_user.id,),
        ).fetchall()
    else:
        data = cursor.execute(
            f"""
            select 
                strftime('%Y-%m-%d', datetime(time_sent, '{utcoffset_seconds} seconds')) as time_period,
                avg(meme_score) as avg_meme_score
            from
                meme_stats
            where 
                time_sent >= date('now', '{-1 * utcoffset_seconds} seconds', '-1 {time_period_param}')
            group by
                time_period
        """,
            (),
        ).fetchall()

    if not data:
        await ctx.respond(
            f"Looks like {(user.display_name or 'User') if not calculate_for_server else 'the server'} hasn't had any of their memes rated yet. 10/10 for them!"
        )
        return

    df = pd.DataFrame(data, columns=["time_period", "avg_meme_score"])
    df["time_period"] = pd.to_datetime(df["time_period"])
    df.set_index("time_period", inplace=True)

    # Create a complete date range and reindex.
    df = df.asfreq("d", fill_value=None)
    # use a simple rolling average to do some smoothing which is perhaps aesthetically pleasant
    df["rolling_avg_meme_score"] = (
        df["avg_meme_score"].rolling(window=7, min_periods=1).mean()
    )

    # graphic plot thingy
    buffer = BytesIO()
    with plt.style.context("fivethirtyeight"):
        plt.figure(figsize=(10, 6))
        plt.plot(
            df.index,
            df["avg_meme_score"],
            marker="o",
            color="#FF6F61",
            linewidth=1,
            markersize=8,
        )
        plt.plot(
            df.index,
            df["rolling_avg_meme_score"],
            linestyle="--",
            color="#cccccc",
            linewidth=1,
        )
        plt.plot
        plt.xlabel("Days", fontsize=12)
        plt.ylabel("Average Meme Score", fontsize=12)
        display_name = (
            "server" if calculate_for_server else user.display_name if user else None
        )
        plt.title(
            f"Meme Scores Over Time ({time_period_param}) for {display_name}",
            fontsize=16,
        )
        plt.xticks(fontsize=8)
        plt.yticks(fontsize=12)
        plt.ylim(
            bottom=-0.5, top=max(10, df["avg_meme_score"].max()) + 0.5
        )  # Start y-axis at 0
        plt.grid(False)
        plt.tight_layout()
        plt.savefig(buffer, format="png", dpi=300)
        plt.close()

        flags = hikari.UNDEFINED
        if isinstance(ctx, lightbulb.UserContext):
            flags = hikari.MessageFlag.EPHEMERAL
        await ctx.respond(
            hikari.Bytes(buffer.getvalue(), "meme_score_results.png"), flags=flags
        )


def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)
