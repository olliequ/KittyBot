import asyncio
from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline  # type: ignore

import hikari

import behaviours


async def main(event: hikari.GuildMessageCreateEvent) -> None:
    DELETION_NOTIFICATION_LONGEVITY = 5
    if event.is_bot or not event.content:
        return
    text = event.content

    tokenizer = AutoTokenizer.from_pretrained("alexneakameni/language_detection")  # type: ignore
    model = AutoModelForSequenceClassification.from_pretrained(  # type: ignore
        "alexneakameni/language_detection"
    )
    language_detection = pipeline(
        "text-classification", model=model, tokenizer=tokenizer  # type: ignore
    )
    predictions = language_detection(text)  # type: ignore
    if predictions[0].get("label", "") == "fra_Latn":  # type: ignore # any probability
        response = await event.message.respond(
            f"Hey {event.author.mention}! Unfortunately, French is banned here. Oh non!",
            user_mentions=True,
        )
        await asyncio.sleep(DELETION_NOTIFICATION_LONGEVITY)
        await response.delete()
        raise behaviours.EndProcessing()
