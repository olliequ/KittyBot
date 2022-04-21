import lightbulb
import hikari
import cowsay

plugin = lightbulb.Plugin("Cowsay")

@plugin.command
@lightbulb.option("moossage", "What to moo.")
@lightbulb.command("cowsay", "Moo.")
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def main(ctx: lightbulb.Context) -> None:
    msg = code_block(moo(ctx.option.moossage)})
    if len(msg) > 2000:
        await ctx.respond(code_block(moo("I can only moo so much.\n"
                                         "That moossage was too long.")))
    else:
        await ctx.respond(msg)
        
def moo(msg: str) -> str:
    return cowsay.get_output_string(char_name="cow", text=msg)

def code_block(s: str) -> str:
    return f"```{s}```"

def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)
