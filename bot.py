#!/usr/bin/env python

import os, re, random
import dotenv, aiohttp
import hikari, lightbulb

dotenv.load_dotenv()

bot = lightbulb.BotApp(
        os.environ["BOT_TOKEN"],
        prefix="+",
        banner=None,
        intents=hikari.Intents.ALL,
        default_enabled_guilds=tuple(int(v) for v in os.environ["DEFAULT_GUILDS"].split(','))
        )


@bot.listen(hikari.StartedEvent)
async def botStartup(event):
    print("Bot has started up!")

# Simple ping-pong command example.
@bot.command
@lightbulb.add_cooldown(10, 1, lightbulb.UserBucket)
@lightbulb.command("ping", description="The bot's ping")
@lightbulb.implements(lightbulb.PrefixCommand)
async def ping(ctx: lightbulb.Context) -> None:
    await ctx.respond(f"Pong! Latency: {bot.heartbeat_latency*1000:.2f}ms")


"""
Bot adds #notalurker role for those who comment.
"""
@bot.listen(hikari.GuildMessageCreateEvent)
async def give_role(event):

    if event.is_bot or not event.content:
        return
    
    channelSentIn = event.channel_id
    if channelSentIn != 938847222601240656 and channelSentIn != 938894077519356004 and event.get_member().id != 940684135687659581:
        messageContent = event.content
        messageContent = re.sub(r'<.+?>', "", messageContent)
        print(f"Sender: {event.author} | Content: {messageContent}")

        if any(c.isalpha() for c in messageContent):
            print("Message contains valid symbols.")
            currentRoles = (await event.get_member().fetch_roles())[1:]
            hasRole = False
            for role in currentRoles:
                # print(f"{role}: {type(role)}")
                if role.id == 847009026817654805 or role.id == 938871141110517761:
                    print("Already has role.\n")
                    hasRole = True
            if hasRole is False: # User doesn't have the role yet, and we need to give it to them.
                print("Giving role now.\n")
                if event.guild_id == 813213508036067348: # CS
                    print("CS server.")
                    await event.get_member().add_role(847009026817654805) 
                elif event.guild_id == 798180001101905940: # Personal
                    print("Personal server.")
                    await event.get_member().add_role(938871141110517761)


@bot.listen(lightbulb.CommandErrorEvent)
async def on_error(event: lightbulb.CommandErrorEvent) -> None:
    if isinstance(event.exception, lightbulb.CommandInvocationError):
        await event.context.respond(f"Something went wrong during invocation of command `{event.context.command.name}`.")
        raise event.exception

    # Unwrap the exception to get the original cause
    exception = event.exception.__cause__ or event.exception

    if isinstance(exception, lightbulb.NotOwner):
        await event.context.respond("You are not the owner of this bot.")
    elif isinstance(exception, lightbulb.CommandIsOnCooldown):
        await event.context.respond(f"This command is on cooldown for you {event.context.author.mention}. Try again in `{exception.retry_after:.2f}` seconds.")

"""
Below creates 2 listeners, one for when the bot is starting, and one for when the bot is stopping. 
When the bot is starting, it creates a new aiohttp.ClientSession named aio_session and stores it in the bot.d data store. 
When the bot is stopping, it closes the aio_session.
"""
@bot.listen()
async def on_starting(event: hikari.StartingEvent) -> None:
    bot.d.aio_session = aiohttp.ClientSession()

@bot.listen()
async def on_stopping(event: hikari.StoppingEvent) -> None:
    await bot.d.aio_session.close()

bot.load_extensions_from("./extensions/", must_exist=True)

if __name__ == "__main__":
    if os.name != "nt":
        import uvloop
        uvloop.install()
    bot.run()
