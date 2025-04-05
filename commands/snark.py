import os
import lightbulb
import commons.db as db

plugin = lightbulb.Plugin("Snark")


@plugin.command
@lightbulb.option(
    "prompt", "New prompt. {} is replaced with input.", type=str, required=True
)
@lightbulb.command("setprompt", "Update LLM prompt")
@lightbulb.implements(lightbulb.SlashCommand)
async def setprompt(ctx: lightbulb.Context) -> None:
    if not ctx.member:
        return
    current_roles = (await ctx.member.fetch_roles())[1:]
    for role in current_roles:
        if role.id == int(os.environ["BOT_ADMIN_ROLE"]):
            prompt = ctx.options.prompt
            db.set_option("LLM_PROMPT", prompt)
            print("Prompt is now: " + prompt)
            await ctx.respond("OK")
            return
    await ctx.respond("Not an admin")


def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)
