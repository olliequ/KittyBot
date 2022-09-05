# KittiBot - a sentient Discord bot!

## Current Functionality
- Automatically assigns the `#NotALurker` role to members who qualify for it (previously mods had to manually assign it).
- Answers questions targeted to her with a magic 8 ball response.
- `/fact` command: Returns a random fact // common misconception.
- `/fortune` command: Returns a random fortune. Beware!
- `/advice` command: Returns a piece of life advice :)
- `/emojistats` command: Returns information regarding how often a specified user has used a specific emoji.
- `/userinfo` command: This command returns interesting information about a specified user (specified through the `target` option field). If no member is specified, the command returns info of whoever issued the command. There's also a `type` option field which has 2 choices:
  1) `general`: Returns an embed containing general information such as account creation date, server join date etc.
  2) `emoji`: Returns an embed of the top 5 used emojis of the user, their total messages, and what 'rank' they are in terms of total messages sent.
  - If no option is specified, the `emoji` type is chosen by default. 
- `/messageboard` command: Returns a bar graph of the top 10 users in terms of all-time total messages sent. There's a `type` option field which has 3 graph representation types to choose from:
  1) `lightmode`: Returns the graph (matlibplot image) in a light-mode colour scheme.
  2) `darkmode`: Returns the graph (matlibplot image) in a dark-mode colour scheme.
  3) `native`: Returns of a horizontal block bar chart in native Discord message format.
  - If no option is specified the `lightmode` graph is returned by default.
- `/say` command: Writes a custom text message encapsulated in something rather interesting... 
- `/translate` command: Translates text to and from English. There's 2 option fields. The first is the text, and the second is the language you want to translate into (you write the language code; e.g. `fr` for french). If you don't specify the language code (i.e. leaving this option field blank), then it assumes you want to translate the text you write into English.
- `+ping` command: Kitti returns to you a heartbeat latency message.
- All commands have a 10-second cooldown period (per user), and can be called in slash or prefix command form.
## Key Notes & Repository Information
- Kitti is an open-source, community-powered bot for the `CS@unimelb` Discord server.
- This bot is made using **Hikari** & **Lightbulb**. These are two nice & simple **Python** libraries.
- The docs for these two libraries are https://www.hikari-py.dev/hikari/ & https://hikari-lightbulb.readthedocs.io/en/latest/.
- The following *get-started* guide is very nice if you want to quickly understand how these libraries work: https://neonjonn.readthedocs.io/en/latest/hikari-get-started/lightbulb.html
- **Pull requests are very much accepted (and encouraged!)** if you want to add features to the bot & server :)
- If you want to play around with it, you will need to use your own bot token. You could then invite your own bot (with the token you got) to your own personal server and play around with it there for testing (this is all in the above guide) :)
- You can install the required dependencies (listed in `requirements.txt`) using the command `pip install -r requirements.txt`.
- For readability purposes, if you want to add a function/command, **please write it in a new python file placed in the** `extensions` **folder** -- just like the `userinfo` and `fortune` commands are.
- **Important**: If you want to develop/contribute/test/play-around, you will need to create a `.env` file and inside it add your bot token (as explained in the guide), and the '_default guild_' IDs. It will need to be like: `BOT_TOKEN = 123456` and `DEFAULT_GUILDS = 123456,56789` (comma-seperated list). Specifying guild IDs in `.env` is **not** neccessary, and actually the act of specifying certain IDs to it (can be many guilds) means that slash commands will only be available in those guilds. The benefit of specifying default guilds is that the slash commands become available **instantly** in those servers, which is good for testing purposes. Note: 'guild' means Discord server. 
 - So, to be clear, your `.env` file should be located in the top layer of the repository (same level as `bot.py` and `requirements.txt`) and could look like this:
```
BOT_TOKEN = 123456 # Your bot’s token from the Discord Developer Portal.
DEFAULT_GUILDS = 123456,56789 # The 'default guilds' -- these instantly load slash comamands. Can be empty.
FORTUNE_DIRECTORY=/usr/share/games/fortunes # Location of where fortunes is installed on your machine.
```
- The `/fortune` command requires the `fortunes` package to be installed and pointed to by the `FORTUNE_DIRECTORY` variable in `.env`. 
  - If you're on Linux you can install `fortunes` with `sudo apt-get install -y fortune` and in `.env` set `FORTUNE_DIRECTORY=/usr/share/games/fortunes`
  - If you're on macOS you can install `fortunes` with `brew install fortune` and in `.env` set `FORTUNE_DIRECTORY=/usr/local/Cellar/fortune/9708/share/games/fortunes`
  - I don't have Windows so if you develop on Windows you'll have to find how to download the `fortunes` package yourself. If you can't find it it's fine, it just means the `+fortune` command won't work during testing (but everything else should).
  - You may optionally white-list and black-list database files by setting `FORTUNE_WHITELIST` and/or `FORTUNE_BLACKLIST` to a space-separated list of database file names.
- The bot can grant a role to members when they first send a text message. Conventionally, this role is called `#NotALurker`. To enable this feature the `NOTALURKER_ROLE` parameter in `.env` must be set to the role ID to grant. The bot's role must be higher than this role to have permission to grant it.
- The bot is deployed on a cloud server (droplet on Digital Ocean) which runs Ubuntu 20.04. 

## Further Ideas // Ways to Contribute
- Resolve outstanding issues noted in `Issues`.
- Perhaps a unimelb-handbook webscraping related command? The repo already uses a webscraper (`BeautifulSoup`) you could use!
- Greeting new people when they join the server in `#general`.
- Getting Kitti to reply to someone if they thank Kitti (e.g.: `Thanks @Kitti!` ... `You're welcome @____ 🐱`).
- Add programming/CS related facts to the fact 'database'. The database is currently a list of strings whereby each string is a fact/common-misconception scraped from a Wikipedia page.
- Implement some sort of natural language processing thing (neural network?) that does something to do with text analysis (e.g. off a message that someone sends). This is some next level stuff, but hey, if there's an interest then why not? 😃
- Implement a creative command you have of your own!

## Legal
This software distributes the Noto Emoji font, under the terms of the SIL Open Font License. See `fonts/OFL.txt` for details.
