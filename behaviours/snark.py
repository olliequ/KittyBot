import os, re, datetime, hashlib

import hikari
import behaviours
import db
import commons.agents
import logging as log

eight_ball_responses = [
    "It is certain.",
    "It is decidedly so.",
    "Without a doubt.",
    "Yes, definitely.",
    "You may rely on it.",
    "As I see it, yes.",
    "Most likely.",
    "Outlook good.",
    "Yes.",
    "Signs point to yes.",
    "Reply hazy, try again.",
    "Ask again later.",
    "Better not tell you now.",
    "Cannot predict now.",
    "Concentrate and ask again.",
    "Don't count on it.",
    "My reply is no.",
    "My sources say no.",
    "Outlook not so good.",
    "Very Doubtful.",
]


def choose_eightball_response(message):
    # Add current date down to hour precision to vary the response periodically
    hash_input = message + datetime.datetime.now().strftime("%Y%m%d%H")
    index = hashlib.md5(hash_input.encode()).digest()[0] % len(eight_ball_responses)
    return eight_ball_responses[index]


def find_whole_word(word, text):
    return re.compile(r"\b({0})\b".format(word), flags=re.IGNORECASE).search(text)


def classical_response(event: hikari.GuildMessageCreateEvent) -> str | None:
    message_content = event.content
    if not message_content:
        return None
    regexp = re.compile(r"(\S|\s)\?(\s|$)")
    response = None
    if regexp.search(message_content):
        response = choose_eightball_response(message_content)
    elif find_whole_word("broken", message_content):
        response = f"No {event.author.mention}, you're broken :disguised_face:"
    elif find_whole_word("thanks", message_content) or find_whole_word(
        "thank", message_content
    ):
        response = f"You're welcome {event.author.mention} :heart:"
    elif find_whole_word("work", message_content):
        response = f"{event.author.mention} I do work."
    elif (
        find_whole_word("hey", message_content)
        or find_whole_word("hi", message_content)
        or find_whole_word("hello", message_content)
    ):
        response = f"Hey {event.author.mention}, I am a cat. With robot intestines. If you're bored, you should ask me a question, or check out my `+userinfo`, `+ping`, `+fortune` and `+fact` commands :cat:"
    elif (
        event.message.referenced_message
        and event.message.referenced_message.author
        and event.message.referenced_message.author.id == event.shard.get_user_id()
    ):
        return None
    else:
        response = f"{event.author.mention}, did you forget a question mark? <:mmhmmm:872809423939174440>"
    return response


async def llm_response(event) -> str | None:
    message_content = event.content
    try:
        prompt = db.get_option("LLM_PROMPT")
        response = await commons.agents.agent('chat').run(
            message_content, event.author.mention, prompt
        )
        if not response:
            return "No."
    except Exception as e:
        log.exception("Cannot get LLM response", exc_info=e)
        return classical_response(event)
    return response.replace("@everyone", "everyone").replace("@here", "here")


async def main(event: hikari.GuildMessageCreateEvent) -> None:
    if event.is_bot or not event.content:
        return
    mentioned_ids = event.message.user_mentions_ids
    if not mentioned_ids or event.shard.get_user_id() not in mentioned_ids:
        return
    if event.channel_id == int(os.environ.get("ORIGINALITY_CHANNEL_ID")):
        response = await llm_response(event)
    else:
        response = classical_response(event)
    if response:
        await event.message.respond(response, user_mentions=True, reply=True)
        raise behaviours.EndProcessing()
