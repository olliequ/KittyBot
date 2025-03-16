import os
from typing import Sequence

import hikari
import hikari.errors
from PIL import Image
import imagehash
import behaviours
import db
import re
import requests
import io

phash_th = "PHASH_TH"
chash_th = "CHASH_TH"
HASH_SIZE = 16

_Results = Sequence[tuple[int, hikari.Snowflake, hikari.Snowflake, hikari.Snowflake]]

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
        file_name_match = re.search(r"\.(\w+)$", file_name)
        if not file_name_match:
            continue
        file_extension = file_name_match.group(1)
        image_file_extensions = ["bmp", "gif", "jpg", "jpeg", "png", "tiff", "webp"]
        if file_extension in image_file_extensions:
            # Calculate the approximate hash of the image
            # Download the file from the specified URL
            response = requests.get(attachment.url)

            # Create a memory buffer
            file_buffer = io.BytesIO(response.content)
            image = Image.open(file_buffer)
            image_hash = imagehash.phash(image, HASH_SIZE)
            image = Image.open(file_buffer)
            hash_color = imagehash.colorhash(image, HASH_SIZE)
            # Check if the approximate hash exists in the database
            c.execute(
                """
                SELECT rowid, message_id, channel_id, guild_id
                FROM image_hashes
                WHERE hammingDistance(hash, ?) < ?
                    AND hammingDistanceColor(hash_color, ?) < ?
                ORDER BY rowid ASC""",
                (
                    str(image_hash),
                    int(os.getenv(phash_th, "50")),
                    str(hash_color),
                    int(os.getenv(chash_th, "50")),
                ),
            )

            results: _Results = c.fetchall()
            valid_results: _Results = []
            for result in results:
                # We have a match in the database, but we need to verify that message has not been since deleted
                row_id = result[0]
                message_id = result[1]
                channel_id = result[2]
                try:
                    await event.app.rest.fetch_message(channel_id, message_id)

                except hikari.errors.NotFoundError:
                    c.execute(
                        """
                        DELETE FROM image_hashes
                        WHERE rowid = ?""",
                        (row_id,),
                    )
                else:
                    valid_results.append(result)

            # Always store the current hash, because:
            # a) similarity is not necessarily transitive
            # b) the first could be deleted, so this message becomes the only record of it
            # Do this before sending the response so network errors do not prevent us getting to a db commit.
            c.execute(
                """
                INSERT INTO image_hashes
                (hash, hash_color, message_id, channel_id, guild_id)
                VALUES (?, ?, ?, ?, ?)""",
                (
                    str(image_hash),
                    str(hash_color),
                    event.message_id,
                    event.channel_id,
                    event.guild_id,
                ),
            )
            db.commit()

            if len(valid_results) > 0:
                # OK, message is actually a duplicate of an existing one
                message_id = valid_results[0][1]
                channel_id = valid_results[0][2]
                guild_id = valid_results[0][3]
                response_message = f"Hey {event.author.mention}! Your image has seemingly already been posted before. Time to strive for more originality? <:kermitsippy:1019863020295442533>\n\nIt was first posted here: https://discord.com/channels/{guild_id}/{channel_id}/{message_id}"
                await event.message.respond(response_message)
                raise behaviours.EndProcessing()


def load() -> None:
    def hammingDistance(a: str, b: str):
        return imagehash.hex_to_hash(a) - imagehash.hex_to_hash(b)
    db.create_function("hammingDistance", 2, hammingDistance)

    def hammingDistanceColor(a: str, b: str):
        return imagehash.hex_to_flathash(a, HASH_SIZE) - imagehash.hex_to_flathash(b, HASH_SIZE)
    db.create_function("hammingDistanceColor", 2, hammingDistanceColor)
