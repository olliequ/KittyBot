"""
Displays a graph of meme ratings for a user, grouped by day.
Todo: make day/hour/week/month/year/decade/century/millennium whatever a parameter.
"""
import db
import hikari
import lightbulb
import matplotlib.font_manager as fm
import matplotlib.image as image
import matplotlib.pyplot as plt
from io import BytesIO
import pandas as pd

plugin = lightbulb.Plugin("MemeStats")

@plugin.command
@lightbulb.add_cooldown(10, 1, lightbulb.UserBucket)
@lightbulb.option("target", "The member to roast (or not?).", hikari.User, required=True)
# todo: expand this
@lightbulb.option("period", "time period.",  choices=["month", "year"], default="month", required=False)
@lightbulb.command("memestats", "See someone's average meme rating over time")
@lightbulb.implements(lightbulb.PrefixCommand,lightbulb.SlashCommand)
async def main(ctx: lightbulb.Context) -> None:
    guild = ctx.get_guild()
    cursor = db.cursor()
    user_id = ctx.options.target.id
    user = guild.get_member(user_id)
    time_period = ctx.options.period

    # todo: add a limit or aggregation of greater time periods or whatever
    # todo: get someone else to do this
    time_period_sql_param = "month" if time_period == "month" else "year"
    data = cursor.execute(f"""
        select strftime('%Y-%m-%d', datetime(time_sent, '+10 hours')) as time_period,
            AVG(meme_score) as avg_meme_score
        from meme_stats
        where user = ? and time_sent >= date('now', '-1 {time_period_sql_param}')
        group BY user, time_period
    """, (user_id,)).fetchall()

    if not data:
        return await ctx.respond(f"Looks like {user.display_name} hasn't had any of their memes rated yet. 10/10 for them!")
    
    # Convert SQLite query result into a DataFrame.
    # random commands found by a combination of chatgpt and google that seem to work
    df = pd.DataFrame(data, columns=["time_period", "avg_meme_score"])
    df["time_period"] = pd.to_datetime(df["time_period"])
    df.set_index("time_period", inplace=True)
    
    # Create a complete date range and reindex.
    df = df.asfreq("d", fill_value=None)
    df["avg_meme_score"] = df.rolling(min_periods=1, center=True, window=3).mean()
    
    # graphic plot thingy
    buffer = BytesIO()
    plt.style.use('fivethirtyeight')
    plt.figure(figsize=(10, 6))
    plt.plot(df.index, df["avg_meme_score"], marker='o', color='#FF6F61', linewidth=1, markersize=8)
    plt.xlabel('Days', fontsize=12)
    plt.ylabel('Average Meme Score', fontsize=12)
    plt.title(f'Meme Scores Over Time ({time_period}) for {user.display_name}', fontsize=16)
    plt.xticks(fontsize=8)
    plt.yticks(fontsize=12)
    plt.ylim(bottom=0, top=max(10, df["avg_meme_score"].max()))  # Start y-axis at 0
    plt.grid(False)
    plt.tight_layout()
    plt.savefig(buffer, format='png', dpi=300)
    plt.close()
    return await ctx.respond(hikari.Bytes(buffer.getvalue(), 'meme_score_results.png'))
    

def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)
