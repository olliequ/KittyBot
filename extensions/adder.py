import lightbulb

plugin = lightbulb.Plugin("Adder")

@plugin.command
@lightbulb.option('num2', 'Second number', type=int)
@lightbulb.option('num1', 'First number', type=int)
@lightbulb.command('numberadder', 'Adds 2 numbers together')
@lightbulb.implements(lightbulb.PrefixCommand, lightbulb.SlashCommand)
async def main(ctx: lightbulb.Context) -> None:
    await ctx.respond(ctx.options.num1 + ctx.options.num2)

def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)
