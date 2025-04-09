import re
import hikari
import os

import behaviours
from commons import message_utils


ALLOWED_STEMS = ["rant", "vent"]
ALLOWED_PREFIXES = ["anti-", "co-"]
ALLOWED_STEMS_PIPED = "|".join(ALLOWED_STEMS)
ALLOWED_PREFIXES_PIPED = "|".join(ALLOWED_PREFIXES)

RANT_REGEX = re.compile(f"^[^ ]*({ALLOWED_STEMS_PIPED}) *:", flags=re.IGNORECASE)
VALID_RANT_REGEX = re.compile(
    f"^({ALLOWED_PREFIXES_PIPED})*({ALLOWED_STEMS_PIPED}): ", flags=re.IGNORECASE
)
VALID_CONTENTLESS_RANT_REGEX = re.compile(
    f"^({ALLOWED_PREFIXES_PIPED})*({ALLOWED_STEMS_PIPED}):$", flags=re.IGNORECASE
)

FORMATTED_STEMS = message_utils.humanize_list(
    [f"'{stem}: '" for stem in ALLOWED_STEMS], "or"
)


async def main(event: hikari.GuildMessageCreateEvent):
    if not event.is_human or not event.content:
        return
    rant_channel_id = os.environ["RANT_AND_VENT_CHANNEL_ID"]
    in_channel = event.channel_id == int(rant_channel_id)
    content = event.content
    is_a_rant = RANT_REGEX.match(content)
    is_valid = VALID_RANT_REGEX.match(content) or (
        VALID_CONTENTLESS_RANT_REGEX.match(content)
        and (event.embeds or event.message.attachments)
    )

    response = None
    if is_a_rant and not in_channel:
        response = (
            f"You appear to be ranting or venting, please move to <#{rant_channel_id}>"
        )
    elif is_a_rant and not is_valid:
        response = f"Your message must start with {FORMATTED_STEMS}, and may be preceded by pre-approved prefixes. Try again or keep your complaints to yourself."
    if response:
        await event.message.respond(response, reply=True, user_mentions=True)
        raise behaviours.EndProcessing()
