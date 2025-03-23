import re
import hikari

CISSA_REGEX = re.compile(r"\bCISSA\b")


async def main(event: hikari.GuildMessageCreateEvent) -> None:
    if not event.is_human or not event.content:
        return
    content = event.content
    is_cissa_mentioned = re.search(CISSA_REGEX, content)
    if is_cissa_mentioned:
        await event.message.respond(
            f"Hey {event.author.display_name}, we don't talk about C*SSA here!!! 📍 🐱",
            reply=True,
            user_mentions=True,
        )
