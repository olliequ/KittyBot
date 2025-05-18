import hikari
import lightbulb
from behaviours import meme_rater
from random import choice

plugin = lightbulb.Plugin("meme_context_commands")

loading_messages = [
    "Rating meme...",
    "Processing meme...",
    "Analyzing meme...",
    "Evaluating meme...",
    "Assessing meme...",
    "Grading meme...",
    "Reviewing meme...",
    "Examining meme...",
    "Judging meme...",
    "Scoring meme...",
    "Stand back, meme rating in progress...",
    "Hold tight, meme rating underway...",
    "Just a moment, meme rating in progress...",
]


@plugin.command
@lightbulb.command("Rate Meme", "Rate this meme using AI")
@lightbulb.implements(lightbulb.MessageCommand)
async def rate_meme_command(ctx: lightbulb.MessageContext) -> None:
    """Rate a meme using the meme rater."""
    message = ctx.options.target

    # Check if message has any media content
    if not message.attachments and not message.embeds:
        await ctx.respond(
            "No meme content found in this message!", flags=hikari.MessageFlag.EPHEMERAL
        )
        return

    loading_message = choice(loading_messages)

    await ctx.respond(loading_message, flags=hikari.MessageFlag.EPHEMERAL)

    existing_results = meme_rater.get_meme_stats(message.id)

    if existing_results:
        await ctx.edit_last_response(
            f"Rating: {existing_results.meme_score}\nEvaluation: {existing_results.emoji()}\nExplanation: {existing_results.meme_reasoning}",
        )
        return

    ratings = await meme_rater.process_message_content(message)

    results = await meme_rater.rate_meme(message, ratings)
    if not results:
        await ctx.edit_last_response("Failed to rate the meme...")
        return

    await ctx.edit_last_response(
        f"Rating: {results.meme_score}\nEvaluation: {results.emoji()}\nExplanation: {results.meme_reasoning}",
    )


def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)
