#!/usr/bin/env python

import os
import dotenv, aiohttp
import hikari, lightbulb
from commons.message_utils import send_long_message

# Some modules are naughty and expect to load things from the environment
# immediately on import.
dotenv.load_dotenv()

import behaviours
import commons.agents


bot = lightbulb.BotApp(
    os.environ["BOT_TOKEN"],
    prefix="+",
    banner=None,
    intents=hikari.Intents.ALL,
    default_enabled_guilds=tuple(
        int(v) for v in os.environ["DEFAULT_GUILDS"].split(",")
    ),
)


@bot.listen(hikari.StartedEvent)
async def botStartup(event):
    print("Bot has started up!")


@bot.listen(lightbulb.CommandErrorEvent)
async def on_error(event: lightbulb.CommandErrorEvent) -> None:
    if isinstance(event.exception, lightbulb.CommandInvocationError):
        error_message = f"Something went wrong during invocation of command `{event.context.command.name}`."
        await send_long_message(event.context, error_message)
        raise event.exception

    # Unwrap the exception to get the original cause
    exception = event.exception.__cause__ or event.exception

    if isinstance(exception, lightbulb.NotOwner):
        await send_long_message(event.context, "You are not the owner of this bot.")
    elif isinstance(exception, lightbulb.CommandIsOnCooldown):
        cooldown_message = f"This command is on cooldown for you {event.context.author.mention}. Try again in `{exception.retry_after:.2f}` seconds."
        await send_long_message(event.context, cooldown_message)


@bot.listen()
async def on_starting(event: hikari.StartingEvent) -> None:
    bot.d.aio_session = aiohttp.ClientSession()


@bot.listen()
async def on_stopping(event: hikari.StoppingEvent) -> None:
    await bot.d.aio_session.close()


commons.agents.load()
bot.load_extensions_from("./commands/", must_exist=True)
behaviours.register(bot)

if __name__ == "__main__":
    if os.name != "nt":
        import uvloop

        uvloop.install()
    bot.run()
