import sys, pathlib

if __name__ == "__main__":
    sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

import unittest
from commons.wordle import BasicWordle, Tile  # adjust import path


class TestBasicWordle(unittest.TestCase):
    def setUp(self):
        self.uid = 1
        self.game = BasicWordle(day="t", target_word="tartan")

    def test_win_first_try(self):
        """Guessing the solution in round 1 sets won/over and scores correctly"""
        self.game.guess("tartan", self.uid)
        self.assertTrue(self.game.won)
        self.assertTrue(self.game.over)
        self.assertEqual(len(self.game.past_guesses), 1)
        self.assertEqual(self.game.score_board[self.uid], 12)  # 3 tiles × 2 pts

    def test_keyboard_not_present(self):
        """Letters absent from the solution become NOT_PRESENT on the keyboard"""
        self.game.guess("xyzqml", self.uid)
        for ch in "xyzqml":
            self.assertEqual(self.game.keyboard[ch], Tile.NOT_PRESENT)


class TestBasicWordleScoreWin(unittest.TestCase):
    def setUp(self):
        self.uid = 1
        self.game = BasicWordle(day="t", target_word="pepper")

    def test_scores(self):
        """Guessing the solution over 4 rounds sets won/over and scores correctly"""
        self.game.guess("couple", self.uid)
        self.assertFalse(self.game.won)
        self.assertFalse(self.game.over)
        self.assertEqual(len(self.game.past_guesses), 1)
        self.assertEqual(self.game.score_board[self.uid], 3)

        self.game.guess("abides", self.uid)
        self.assertFalse(self.game.won)
        self.assertFalse(self.game.over)
        self.assertEqual(len(self.game.past_guesses), 2)
        self.assertEqual(self.game.score_board[self.uid], 4)

        self.game.guess("temper", self.uid)
        self.assertFalse(self.game.won)
        self.assertFalse(self.game.over)
        self.assertEqual(len(self.game.past_guesses), 3)
        self.assertEqual(self.game.score_board[self.uid], 8)

        self.game.guess("pepper", self.uid)
        self.assertTrue(self.game.won)
        self.assertTrue(self.game.over)
        self.assertEqual(len(self.game.past_guesses), 4)
        self.assertEqual(self.game.score_board[self.uid], 12)


class TestBasicWordleScoreWin2(unittest.TestCase):
    def setUp(self):
        self.uid = 1
        self.game = BasicWordle(day="t", target_word="tartan")

    def test_scores(self):
        """Guessing the solution and scores correctly"""
        self.game.guess("bought", self.uid)
        self.assertFalse(self.game.won)
        self.assertFalse(self.game.over)
        self.assertEqual(len(self.game.past_guesses), 1)
        self.assertEqual(self.game.score_board[self.uid], 1)

        self.game.guess("strafe", self.uid)
        self.assertFalse(self.game.won)
        self.assertFalse(self.game.over)
        self.assertEqual(len(self.game.past_guesses), 2)
        self.assertEqual(self.game.score_board[self.uid], 4)

        self.game.guess("pirate", self.uid)
        self.assertFalse(self.game.won)
        self.assertFalse(self.game.over)
        self.assertEqual(len(self.game.past_guesses), 3)
        self.assertEqual(self.game.score_board[self.uid], 4)

        self.game.guess("martyr", self.uid)
        self.assertFalse(self.game.won)
        self.assertFalse(self.game.over)
        self.assertEqual(len(self.game.past_guesses), 4)
        self.assertEqual(self.game.score_board[self.uid], 6)

        self.game.guess("tartan", self.uid)
        self.assertTrue(self.game.won)
        self.assertTrue(self.game.over)
        self.assertEqual(len(self.game.past_guesses), 5)
        self.assertEqual(self.game.score_board[self.uid], 12)


class TestBasicWordleRepeatGuessSameScore(unittest.TestCase):
    def setUp(self):
        self.uid = 1
        self.game = BasicWordle(day="t", target_word="tartan")

    def test_scores(self):
        """Checking that repeated words do not alter the score"""
        self.game.guess("estate", self.uid)
        self.assertFalse(self.game.won)
        self.assertFalse(self.game.over)
        self.assertEqual(len(self.game.past_guesses), 1)
        self.assertEqual(self.game.score_board[self.uid], 3)

        self.game.guess("estate", self.uid)
        self.assertFalse(self.game.won)
        self.assertFalse(self.game.over)
        self.assertEqual(len(self.game.past_guesses), 2)
        self.assertEqual(self.game.score_board[self.uid], 3)

        self.game.guess("player", self.uid)
        self.assertFalse(self.game.won)
        self.assertFalse(self.game.over)
        self.assertEqual(len(self.game.past_guesses), 3)
        self.assertEqual(self.game.score_board[self.uid], 4)

        self.game.guess("player", self.uid)
        self.assertFalse(self.game.won)
        self.assertFalse(self.game.over)
        self.assertEqual(len(self.game.past_guesses), 4)
        self.assertEqual(self.game.score_board[self.uid], 4)


