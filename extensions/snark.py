import re, datetime, hashlib
import hikari, lightbulb

plugin = lightbulb.Plugin("Snark")

eight_ball_responses = [ "It is certain.", "It is decidedly so.", "Without a doubt.", "Yes, definitely.",
               "You may rely on it.", "As I see it, yes.", "Most likely.", "Outlook good.",
               "Yes.", "Signs point to yes.", "Reply hazy, try again.", "Ask again later.",
               "Better not tell you now.", "Cannot predict now.", "Concentrate and ask again.",
               "Don't count on it.", "My reply is no.", "My sources say no.", "Outlook not so good.", "Very Doubtful."]

def choose_eightball_response(message):
    # Add current date down to hour precision to vary the response periodically
    hash_input = message + datetime.datetime.now().strftime('%Y%m%d%H')
    index = hashlib.md5(hash_input.encode()).digest()[0] % len(eight_ball_responses)
    return eight_ball_responses[index]

def find_whole_word(word, text):
    return re.compile(r'\b({0})\b'.format(word), flags=re.IGNORECASE).search(text)

@plugin.listener(hikari.GuildMessageCreateEvent)
async def main(event) -> None:
    if event.is_bot or not event.content:
        return
    mentioned_ids = event.message.mentions.user_ids
    if plugin.bot.application.id not in mentioned_ids:
        return
    messageContent = event.content
    regexp = re.compile(r'(\S|\s)\?(\s|$)')
    if regexp.search(messageContent):
        await event.message.respond(choose_eightball_response(messageContent))
    elif find_whole_word('broken', messageContent):
        await event.message.respond(f"No {event.author.mention}, you're broken :disguised_face:")
    elif find_whole_word('thanks', messageContent) or find_whole_word('thank', messageContent):
        await event.message.respond(f"You're welcome :heart:")
    elif find_whole_word('work', messageContent):
        await event.message.respond(f"{event.author.mention} I do work.")
    elif find_whole_word('hey', messageContent) or find_whole_word('hi', messageContent) or find_whole_word('hello', messageContent):
        await event.message.respond(f"Hey {event.author.mention}, I am a cat. With robot intestines. If you're bored, you should ask me a question, or check out my `+userinfo`, `+ping`, `+fortune` and `+fact` commands :cat:")
    else:
        await event.message.respond(f"{event.author.mention}, did you forget a question mark? <:mmhmmm:872809423939174440>")

def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)
