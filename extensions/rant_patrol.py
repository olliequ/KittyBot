import re
import hikari, lightbulb
import os

plugin = lightbulb.Plugin("rantpatrol")

"""
Bot deletes improperly formatted rants or vents
Message must start with 'rant: ' or 'vent: ' followed by literally any alphanumeric text. Lowercase only.
"""

# helpers


@plugin.listener(hikari.GuildMessageCreateEvent)
async def main(event: hikari.GuildMessageCreateEvent):
    if event.channel_id != os.environ["RANT_AND_VENT_CHANNEL_ID"]:
        return

    if event.is_bot or not event.content:
        return

    messageContent = event.content

    """
    "Rant: too many memes" ==> picked up by kitti
    "rant: my website's domain got sniped" ==> all good (properly formatted)
    "shut the fuck up jimmy"" ==> all good (standard comment)    
    """

    if re.match("^((anti)?(rant|vent):).", messageContent.lower().strip("-")):
        if not re.match("^((anti-)?(rant|vent):).", messageContent):
            response: str = (
                f"> Your message must start with 'rant: ' OR 'vent: ' with the optional 'anti-' prefix. Try again or keep your complaints to yourself."
            )
            await event.message.respond(response, reply=True, user_mentions=True)
        else:
            return
    return


def load(bot: lightbulb.BotApp):
    bot.add_plugin(plugin)
