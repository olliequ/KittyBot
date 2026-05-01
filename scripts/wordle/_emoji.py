import hikari, lightbulb
import os
import dotenv
import json

dotenv.load_dotenv()

APPLICATION_ID = 1015897978327810069  # change

bot = lightbulb.BotApp(
    os.environ["BOT_TOKEN"],
    prefix="+",
    banner=None,
    intents=hikari.Intents.ALL,
    default_enabled_guilds=tuple(
        int(v) for v in os.environ["DEFAULT_GUILDS"].split(",")
    ),
)

EMOJI_DIR = "./wordle_icons"


@bot.listen()
async def on_started(_: hikari.StartedEvent) -> None:
    emoji = None
    for fname in os.listdir(EMOJI_DIR):
        if not fname.lower().endswith((".png", ".jpg", ".jpeg", ".gif")):
            continue  # skip non-image files
        path = os.path.join(EMOJI_DIR, fname)
        emoji_name = os.path.splitext(fname)[0][:32]  # 2–32 chars
        print(emoji_name)

        emoji = await bot.rest.create_application_emoji(
            APPLICATION_ID,
            name=emoji_name,
            image=hikari.File(path),
        )
    if emoji:
        print(f"added :{emoji.name}: → {emoji.id}")
    app_emojis = await bot.rest.fetch_application_emojis(APPLICATION_ID)
    with open("wordle_emoji_map.json", "w") as file:
        emojis = {}
        for emoji in app_emojis:
            print(emoji.id, emoji.name)
            emojis[emoji.name] = emoji.id
        json.dump(emojis, file, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    bot.run()
