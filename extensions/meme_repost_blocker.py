import hikari, lightbulb, sqlite3
from PIL import Image
import imagehash
import db
import re
import requests
import io

plugin = lightbulb.Plugin("ImageHashDetector")
print("test!")

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
        file_extension = re.search(r"\.(\w+)$", file_name).group(1)
        image_file_extensions = ["bmp", "gif", "jpg", "jpeg", "png", "tiff", "webp"]
        if file_extension in image_file_extensions:
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
                # Get the ID of the message that you want to link to
                message_id = result[1]
                channel_id = result[2]
                guild_id = result[3]

                # Construct the message that you want to send
                response_message = f"Hey {event.author.mention}! Your image has apparently already been posted. Time for more original memes! It was first posted here: https://discord.com/channels/{guild_id}/{channel_id}/{message_id}"

                # Send the message
                await event.message.respond(response_message)
            # Otherwise, add the approximate hash to the database
            else:
                c.execute(
                    "INSERT INTO image_hashes (hash, message_id, channel_id, guild_id) VALUES (?, ?, ?, ?)",
                    (
                        str(image_hash),
                        event.message_id,
                        event.channel_id,
                        event.guild_id,
                    ),
                )
                db.commit()


def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)
