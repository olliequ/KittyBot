TESTMODE = __name__ == "__main__"

import sqlite3
from collections import defaultdict, Counter
from pathlib import Path
from typing import Callable, TypedDict
from enum import Enum
import commons.db as db

if not TESTMODE:
    import commons.appemoji as appemoji

ASSETS = Path(__file__).resolve().parent.parent / "assets"  # one level up


def load_words():
    with open(ASSETS / "wordle_valid_words.txt") as f:
        valid_guess_words = f.read().splitlines()
    with open(ASSETS / "wordle_solutions.txt") as f:
        solutions = f.read().splitlines()
    return valid_guess_words, solutions


class FlipCounts(TypedDict):
    green: int
    orange: int
    grey: int


class FlipInfo(TypedDict):
    counts: FlipCounts
    existing_greens: list[int]


def _template() -> FlipInfo:
    return {"counts": {"green": 0, "orange": 0, "grey": 0}, "existing_greens": []}


class Tile(Enum):
    CORRECT = "green"
    MISPLACED = "orange"
    DEFAULT = "grey"
    NOT_PRESENT = "black"


# map each colour to a wrapper for the letter if the emoji map is not present
# let's you also play a version of this in a terminal for debugging
text_annotations: dict[Tile, Callable[[str], str]] = {
    Tile.MISPLACED: lambda c: f"{{{c}}}",  # {t}
    Tile.CORRECT: lambda c: f"[{c}]",  # [r]
    Tile.NOT_PRESENT: lambda c: f"#{c}#",  # #n#
    Tile.DEFAULT: lambda c: f"({c})",  # (e)
}


def letter_repr(letter: str, kind: Tile):
    if TESTMODE:
        return text_annotations[kind](letter)
    if letter == " ":
        letter = "sp"
    return appemoji.get(  # pyright: ignore [reportPossiblyUnboundVariable]
        f"{kind.value}_{letter}"
    ).mention