class TestBasicWordleScoreLoss(unittest.TestCase):
    def setUp(self):
        self.uid = 1
        self.game = BasicWordle(day="t", target_word="pepper", rounds=4)

    def test_scores(self):
        """Failing to guess the solution over 4 rounds sets won/over and scores correctly"""
        self.game.guess("couple", self.uid)
        self.assertFalse(self.game.won)
        self.assertFalse(self.game.over)
        self.assertEqual(len(self.game.past_guesses), 1)
        self.assertEqual(self.game.score_board[self.uid], 3)

        self.game.guess("abides", self.uid)
        self.assertFalse(self.game.won)
        self.assertFalse(self.game.over)
        self.assertEqual(len(self.game.past_guesses), 2)
        self.assertEqual(self.game.score_board[self.uid], 4)

        self.game.guess("temper", self.uid)
        self.assertFalse(self.game.won)
        self.assertFalse(self.game.over)
        self.assertEqual(len(self.game.past_guesses), 3)
        self.assertEqual(self.game.score_board[self.uid], 8)

        self.game.guess("capers", self.uid)
        self.assertFalse(self.game.won)
        self.assertTrue(self.game.over)
        self.assertEqual(len(self.game.past_guesses), 4)
        self.assertEqual(self.game.score_board[self.uid], 10)


class TestDuplicateLetters(unittest.TestCase):
    """Scoring & keyboard when the guess contains repeated letters."""

    UID = 9

    def setUp(self):
        self.game = BasicWordle(day="dup", target_word="letter")  # l e t t e r

    def test_duplicate_handling(self):
        # guess has 1 green l, 1 green e, 1 orange e, three excess e's → 5 pts total
        self.game.guess("leeexe", self.UID)
        self.assertEqual(self.game.score_board[self.UID], 5)

        # keyboard: l/e GREEN, t MISPLACED (not guessed), r DEFAULT, x NOT_PRESENT
        self.assertEqual(self.game.keyboard["l"], Tile.CORRECT)
        self.assertEqual(self.game.keyboard["e"], Tile.CORRECT)
        self.assertEqual(self.game.keyboard["t"], Tile.DEFAULT)
        self.assertEqual(self.game.keyboard["x"], Tile.NOT_PRESENT)


class TestMultipleUsers(unittest.TestCase):
    """Game keeps independent scores per user."""

    def test_two_players(self):
        g = BasicWordle(day="multi", target_word="planet")

        g.guess("planes", 1)  # user 1 wins immediately (12 pts)
        g.guess("planet", 2)  # user 2 first guess (5 pts)

        self.assertTrue(g.won)
        self.assertEqual(g.score_board[1], 10)
        self.assertEqual(g.score_board[2], 2)
        self.assertEqual(g.keyboard["p"], Tile.CORRECT)  # still green for everyone


class TestKeyboardUpdates(unittest.TestCase):
    """Keyboard should show MISPLACED / CORRECT but never downgrade."""

    UID = 42

    def setUp(self):
        self.game = BasicWordle(day="d1", target_word="planet")  # 6-letter target

    # ── helpers ───────────────────────────────────────────────
    def guess_and_assert(self, guess: str, expectations: dict[str, Tile]):
        self.game.guess(guess, self.UID)
        for ch, expected in expectations.items():
            self.assertEqual(
                self.game.keyboard[ch],
                expected,
                msg=f"letter {ch!r} expected {expected}, got {self.game.keyboard[ch]}",
            )

    # ── tests ────────────────────────────────────────────────
    def test_keyboard_marks_present_misplaced(self):
        """
        n,a,p,l are in 'planet' but wrong spots → MISPLACED
        e is green; s absent.
        """
        self.guess_and_assert(
            "naples",
            {
                "n": Tile.MISPLACED,
                "a": Tile.MISPLACED,
                "p": Tile.MISPLACED,
                "l": Tile.MISPLACED,
                "e": Tile.CORRECT,
                "s": Tile.NOT_PRESENT,
            },
        )

    def test_keyboard_never_downgrades_green(self):
        """
        p starts orange, later flips to green; keyboard must stay GREEN.
        """
        self.game.guess("appppp", self.UID)  # first: p MISPLACED
        self.assertEqual(self.game.keyboard["p"], Tile.MISPLACED)

        self.game.guess("planet", self.UID)  # now p GREEN
        self.assertEqual(self.game.keyboard["p"], Tile.CORRECT)

        # make another guess without p – keyboard must remain GREEN
        self.game.guess("abcdef", self.UID)
        self.assertEqual(self.game.keyboard["p"], Tile.CORRECT)


if __name__ == "__main__":
    unittest.main()
