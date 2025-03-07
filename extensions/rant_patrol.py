import re
import hikari, lightbulb
import os
import random

plugin = lightbulb.Plugin("Rantpatrol")

RANT_REGEX = re.compile("^[^ ]*(rant|vent) *:", flags=re.IGNORECASE)
FORMAT_REGEX = re.compile("^(anti-|co-)?(rant|vent): ")


@plugin.listener(hikari.GuildMessageCreateEvent)
async def main(event: hikari.GuildMessageCreateEvent):
    if not event.is_human or not event.content:
        return

    rant_channel_id = os.environ["RANT_AND_VENT_CHANNEL_ID"]
    in_channel = event.channel_id == int(rant_channel_id)
    content = event.content
    is_a_rant = RANT_REGEX.match(content)
    content = random.choice([content, content.lower()])
    is_valid = FORMAT_REGEX.match(content)

    response = None
    if is_a_rant and not in_channel:
        response = (
            f"You appear to be ranting or venting, please move to <#{rant_channel_id}>"
        )
    elif is_a_rant and not is_valid:
        response = "Your message must start with 'rant: ' or 'vent: ', with an optional pre-approved prefix. Try again or keep your complaints to yourself."

    if response:
        await event.message.respond(response, reply=True, user_mentions=True)


def load(bot: lightbulb.BotApp):
    bot.add_plugin(plugin)
