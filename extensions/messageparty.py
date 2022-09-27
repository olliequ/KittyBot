import os, db
import hikari, lightbulb

plugin = lightbulb.Plugin("messageparty")

"""
Kitti congratulates you for your efforts.
"""
@plugin.listener(hikari.GuildMessageCreateEvent)
async def main(event):
    if event.is_bot or not event.content or "NOTALURKER_ROLE" not in os.environ:
        return
    
    messageContent = event.content
    user_id = event.author_id
    cursor = db.cursor()
    cursor.execute("""SELECT user, count FROM message_counts 
                      WHERE user = ?""", (user_id,))
    data = cursor.fetchall()
    message_count = data[0][1]
    message_count_formatted = "{:,}".format(message_count)
    if message_count % 4 == 0:
        response = f"""<a:partyblob:815938533470240799> <a:partyblob:815938533470240799> <a:partyblob:815938533470240799> {event.author.mention}, congratulations on sending **{message_count_formatted}** messages! <a:partyblob:815938533470240799> <a:partyblob:815938533470240799> <a:partyblob:815938533470240799>.
        \nWhat an epic milestone! <:catking:993871956103405639>"""
        await event.message.respond(response, user_mentions=True)
    elif message_count % 1000 == 0:
        response1 = f"""<a:partyblob:815938533470240799> <a:partyblob:815938533470240799> <a:partyblob:815938533470240799> {event.author.mention}, congratulations on sending {message_count} messages! <a:partyblob:815938533470240799> <a:partyblob:815938533470240799> <a:partyblob:815938533470240799>."""
        await event.message.respond(response1, user_mentions=True)

def load(bot: lightbulb.BotApp):
    bot.add_plugin(plugin)