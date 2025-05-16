import hikari
import lightbulb
from behaviours import meme_rater

plugin = lightbulb.Plugin("meme_context_commands")


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

    await ctx.respond("Rating meme...", flags=hikari.MessageFlag.EPHEMERAL)

    ratings, explanations = await meme_rater.process_message_content(message)
    if not ratings:
        await ctx.edit_last_response(
            "Failed to rate the meme...", flags=hikari.MessageFlag.EPHEMERAL
        )
        return

    results = await meme_rater.rate_meme(message, ratings, explanations)
    if not results:
        await ctx.edit_last_response(
            "Failed to rate the meme...", flags=hikari.MessageFlag.EPHEMERAL
        )
        return

    await ctx.edit_last_response(
        f"Rating: {results['rating']}\nEvaluation: {results['emoji']}\nExplanation: {results['explanation']}",
        flags=hikari.MessageFlag.EPHEMERAL,
    )


def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)
