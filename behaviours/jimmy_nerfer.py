import hikari
import asyncio
import behaviours

FIRESHIP_GUILD_ID = 1015095797689360444
DELETION_NOTIFICATION_LONGEVITY = 10


async def delete_duplicate(event: hikari.GuildMessageCreateEvent) -> None:
    ref = event.message.message_reference
    if ref and ref.guild_id == FIRESHIP_GUILD_ID:
        await event.message.delete()
        response = await event.message.respond(
            f"Hey {event.author.mention}! No fireship forwards!!! Seethe and cope.",
            user_mentions=True,
        )
        await asyncio.sleep(DELETION_NOTIFICATION_LONGEVITY)
        await response.delete()
        raise behaviours.EndProcessing()
