import commons.db as db
import lightbulb

plugin = lightbulb.Plugin("Kitti Co-ordle stats")


def _bar(val: float, scale: float) -> str:
    return "▉" * max(1, int(round(val * scale)))


@plugin.command
@lightbulb.command(
    "wordle_stats", "Shows assorted stats from your Kitti co-ordle guess history."
)
@lightbulb.implements(lightbulb.SlashCommand)
async def main(ctx: lightbulb.Context) -> None:
    if not ctx.member:
        return

    cur = db.cursor()
    # last 10 days graph
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
    lines = [f"{day[-5:]} │ {_bar(avg, scale)} {avg:.1f}" for day, avg in rows]
    overall = sum(avg for _, avg in rows) / len(rows)
    graph = (
        "```\n"
        "Average daily Kitti Co-ordle score per day\n"
        + "\n".join(lines)
        + f"\n──────┴───────────────────\n mean │ {overall:.2f}\n```"
    )

    # most used starting word
    cur.execute(
        """
        SELECT guess, COUNT(*) AS cnt
        FROM   wordle_stats
        WHERE  user = ? AND round = 0
        GROUP  BY guess
        ORDER  BY cnt DESC
        LIMIT  1
        """,
        (ctx.member.id,),
    )
    first = cur.fetchone()
    start_word, start_count = first if first else ("—", 0)

    # top 5 guesses overall
    cur.execute(
        """
        SELECT guess, COUNT(*) AS cnt
        FROM   wordle_stats
        WHERE  user = ?
        GROUP  BY guess
        ORDER  BY cnt DESC
        LIMIT  5
        """,
        (ctx.member.id,),
    )
    top = cur.fetchall()
    top_list = "\n".join(f"{i+1}. {w} ({c})" for i, (w, c) in enumerate(top))

    stats = (
        f"Most used starting word: **{start_word}** ({start_count} times)\n"
        f"Top 5 guesses:\n{top_list}"
    )

    await ctx.respond(f"{graph}\n{stats}", user_mentions=True)


def load(bot: lightbulb.BotApp):
    bot.add_plugin(plugin)
