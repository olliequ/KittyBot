import commons.db as db
import lightbulb

plugin = lightbulb.Plugin("Kitti Co-ordle stats")


def _bar(val: float, scale: float) -> str:
    return "▉" * max(1, int(round(val * scale)))


@plugin.command
@lightbulb.command(
    "wordle_stats", "Show your last 10 Kitti Wordle scores as an ASCII graph."
)
@lightbulb.implements(lightbulb.SlashCommand)
async def main(ctx: lightbulb.Context) -> None:
    if not ctx.member:
        return

    cur = db.cursor()
    cur.execute(
        """
        SELECT day, AVG(round_score) AS avg_score
        FROM   wordle_stats
        WHERE  user = ?
        GROUP  BY day
        ORDER  BY day DESC
        LIMIT  10
        """,
        (ctx.member.id,),
    )
    rows = cur.fetchall()
    if not rows:
        await ctx.respond("No Wordle data for you.")
        return

    max_avg = max(r[1] for r in rows)
    scale = 20 / max_avg if max_avg else 1

    lines = [
        f"{day[-5:]} │ {_bar(avg, scale)} {avg:.1f}"  # show last 5 chars of ISO date (-MM-DD)
        for day, avg in rows
    ]

    overall = sum(avg for _, avg in rows) / len(rows)

    graph = (
        "```\n"
        + "Average daily Kitti Co-ordle score per day"
        + "\n".join(lines)
        + f"\n──────┴───────────────────\n mean │ {overall:.2f}\n```"
    )
    await ctx.respond(graph, user_mentions=True)


def load(bot: lightbulb.BotApp):
    bot.add_plugin(plugin)
