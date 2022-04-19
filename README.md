# KittyBot
- A bot for the CS@unimelb Discord server.
- This bot is made using **Hikari** & **Lightbulb**. These are 2 nice & simple **Python** libraries.
- The docs for these 2 libraries are https://www.hikari-py.dev/hikari/ & https://hikari-lightbulb.readthedocs.io/en/latest/.
- The following *get-started* guide is very nice if you want to quickly understand how these libraries work: https://neonjonn.readthedocs.io/en/latest/hikari-get-started/lightbulb.html
- Pull requests are very much accepted if you want to add features to the bot & server!
- If you want to play around with it, you will need to use your own bot token. You could then invite your own bot (with the token you got) to your own personal server and play around with it there for testing (this is all in the above guide) :)
- For readability purposes, if you want to add an extensive function, please write it in a new python file placed in the `extensions` folder -- just like the `userinfo` command is.
- You can install the required dependencies (listed in `requirements.txt`) using the command `pip install -r requirements.txt`.
- The fortune module requires the fortune files to be installed and pointed to by the FORTUNE_DIRECTORY variable. Generally this means installing the `fortunes` package and setting `FORTUNE_DIRECTORY=/usr/share/games/fortunes`. You may optionally white- and black-list database files by settings FORTUNE_WHITELIST and/or FORTUNE_BLACKLIST to a space-separates list of database file names.
