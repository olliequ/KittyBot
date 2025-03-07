import os, re, datetime, hashlib
import hikari, lightbulb
import db
from commons.agents import kitty_gemini_agent
import logging as log

plugin = lightbulb.Plugin("Snark")

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


def classical_response(event) -> str | None:
    message_content = event.content
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
        and event.message.referenced_message.author.id == plugin.bot.application.id
    ):
        return None
    else:
        response = f"{event.author.mention}, did you forget a question mark? <:mmhmmm:872809423939174440>"
    return response


async def llm_response(event) -> str | None:
    message_content = event.content
    try:
        prompt = db.get_option("LLM_PROMPT")
        response = await kitty_gemini_agent.run(
            message_content, event.author.mention, prompt
        )
        if not response:
            return "No."
    except Exception as e:
        log.info(e)
        return classical_response(event)
    return response.replace("@everyone", "everyone").replace("@here", "here")


@plugin.command
@lightbulb.option(
    "prompt", "New prompt. {} is replaced with input.", type=str, required=True
)
@lightbulb.command("setprompt", "Update LLM prompt")
@lightbulb.implements(lightbulb.SlashCommand)
async def setprompt(ctx: lightbulb.Context) -> None:
    current_roles = (await ctx.member.fetch_roles())[1:]
    for role in current_roles:
        if role.id == int(os.environ["BOT_ADMIN_ROLE"]):
            prompt = ctx.options.prompt
            db.set_option("LLM_PROMPT", prompt)
            print("Prompt is now: " + prompt)
            await ctx.respond("OK")
            return
    await ctx.respond("Not an admin")


@plugin.listener(hikari.GuildMessageCreateEvent)
async def main(event) -> None:
    if event.is_bot or not event.content:
        return
    mentioned_ids = event.message.user_mentions_ids
    if plugin.bot.application.id not in mentioned_ids:
        return
    if event.channel_id == int(os.environ.get("ORIGINALITY_CHANNEL_ID")):
        response = await llm_response(event)
    else:
        response = classical_response(event)
    if response:
        await event.message.respond(response, user_mentions=True, reply=True)


def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)