class BasicWordle:
    """
    A basic wordle game.
    """

    def __init__(
        self,
        *,
        day: str,
        target_word: str,
        rounds: int = 9,
    ):
        self.max_rounds = rounds
        self.day = day
        # store the solution for convenience
        self.target_word = target_word
        # holds scores by user id, for convenience
        self.score_board: defaultdict[int, int] = defaultdict(int)
        # list of all the past guesses
        self.past_guesses: list[tuple[list[tuple[int, str, Tile, int]], int]] = []
        # wordle keyboard
        self.keyboard: defaultdict[str, Tile] = defaultdict(lambda: Tile.DEFAULT)
        # scoring bookkeeping
        self.flips: defaultdict[str, FlipInfo] = defaultdict(_template)
        # initial letter flip possibilities
        for letter in self.target_word:
            self.flips[letter]["counts"]["grey"] += 1
        # initial current guess with placeholder data
        self.current_guess: list[tuple[int, str, Tile, int]] = [
            (0, "", Tile.DEFAULT, 0)
        ] * len(self.target_word)
        self.round = 0
        self.won = False
        self.over = False
        self.keyboard[" "] = Tile.NOT_PRESENT
        self.start_round(is_first_round=True)

    def _track_flips_score(
        self, *, ch: str, is_exact: bool, remaining: Counter[str], idx: int
    ) -> int:
        """
        Update flips + remaining and return score for this tile.
        - Exact match  : 2 pts first-time, 1 pt when flipping an orange → green,
                         0 pt when all flips already green.
        - Mis-placed   : 1 pt first-time orange, 0 pt otherwise.
        - Excess letter: 0 pt.
        """
        info = self.flips[ch]["counts"]
        greens = self.flips[ch]["existing_greens"]  # always a list now
        # exact position (GREEN)
        if is_exact:
            # once we find a correct tile, we never again award points for flipping that specific ch in that idx to green again
            # we also want to avoid incorrectly flipping from orange -> green when it should just be grey -> green and worth 2
            if idx in greens:
                remaining[ch] -= 1
                return 0
            # not a flip, because we map this green one to a previous index that was flipped to green
            if info["orange"] > 0:  # flipped an orange to a green somewhere else
                greens.append(idx)
                info["orange"] -= 1
                info["green"] += 1
                remaining[ch] -= 1
                return 1
            if info["grey"] > 0:  # first discovery and a correct first find
                greens.append(idx)
                info["grey"] -= 1
                info["green"] += 1
                remaining[ch] -= 1
                return 2
            remaining[ch] -= 1  # already flipped earlier
            return 0
        # ── wrong position (ORANGE / BLACK)
        if remaining[ch] == 0:  # excess copies → black
            return 0
        if info["grey"] > 0:  # valid new orange
            info["grey"] -= 1
            info["orange"] += 1
            return 1
        # already had orange/green copies
        return 0

    def start_round(self, is_first_round: bool = False):
        """
        Initialise some things each round / line of the Co-ordle game
        """
        if not is_first_round:
            self.round += 1
        # we're done, and we didn't win
        if self.round >= self.max_rounds:
            self.over = True

    def finish_round(self, id_user: int, guess_word: str):
        """
        Runs at the end of every round after a guess.
        """
        self.score_board[id_user] += self.calculate_round_scores(self.current_guess)
        self.past_guesses.append((self.current_guess, id_user))

        # do some DB stuff for stats or whatever
        cursor: sqlite3.Cursor = db.cursor()
        cursor.execute(
            """insert into
                        wordle_stats
                values (?, ?, ?, ?, ?)""",
            (id_user, self.day, self.round, self.score_board[id_user], guess_word),
        )
        db.commit()

        if self._is_solved():
            self.won = self.over = True
        else:
            # start next round
            self.start_round()

    def calculate_round_scores(self, guess: list[tuple[int, str, Tile, int]]) -> int:
        """
        Calculates scores for a single list of guesses
        """
        return sum([item[3] for item in guess])

    def _is_solved(self):
        """
        Returns True if Co-ordle been solved with all green letters
        """
        for item in self.current_guess:
            if item[2] != Tile.CORRECT:
                return False
        return True

    def _update_keyboard(self, ch: str, is_present: bool, remaining: Counter[str]):
        """Update keyboardDict without ever downgrading a key."""
        current = self.keyboard[ch]
        # once green, always green
        if current is Tile.CORRECT:
            return
        # letter confirmed somewhere → green wins
        if self.flips[ch]["counts"]["green"] > 0:
            self.keyboard[ch] = Tile.CORRECT
            return
        # letter exists but not yet green
        if is_present:
            self.keyboard[ch] = Tile.MISPLACED
            return
        # only set NOT_PRESENT if we’ve never seen it as MISPLACED
        if current is Tile.DEFAULT:
            self.keyboard[ch] = Tile.NOT_PRESENT

    def guess(self, guess: str, id_user: int):
        """
        Attempt and score a guess. Perform bookeeping for things like the
        keyboard used to display possibilities and not present letters etc.
        """
        if self.over:
            self.finish_round(id_user, guess)
        if len(guess) != len(self.target_word):
            return "length of guess is not correct"
        # initialise with some junk data that will be overwritten
        # todo: make this all better
        current_guess = [(-1, "", Tile.DEFAULT, 0)] * len(self.target_word)
        remaining = Counter(self.target_word)
        for idx, ch in enumerate(guess):
            if ch == self.target_word[idx]:
                current_guess[idx] = (
                    idx,
                    ch,
                    Tile.CORRECT,
                    self._track_flips_score(
                        ch=ch, is_exact=True, remaining=remaining, idx=idx
                    ),
                )
                self._update_keyboard(ch, True, remaining)
        # 2. orange / absent (orange / grey)
        for idx, ch in enumerate(guess):
            if current_guess[idx][0] != -1:  # already green
                continue
            if remaining[ch] > 0:  # still unused copy of the letter exists
                current_guess[idx] = (
                    idx,
                    ch,
                    Tile.MISPLACED,
                    (
                        0  # fewer of this specific misplaced char in guess than have been revealed, so don't bother trying to score
                        if guess.count(ch) <= self.flips[ch]["counts"]["orange"]
                        else self._track_flips_score(
                            ch=ch, is_exact=False, remaining=remaining, idx=idx
                        )
                    ),
                )
                remaining[ch] -= 1
                self._update_keyboard(ch, True, remaining)
            else:
                current_guess[idx] = (idx, ch, Tile.NOT_PRESENT, 0)
                self._update_keyboard(ch, False, remaining)
        self.current_guess = current_guess[:]
        self.finish_round(id_user, guess)

    def render(self) -> tuple[str, str]:
        """
        Renders a string including Discord emoji representing the game state
        """
        # current rows
        out_lines: list[str] = []
        total_score_user: defaultdict[int, int] = defaultdict(int)
        for idx, (row, user_id) in enumerate(self.past_guesses):
            emojis = " ".join((letter_repr(guess[1], guess[2])) for guess in row) + " "
            delta = self.calculate_round_scores(row)
            total_score_user[user_id] += delta
            out_lines.append(
                f"{idx}. {emojis} <@{user_id}> - {total_score_user[user_id]} points"
            )

        # render keyboard
        rows = ["qwertyuiop", "asdfghjkl ", " zxcvbnm  "]

        keyboard = "\n".join(
            "".join(
                (letter_repr(ch, self.keyboard.get(ch, Tile.DEFAULT)) for ch in row)
            )
            for row in rows
        )

        # congratulations, now you can't play Wordle until the next day (whenever that is)
        if self.won:
            if self.round == 0:
                out_lines.append(
                    "Very lucky. Everyone who participated gets +10 points. 🌟"
                )
            elif self.round <= 6:
                out_lines.append(
                    "Great job! Everyone who participated gets +2 points. 🎉"
                )
            elif self.round <= 8:
                out_lines.append(
                    "Acceptable job. Everyone who participated gets +2 points. 🎉"
                )
            else:
                out_lines.append(
                    "Okay job. Everyone still gets +2 points for participating. 🎉"
                )
        elif self.over:
            out_lines.append(
                f"You didn't get the word. :(. No points.\nThe word was: **{self.target_word}**"
            )
        out = "\n".join(out_lines)
        return (out, keyboard)


if TESTMODE:
    """
    Basic terminal version for debugging
    """
    target_word = "berate"
    game = BasicWordle(rounds=9, target_word=target_word, day="test")

    is_not_won = True
    while is_not_won:
        guess = input()
        if (len(guess)) != len(target_word):
            print("guess not of correct length")
            continue
        game.guess(guess, 1)
        (board, keys) = game.render()
        print(board)
        print(keys)
        if game.won:
            is_not_won = False
