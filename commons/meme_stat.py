import hikari
from dataclasses import dataclass
from typing import Optional
from datetime import datetime
import os
from typing_extensions import Final

MINIMUM_MEME_RATING_TO_NOT_DELETE: Final[int] = int(
    os.environ.get("MEME_QUALITY_THRESHOLD", "6")
)


@dataclass
class MemeStat:
    author_id: Optional[hikari.Snowflake]
    emoji: Optional[str | hikari.Emoji | hikari.UnicodeEmoji | hikari.CustomEmoji]
    meme_rating: Optional[int]
    meme_reasoning: str
    meme_score: int
    message_id: hikari.Snowflake
    rating_count: Optional[int]
    timestamp: Optional[datetime]

    def get_emoji(self) -> hikari.Emoji:
        if self.meme_score >= MINIMUM_MEME_RATING_TO_NOT_DELETE:
            self.emoji = hikari.Emoji.parse("👍")
        self.emoji = hikari.Emoji.parse("💩")
        return self.emoji
