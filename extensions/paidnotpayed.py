import os, re
import hikari, lightbulb

plugin = lightbulb.Plugin("paid")

"""
Bot makes a slight correction.
"""
def find_whole_word(word, text):
    return re.compile(r'\b({0})\b'.format(word), flags=re.IGNORECASE).search(text)

@plugin.listener(hikari.GuildMessageCreateEvent)
async def main(event):
    if event.is_bot or not event.content or "NOTALURKER_ROLE" not in os.environ:
        return
    channelSentIn = event.channel_id
    messageContent = event.content
    messageContent = re.sub(r'<.+?>', "", messageContent)

    if not any(c.isalpha() for c in messageContent):
        return

    if find_whole_word('payed', messageContent):
        corrected_message = messageContent.replace("payed", "*paid*")
        output_message = f"""FTFY.\n\nAlthough *payed* exists (the reason why autocorrection didn't help you), it is only correct in:\n\n**1)** Nautical context, when it means to paint a surface, or to cover with something like tar or resin in order to make it waterproof or corrosion-resistant. *The deck is yet to be payed*.\n**2)** Payed out when letting strings, cables or ropes out, by slacking them. *The rope is payed out! You can pull now*.\n\nUnfortunately {event.author.mention}, I was unable to find nautical or rope-related words in your comment."""
        response = f"> {corrected_message}\n\n{output_message}"
        await event.message.respond(response, reply=True, user_mentions=True)
    else:
        # print("Sentence doesn't contain 'payed'.")
        return

def load(bot: lightbulb.BotApp):
    bot.add_plugin(plugin)