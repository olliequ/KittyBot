# KittyBot - a sentient Discord bot!
## Key Notes
- An open-source, community-powered bot for the `CS@unimelb` Discord server.
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
- The `+fortune` command requires the `fortunes` package to be installed and pointed to by the `FORTUNE_DIRECTORY` variable in `.env`. 
  - If you're on Linux you can install `fortunes` with `sudo apt-get install -y fortune` and in `.env` set `FORTUNE_DIRECTORY=/usr/share/games/fortunes`
  - If you're on macOS you can install `fortunes` with `brew install fortune` and in `.env` set `FORTUNE_DIRECTORY=/usr/local/Cellar/fortune/9708/share/games/fortunes`
  - I don't have Windows so if you develop on Windows you'll have to find how to download the `fortunes` package yourself. If you can't find it it's fine, it just means the `+fortune` command won't work during testing (but everything else should).
  - You may optionally white-list and black-list database files by setting `FORTUNE_WHITELIST` and/or `FORTUNE_BLACKLIST` to a space-separated list of database file names.
- The bot is deployed on a cloud server (droplet on Digital Ocean) which runs Ubuntu 20.04. 

## Current Functionality
- Automatically assigns the `#NotALurker` role to members who qualify for it (previously mods had to manually assign it).
- `+ping` command: Kitti returns to you a heartbeat latency message.
- `+numberadder` command: Takes 2 numbers as input and returns the sum of them.
- `+fact` command: Returns a random fact // common misconception.
- `+fortune` command: Returns a random fortune. Beware!
- `+userinfo` command: Returns an embed containing useful information of a specified member of the server. If no member is specified, it returns that of the user who issued the command.
- All commands have a 10-second cooldown period (per user), and can also be called in slash command form.

## Further Ideas // Ways to Contribute
- Resolve outstanding issues noted in `Issues`.
- Perhaps a unimelb-handbook webscraping related command? The repo already uses a webscraper (`BeautifulSoup`) you could use!
- Greeting new people when they join the server in `#general`.
- Getting Kitti to reply to someone if they thank Kitti (e.g.: `Thanks @Kitti!` ... `You're welcome @____ 🐱`).
- Add programming/CS related facts to the fact 'database'. The database is currently a list of strings whereby each string is a fact/common-misconception scraped from a Wikipedia page.
- Implement some sort of natural language processing thing (neural network?) that does something to do with text analysis (e.g. off a message that someone sends). This is some next level stuff, but hey, if there's an interest then why not? 😃
- Implement a creative command you have of your own!
