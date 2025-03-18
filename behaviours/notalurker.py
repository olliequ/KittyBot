import os
import re

import hikari
from commons.message_utils import get_member

"""
Bot adds #notalurker role for those who comment.
"""


async def main(event: hikari.GuildMessageCreateEvent) -> None:
    if event.is_bot or not event.content or "NOTALURKER_ROLE" not in os.environ:
        return
    messageContent = event.content
    messageContent = re.sub(r"<.+?>", "", messageContent)
    if not any(c.isalpha() for c in messageContent):
        return
    currentRoles = (await get_member(event, event.author_id).fetch_roles())[1:]
    for role in currentRoles:
        if role.id == int(os.environ["NOTALURKER_ROLE"]):
            return
    await event.app.rest.add_role_to_member(
        event.guild_id, event.author, int(os.environ["NOTALURKER_ROLE"])
    )
