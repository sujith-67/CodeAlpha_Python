"""Unit tests for the Hangman game logic and dictionary system."""

import unittest
from src.game_logic import (
    BASE_POINTS,
    BONUS_PER_ATTEMPT,
    HINT_PENALTY,
    WORD_BANK,
    GameLogic,
)


class TestWordBankAndDifficulties(unittest.TestCase):
    """Test word bank constraints and difficulty tiers."""

    def test_word_bank_not_empty(self):
        """Ensure all difficulty tiers contain sufficient words."""
        for diff in ("easy", "medium", "hard"):
            self.assertIn(diff, WORD_BANK)
            self.assertGreaterEqual(len(WORD_BANK[diff]), 20)

    def test_easy_word_lengths(self):
        """Easy words must have 4 to 5 letters."""
        for entry in WORD_BANK["easy"]:
            word = entry["word"]
            self.assertTrue(
                4 <= len(word) <= 5,
                f"Easy word '{word}' length ({len(word)}) not in 4-5 range",
            )
            self.assertTrue(word.isalpha() and word.isascii())
            self.assertTrue(len(entry["hint"]) > 5)

    def test_medium_word_lengths(self):
        """Medium words must have 6 to 8 letters."""
        for entry in WORD_BANK["medium"]:
            word = entry["word"]
            self.assertTrue(
                6 <= len(word) <= 8,
                f"Medium word '{word}' length ({len(word)}) not in 6-8 range",
            )
            self.assertTrue(word.isalpha() and word.isascii())
            self.assertTrue(len(entry["hint"]) > 5)

    def test_hard_word_lengths(self):
        """Hard words must have 9 or more letters."""
        for entry in WORD_BANK["hard"]:
            word = entry["word"]
            self.assertGreaterEqual(
                len(word),
                9,
                f"Hard word '{word}' length ({len(word)}) less than 9",
            )
            self.assertTrue(word.isalpha() and word.isascii())
            self.assertTrue(len(entry["hint"]) > 5)


class TestGameLogicMechanics(unittest.TestCase):
    """Test game logic mechanics, guesses, scoring, and win/loss states."""

    def setUp(self):
        self.game = GameLogic(difficulty="easy")

    def test_initial_state(self):
        """Verify initial values after game start."""
        self.assertEqual(self.game.attempts_left, 6)
        self.assertEqual(self.game.max_attempts, 6)
        self.assertFalse(self.game.game_over)
        self.assertFalse(self.game.is_won)
        self.assertFalse(self.game.hint_used)
        self.assertEqual(len(self.game.guessed_letters), 0)
        self.assertGreater(len(self.game.secret_word), 0)

    def test_no_immediate_word_repeat(self):
        """Word selection should not immediately repeat if other choices exist."""
        first_word = self.game.secret_word
        repeated = False
        # Test 10 consecutive new game calls
        for _ in range(10):
            self.game.start_new_game(difficulty="easy")
            if self.game.secret_word == first_word:
                repeated = True
            first_word = self.game.secret_word
        self.assertFalse(repeated, "Selected word was immediately repeated")

    def test_correct_guess(self):
        """Correct guess reveals letter and preserves attempts."""
        self.game.secret_word = "code"
        res = self.game.make_guess("c")
        self.assertEqual(res["status"], "correct")
        self.assertEqual(self.game.attempts_left, 6)
        self.assertIn("c", self.game.correct_guesses)
        self.assertIn("c", self.game.guessed_letters)
        self.assertEqual(self.game.get_display_string(), "C _ _ _")

    def test_incorrect_guess(self):
        """Incorrect guess decrements attempts and records letter."""
        self.game.secret_word = "code"
        res = self.game.make_guess("z")
        self.assertEqual(res["status"], "incorrect")
        self.assertEqual(self.game.attempts_left, 5)
        self.assertIn("z", self.game.incorrect_guesses)
        self.assertIn("z", self.game.guessed_letters)

    def test_case_insensitive_guess(self):
        """Uppercase input should be processed correctly."""
        self.game.secret_word = "code"
        res = self.game.make_guess("O")
        self.assertEqual(res["status"], "correct")
        self.assertIn("o", self.game.correct_guesses)

    def test_repeated_guess(self):
        """Repeated guesses are rejected without penalty."""
        self.game.secret_word = "code"
        self.game.make_guess("a")  # Incorrect
        self.assertEqual(self.game.attempts_left, 5)

        repeat_res = self.game.make_guess("a")
        self.assertEqual(repeat_res["status"], "repeated")
        self.assertEqual(self.game.attempts_left, 5)

    def test_invalid_input(self):
        """Non-alphabet, multi-letter, or empty input must be rejected."""
        self.game.secret_word = "code"
        for invalid in ("1", "@", "ab", "", "   ", "!"):
            res = self.game.make_guess(invalid)
            self.assertEqual(res["status"], "invalid")
            self.assertEqual(self.game.attempts_left, 6)

    def test_win_condition(self):
        """Guessing all letters triggers victory."""
        self.game.secret_word = "code"
        for letter in ("c", "o", "d", "e"):
            res = self.game.make_guess(letter)

        self.assertTrue(self.game.is_won)
        self.assertTrue(self.game.game_over)
        self.assertEqual(res["is_won"], True)
        self.assertEqual(res["game_over"], True)
        self.assertEqual(self.game.get_display_string(), "C O D E")

    def test_loss_condition(self):
        """Exhausting 6 attempts triggers game over loss."""
        self.game.secret_word = "code"
        wrongs = ["z", "y", "x", "w", "v", "u"]
        for letter in wrongs:
            res = self.game.make_guess(letter)

        self.assertFalse(self.game.is_won)
        self.assertTrue(self.game.game_over)
        self.assertEqual(self.game.attempts_left, 0)
        self.assertEqual(res["status"], "incorrect")
        self.assertTrue(res["game_over"])

    def test_hint_usage(self):
        """Hint returns string and sets flag."""
        self.assertFalse(self.game.hint_used)
        hint = self.game.use_hint()
        self.assertTrue(self.game.hint_used)
        self.assertEqual(hint, self.game.hint)

    def test_score_calculation(self):
        """Score computes base + bonus - penalty properly."""
        self.game.difficulty = "medium"
        self.game.secret_word = "python"
        self.game.attempts_left = 4
        self.game.is_won = True
        self.game.hint_used = True

        breakdown = self.game.calculate_score_breakdown()
        expected_base = BASE_POINTS["medium"]  # 200
        expected_bonus = 4 * BONUS_PER_ATTEMPT  # 100
        expected_penalty = -HINT_PENALTY  # -30
        expected_total = expected_base + expected_bonus + expected_penalty  # 270

        self.assertEqual(breakdown["base"], expected_base)
        self.assertEqual(breakdown["bonus"], expected_bonus)
        self.assertEqual(breakdown["penalty"], expected_penalty)
        self.assertEqual(breakdown["total"], expected_total)

    def test_score_for_loss(self):
        """Losing gives 0 score."""
        self.game.is_won = False
        breakdown = self.game.calculate_score_breakdown()
        self.assertEqual(breakdown["total"], 0)


if __name__ == "__main__":
    unittest.main()
