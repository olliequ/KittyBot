import re
import hikari, lightbulb
import os

plugin = lightbulb.Plugin("rantpatrol")

"""
Bot deletes improperly formatted rants or vents
Message must start with 'rant: ' or 'vent: ' followed by literally any alphanumeric text. Lowercase only.
"""


@plugin.listener(hikari.GuildMessageCreateEvent)
async def main(event: hikari.GuildMessageCreateEvent):
    if event.channel_id != os.environ["RANT_AND_VENT_CHANNEL_ID"]:
        return

    if event.is_bot or not event.content:
        return

    messageContent = event.content

    if not re.match("^(rant|vent): [a-zA-Z0-9_].*", messageContent):
        response: str = (
            f"> Your message must start with 'rant: ' OR 'vent: '. Try again or keep your complaints to yourself."
        )
        await event.message.respond(response, reply=True, user_mentions=True)
    else:
        return


def load(bot: lightbulb.BotApp):
    bot.add_plugin(plugin)
