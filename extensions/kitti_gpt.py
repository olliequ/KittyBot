import google.generativeai as genai

import re, datetime, hashlib
import hikari, lightbulb
import os

plugin = lightbulb.Plugin("KittiGPT")

genai.configure(api_key=os.environ["GEMINI_API_KEY"])

# Set up the model
generation_config = {
    "temperature": 1,
    "top_p": 1,
    "top_k": 1,
    "max_output_tokens": 2000,
}

safety_settings = [
    {
        "category": "HARM_CATEGORY_HARASSMENT",
        "threshold": "BLOCK_ONLY_HIGH"
    },
    {
        "category": "HARM_CATEGORY_HATE_SPEECH",
        "threshold": "BLOCK_ONLY_HIGH"
    },
    {
        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
        "threshold": "BLOCK_ONLY_HIGH"
    },
    {
        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
        "threshold": "BLOCK_ONLY_HIGH"
    },
]

model = genai.GenerativeModel(model_name="gemini-pro",
                              generation_config=generation_config,
                              safety_settings=safety_settings)


@plugin.listener(hikari.GuildMessageCreateEvent)
async def main(event) -> None:
    if event.is_bot or not event.content:
        return
    mentioned_ids = event.message.user_mentions_ids
    if plugin.bot.application.id not in mentioned_ids:
        return
    messageContent = event.content
    prompt_parts = [
        "You are the Savage Kitti Bot on Computer Science @ UniMelb Discord. Respond Appropriately. Kitti has a God "
        f"Complex and doesn't hold back. You are gen z and reply succinct.\nQ: {messageContent}",
    ]

    response = model.generate_content(prompt_parts)

    if response.candidates[0].finish_reason != 1:
        await event.message.respond("Too NSFW to say", user_mentions=True, reply=True)
        return

    await event.message.respond(response.text, user_mentions=True, reply=True)


def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)
