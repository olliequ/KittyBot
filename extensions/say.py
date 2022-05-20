import lightbulb
import hikari
import cowsay

import extensions.fortune

plugin = lightbulb.Plugin("Say")

@plugin.command
@lightbulb.option("character", "Which character?", 
                  required=True, choices=cowsay.char_names)
@lightbulb.option("message", "Message to say", 
                  required=True)
@lightbulb.command("say", "Say a message with an ASCII character")
@lightbulb.implements(lightbulb.SlashCommand)
async def main(ctx: lightbulb.Context) -> None:
    character = ctx.options.character
    if character not in cowsay.char_names:
        message = say(f"I don't know a '{character}'")
    else:
        message = ctx.options.message.strip()
        if message == "fortune" or ctx.prefix + message == "fortune":
            message = extensions.fortune.fortune()
        message = say(message, character)

    if len(message) > 2000:
        await ctx.respond(say("That message was too long."))
    else:
        await ctx.respond(message)
        
def say(msg: str, character: str = "cow") -> str:
    return code_block(cowsay.get_output_string(text=msg, char_name=character))

def code_block(s: str) -> str:
    return f"```{s}```"

def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)