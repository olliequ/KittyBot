import hikari, lightbulb, sqlite3
from PIL import Image
import imagehash
import db
import re
import requests
import io

plugin = lightbulb.Plugin("ImageHashDetector")


@plugin.listener(hikari.GuildMessageCreateEvent)
async def main(event: hikari.GuildMessageCreateEvent) -> None:
    # Don't handle messages from bots or without content
    if event.is_bot:
        return

    # Connect to the sqlite3 database
    c = db.cursor()

    # Iterate through the attachments in the message
    for attachment in event.message.attachments:
        # Check if the attachment is an image
        file_name = attachment.filename
        file_extension = re.search(r'\.(\w+)$', file_name).group(1)
        if file_extension == "png" or file_extension == "jpg":
            # Calculate the approximate hash of the image
            # Download the file from the specified URL
            response = requests.get(attachment.url)

            # Create a memory buffer
            file_buffer = io.BytesIO(response.content)
            image = Image.open(file_buffer)
            image_hash = imagehash.average_hash(image)
            # Check if the approximate hash exists in the database
            c.execute("SELECT * FROM image_hashes WHERE hash=?", (str(image_hash),))
            result = c.fetchone()
            if result:
                # If a match is found, delete the message and inform the user
                await event.message.delete()
                await event.message.respond(
                    f"Hey {event.author.mention}! Your image has been detected as a duplicate and has been deleted."
                )
            # Otherwise, add the approximate hash to the database
            else:
                c.execute("INSERT INTO image_hashes (hash) VALUES (?)", (str(image_hash),))

def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)
