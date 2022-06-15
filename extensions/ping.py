import lightbulb

plugin = lightbulb.Plugin("Ping")

@plugin.command
@lightbulb.add_cooldown(10, 1, lightbulb.UserBucket)
@lightbulb.command("ping", description="The bot's ping")
@lightbulb.implements(lightbulb.PrefixCommand)
async def main(ctx: lightbulb.Context) -> None:
    await ctx.respond(f"Pong! Latency: {plugin.bot.heartbeat_latency*1000:.2f}ms")

def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)
