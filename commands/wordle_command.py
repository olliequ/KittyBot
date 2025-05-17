from datetime import datetime
import hikari, lightbulb
from commons.wordle import BasicWordle, load_words
import random
import os


plugin = lightbulb.Plugin("Kitti Co-op Wordle")

VALID_GUESS_WORDS, VALID_SOLUTION_WORDS = load_words()
WORDLE_CACHE: dict[str, BasicWordle] = {}
WORDLE_ATTEMPT_COOLDOWN = 600
WORDLE_SOLUTION_WORD_LENGTH = 6


@plugin.command
@lightbulb.add_cooldown(
    (
        WORDLE_ATTEMPT_COOLDOWN
        if not os.environ.get("DEBUG", "false") in ("true", "1")
        else 1
    ),
    1,
    lightbulb.UserBucket,
)
@lightbulb.option(
    "attempt",
    "What is it?",
    required=True,
    min_length=WORDLE_SOLUTION_WORD_LENGTH,
    max_length=WORDLE_SOLUTION_WORD_LENGTH,
    type="string",
)
@lightbulb.command("wordle", "Co-op wordle.")
@lightbulb.implements(lightbulb.SlashCommand, lightbulb.PrefixCommand)
async def main(ctx: lightbulb.Context) -> None:
    guess = ctx.options.attempt.lower()
    if len(guess) != WORDLE_SOLUTION_WORD_LENGTH:
        await ctx.respond(f"Guess needs to be {WORDLE_SOLUTION_WORD_LENGTH} chars long")
        return
    day = datetime.today().strftime("%Y-%m-%d")
    # init game...
    # todo: more principled solution than global state
    try:
        current_game = WORDLE_CACHE[day]
    except KeyError:
        WORDLE_CACHE.clear()
        current_target_word = random.choice(VALID_SOLUTION_WORDS)
        print(current_target_word)
        WORDLE_CACHE[day] = BasicWordle(
            rounds=9, target_word=current_target_word, day=day
        )
        current_game = WORDLE_CACHE[day]

    if not guess.isascii() or not guess.isalpha():
        await ctx.respond(
            "Co-ordle guesses must consist only of ASCII alphabetic characters."
        )
        return
    if guess not in VALID_GUESS_WORDS:
        await ctx.respond("Not a valid word for a guess!")
        return
    user = ctx.member
    if user is None:
        await ctx.respond("No user ID for some reason!")
        return
    # play
    if current_game.over:
        # game is either won or failed, render the state that it ended at
        # split up the two game string outputs to reduce risk of Discord embed field char limit error
        game_render, keyboard_render = current_game.render()
    else:
        current_game.guess(guess, user.id)
        game_render, keyboard_render = current_game.render()

    embed = hikari.Embed(
        title=f"{day}'s Kitti Co-ordle",
        colour=0x3B9DFF if not current_game.won else 0x36D40F,
        timestamp=datetime.now().astimezone(),
        description=game_render,
    ).add_field(
        name="Letters:",
        value=keyboard_render,
        inline=False,
    )
    await ctx.respond(embed)

    # todo: remove this after testing
    if current_game.over and os.environ.get("DEBUG", "false") in ("true", "1"):
        WORDLE_CACHE.clear()


def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)
