import asyncio
from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline

import hikari

import behaviours


async def main(event: hikari.GuildMessageCreateEvent) -> None:
    DELETION_NOTIFICATION_LONGEVITY = 5
    if event.is_bot or not event.content:
        return
    text = event.content

    tokenizer = AutoTokenizer.from_pretrained("alexneakameni/language_detection")
    model = AutoModelForSequenceClassification.from_pretrained(
        "alexneakameni/language_detection"
    )
    language_detection = pipeline(
        "text-classification", model=model, tokenizer=tokenizer
    )
    predictions = language_detection(text)
    if predictions[0].get("label", "") == "fra_Latn":  # any probability
        response = await event.message.respond(
            f"Hey {event.author.mention}! Unfortunately, French is banned here. Oh non!",
            user_mentions=True,
        )
        await asyncio.sleep(DELETION_NOTIFICATION_LONGEVITY)
        await response.delete()
        raise behaviours.EndProcessing()
