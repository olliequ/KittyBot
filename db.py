import sqlite3
import os


def cursor():
    return conn.cursor()


def commit():
    conn.commit()


def start():
    c = cursor()
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

    try:
        c.execute("ALTER TABLE image_hashes ADD hash_color TEXT NOT NULL")
        c.execute("ALTER TABLE meme_stats ADD meme_rating INTEGER")
        c.execute("ALTER TABLE meme_stats ADD rating_count INTEGER")
    except Exception as ex:
        pass
    # EmojiCache Table Removed
    c.execute("CREATE TABLE IF NOT EXISTS options (name TEXT, value TEXT)")
    c.execute("CREATE UNIQUE INDEX IF NOT EXISTS options_idx ON options (name)")


def get_option(name: str, default=None):
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


def create_function(name, nargs, fn):
    conn.create_function(name, nargs, fn)


sqlite3.enable_callback_tracebacks(True)
conn = sqlite3.connect(os.environ.get("KITTY_DB", "persist.sqlite"))
start()
