#!/usr/bin/env python

#  Copyright 2022-2025 The KittyBot Authors
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.


import os
import dotenv
import aiohttp
import hikari
import lightbulb

# Some modules are naughty and expect to load things from the environment
# immediately on import.
dotenv.load_dotenv()

import behaviours
import commons.agents
import commons.scheduler


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
async def botStartup(event: hikari.StartedEvent):
    await commons.scheduler.start(event.app)


@bot.listen(lightbulb.CommandErrorEvent)
async def on_error(event: lightbulb.CommandErrorEvent) -> None:
    if isinstance(event.exception, lightbulb.CommandInvocationError):
        error_message = f"Something went wrong during invocation of command `{event.context.command.name if event.context.command else ''}`."
        await event.context.respond(error_message)
        raise event.exception

    # Unwrap the exception to get the original cause
    exception = event.exception.__cause__ or event.exception

    if isinstance(exception, lightbulb.NotOwner):
        await event.context.respond("You are not the owner of this bot.")
    elif isinstance(exception, lightbulb.CommandIsOnCooldown):
        cooldown_message = f"This command is on cooldown for you {event.context.author.mention}. Try again in `{exception.retry_after:.2f}` seconds."
        await event.context.respond(cooldown_message)


@bot.listen()
async def on_starting(event: hikari.StartingEvent) -> None:
    bot.d.aio_session = aiohttp.ClientSession()


@bot.listen()
async def on_stopping(event: hikari.StoppingEvent) -> None:
    await bot.d.aio_session.close()


commons.agents.load()
bot.load_extensions_from("./commands/", must_exist=True)
bot.load_extensions_from("./message_menu_commands/", must_exist=True)
behaviours.register(bot)

if __name__ == "__main__":
    if os.name != "nt":
        import uvloop

        uvloop.install()
    bot.run()
