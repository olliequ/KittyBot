import sqlite3

def cursor():
    return conn.cursor()

def commit():
    conn.commit()

def start():
    c = cursor()
    c.execute("CREATE TABLE IF NOT EXISTS emoji_counts (user TEXT, emoji TEXT, count INTEGER)");
    c.execute("CREATE UNIQUE INDEX IF NOT EXISTS emoji_counts_idx ON emoji_counts (user, emoji)");
    c.execute("CREATE TABLE IF NOT EXISTS message_counts (user TEXT, count INTEGER)");
    c.execute("CREATE UNIQUE INDEX IF NOT EXISTS message_counts_idx ON message_counts (user)");

conn = sqlite3.connect('persist.sqlite')
start()

