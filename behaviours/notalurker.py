import os
import re

"""
Bot adds #notalurker role for those who comment.
"""


async def main(event) -> None:
    if event.is_bot or not event.content or "NOTALURKER_ROLE" not in os.environ:
        return
    channelSentIn = event.channel_id
    messageContent = event.content
    messageContent = re.sub(r"<.+?>", "", messageContent)
    if not any(c.isalpha() for c in messageContent):
        return
    currentRoles = (await event.get_member().fetch_roles())[1:]
    for role in currentRoles:
        if role.id == int(os.environ["NOTALURKER_ROLE"]):
            return
    await event.get_member().add_role(int(os.environ["NOTALURKER_ROLE"]))
