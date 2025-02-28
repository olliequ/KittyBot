"""
Displays a graph of meme ratings for a user, grouped by day.
Todo: make day/hour/week whatever a parameter.
"""
import db
import hikari
import lightbulb
import matplotlib.font_manager as fm
import matplotlib.image as image
import matplotlib.pyplot as plt
from io import BytesIO

plugin = lightbulb.Plugin("MemeStats")

@plugin.command
@lightbulb.add_cooldown(10, 1, lightbulb.UserBucket)
@lightbulb.option("target", "The member to roast (or not?).", hikari.User, required=True)
@lightbulb.command("memestats", "See someone's average meme rating over time")
@lightbulb.implements(lightbulb.PrefixCommand,lightbulb.SlashCommand)
async def main(ctx: lightbulb.Context) -> None:
    guild = ctx.get_guild()
    cursor = db.cursor()
    user_id = ctx.options.target.id
    user = guild.get_member(user_id)

    # todo: add a limit or aggregation of greater time periods or whatever
    # todo: get someone else to do this
    data = cursor.execute("""
        select strftime('%Y-%m-%d', time_sent) as day,
            AVG(meme_score) as avg_meme_score
        from meme_stats
        where user = ?
        group BY user, day
    """, (user_id,)).fetchall()

    if not data:
        return await ctx.respond(f"Looks like {user.display_name} hasn't had any of their memes rated yet. 10/10 for them!")
    
    # graphic plot thingy
    buffer = BytesIO()
    x = [item[0] for item in data]
    y = [item[1] for item in data]
    plt.style.use('ggplot')
    plt.figure(figsize=(10, 6))
    plt.plot(x, y, marker='o', color='#1f77b4', linewidth=2, markersize=8)
    plt.xlabel('Day', fontsize=14)
    plt.ylabel('Average Meme Score', fontsize=14)
    plt.title(f'Meme Scores Over Time (Days) for {user.display_name}', fontsize=16)
    plt.xticks(fontsize=12)
    plt.yticks(fontsize=12)
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(buffer, format='png', dpi=300)
    plt.close()
    return await ctx.respond(hikari.Bytes(buffer.getvalue(), 'meme_score_results.png'))
    

def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)
