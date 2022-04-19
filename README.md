# KittyBot
- A bot for the CS@unimelb Discord server.
- This bot is made using **Hikari** & **Lightbulb**. These are 2 nice & simple **Python** libraries.
- The docs for these 2 libraries are https://www.hikari-py.dev/hikari/ & https://hikari-lightbulb.readthedocs.io/en/latest/.
- The following *get-started* guide is very nice if you want to quickly understand how these libraries work: https://neonjonn.readthedocs.io/en/latest/hikari-get-started/lightbulb.html
- Pull requests are very much accepted if you want to add features to the bot & server!
- If you want to play around with it, you will need to use your own bot token. You could then invite your own bot (with the token you got) to your own personal server and play around with it there for testing (this is all in the above guide) :)
- Important: You will need to create a `.env` file and inside it add your bot token (as explained in the guide), and the 'default guild' IDs. It will need to be like: `BOT_TOKEN = 123456` and `DEFAULT_GUILDS = 123456,56789` (comma-seperated list). Specifying the guild ID to the bot isn't neccessary, but specifying certain IDs to it (can be many guilds) means that slash commands will only appear in those guild(s). Btw, 'guild' means a Discord server. 
- For readability purposes, if you want to add an extensive function, please write it in a new python file placed in the `extensions` folder -- just like the `userinfo` and `fortune` commands are.
- You can install the required dependencies (listed in `requirements.txt`) using the command `pip install -r requirements.txt`.
- The `fortune` command requires the fortune files to be installed and pointed to by the `FORTUNE_DIRECTORY` variable in `.env`. 
  - If you're on Linux you can install `fortunes` with `sudo apt-get install -y fortune` and in `.env` set `FORTUNE_DIRECTORY=/usr/share/games/fortunes`
  - If you're on macOS you can install `fortunes` with `brew install fortune` and in `.env` set `FORTUNE_DIRECTORY=/usr/local/Cellar/fortune/9708/share/games/fortunes`
  - You may optionally white-list and black-list database files by setting `FORTUNE_WHITELIST` and/or `FORTUNE_BLACKLIST` to a space-separates list of database file names.

## Further ideas
- Perhaps a unimelb-handbook web-scraping related command? The repo already uses a webscraper (BeautifulSoup) you could use!
