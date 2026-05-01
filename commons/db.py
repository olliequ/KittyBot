import sqlite3
import os
from typing import Callable, overload, Any, Optional

# Reexport type for convenience of module users
Cursor = sqlite3.Cursor


def cursor():
    return conn.cursor()


def commit():
    conn.commit()


def start():
    c = cursor()
    c.execute("CREATE TABLE IF NOT EXISTS wordle (id_game TEXT, target_word TEXT)")
    c.execute(
        "CREATE TABLE IF NOT EXISTS wordle_stats (user TEXT, day TEXT, round INTEGER, round_score INTEGER, guess TEXT)"
    )
    c.execute(
        "CREATE TABLE IF NOT EXISTS emoji_counts (user TEXT, emoji TEXT, count INTEGER)"
    )
    c.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS emoji_counts_idx ON emoji_counts (user, emoji)"
    )
    c.execute("CREATE TABLE IF NOT EXISTS message_counts (user TEXT, count INTEGER)")
    c.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS message_counts_idx ON message_counts (user)"
    )
    c.execute(
        "CREATE TABLE IF NOT EXISTS message_hashes (user TEXT, message_id TEXT, message_hash TEXT, time_sent TEXT)"
    )
    c.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS message_hashes_idx ON message_hashes (message_hash)"
    )
    c.execute(
        "CREATE TABLE IF NOT EXISTS image_hashes (hash TEXT, message_id TEXT, channel_id TEXT, guild_id TEXT)"
    )
    c.execute("CREATE TABLE IF NOT EXISTS message_deletes (user TEXT, count INTEGER)")
    c.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS message_deletes_idx ON message_deletes (user)"
    )
    c.execute(
        "CREATE TABLE IF NOT EXISTS meme_stats (user TEXT, message_id TEXT, meme_score INTEGER, time_sent TEXT)"
    )
    c.execute("CREATE TABLE IF NOT EXISTS shit_meme_deletes (user TEXT, count INTEGER)")
    c.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS shit_meme_deletes_idx ON shit_meme_deletes (user)"
    )

    try:
        c.execute("ALTER TABLE image_hashes ADD hash_color TEXT NOT NULL")
    except Exception:
        pass
    try:
        c.execute("ALTER TABLE meme_stats ADD meme_rating INTEGER")
    except Exception:
        pass
    try:
        c.execute("ALTER TABLE meme_stats ADD rating_count INTEGER")
    except Exception:
        pass
    try:
        c.execute("ALTER TABLE meme_stats ADD meme_reasoning TEXT")
    except Exception:
        pass

    # EmojiCache Table Removed
    c.execute("CREATE TABLE IF NOT EXISTS options (name TEXT, value TEXT)")
    c.execute("CREATE UNIQUE INDEX IF NOT EXISTS options_idx ON options (name)")
    c.execute(
        "CREATE TABLE IF NOT EXISTS scheduled_actions (time INTEGER, action TEXT, arguments TEXT)"
    )


@overload
def get_option(name: str) -> Optional[str]: ...


@overload
def get_option(name: str, default: str) -> str: ...


def get_option(name: str, default: Optional[str] = None) -> Optional[str]:
    res = (
        cursor().execute("select value from options where name = ?", (name,)).fetchone()
    )
    if res is None:
        return default
    return res[0]


def set_option(name: str, value: str):
    cursor().execute(
        "insert into options values(?, ?) on conflict(name) do update set value=excluded.value",
        (name, value),
    )
    commit()


def create_function(name: str, nargs: int, fn: Callable[..., Any]):
    conn.create_function(name, nargs, fn)


sqlite3.enable_callback_tracebacks(True)
conn = sqlite3.connect(os.environ.get("KITTY_DB", "persist.sqlite"))
start()
