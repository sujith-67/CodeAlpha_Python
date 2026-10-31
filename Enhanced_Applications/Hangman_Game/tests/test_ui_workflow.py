"""Integration tests exercising the UI, interaction events, screens, and workflows."""

import tempfile
import unittest
from pathlib import Path
import tkinter as tk
import ttkbootstrap as tb

from src.statistics import StatsManager
from src.ui import HangmanCanvas, HangmanUI


class TestUIWorkflow(unittest.TestCase):
    """Test full UI interactions, screen routing, inputs, and state updates."""

    def setUp(self):
        self.root = tb.Window(themename="nord-dark")
        self.root.withdraw()  # Offscreen for automated test execution
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_stats_file = Path(self.temp_dir.name) / "test_stats.json"

        self.ui = HangmanUI(self.root)
        # Override stats manager with temporary path
        self.ui.stats_manager = StatsManager(filepath=self.test_stats_file)
        self.root.update()

    def tearDown(self):
        try:
            self.root.destroy()
        except Exception:
            pass
        self.temp_dir.cleanup()

    def test_welcome_screen_initialization(self):
        """Welcome screen should be displayed on startup."""
        self.assertEqual(self.ui.welcome_frame.winfo_manager(), "pack")
        self.assertEqual(self.ui.game_frame.winfo_manager(), "")

    def test_all_difficulty_levels_selection(self):
        """Switching difficulty selection updates game logic upon round start."""
        for diff in ("easy", "medium", "hard"):
            self.ui.selected_difficulty.set(diff)
            self.ui.show_gameplay_screen()
            self.assertEqual(self.ui.game.difficulty, diff)
            if diff == "easy":
                self.assertTrue(4 <= len(self.ui.game.secret_word) <= 5)
            elif diff == "medium":
                self.assertTrue(6 <= len(self.ui.game.secret_word) <= 8)
            elif diff == "hard":
                self.assertGreaterEqual(len(self.ui.game.secret_word), 9)

    def test_screen_navigation_to_game_and_home(self):
        """Navigation between Welcome and Game views toggles packed frames."""
        self.ui.show_gameplay_screen()
        self.assertEqual(self.ui.game_frame.winfo_manager(), "pack")
        self.assertEqual(self.ui.welcome_frame.winfo_manager(), "")

        self.ui.show_welcome_screen()
        self.assertEqual(self.ui.welcome_frame.winfo_manager(), "pack")
        self.assertEqual(self.ui.game_frame.winfo_manager(), "")

    def test_button_guess_correct_and_incorrect(self):
        """Guessing via button updates alphabet state, attempts, and word slots."""
        self.ui.show_gameplay_screen()
        self.ui.game.secret_word = "laptop"
        self.ui._render_word_slots()

        # Correct guess: 'l'
        self.ui._handle_guess("l")
        self.assertIn("l", self.ui.game.correct_guesses)
        self.assertEqual(str(self.ui.alphabet_buttons["l"].cget("state")), "disabled")
        self.assertEqual(self.ui.game.attempts_left, 6)

        # Incorrect guess: 'z'
        self.ui._handle_guess("z")
        self.assertIn("z", self.ui.game.incorrect_guesses)
        self.assertEqual(str(self.ui.alphabet_buttons["z"].cget("state")), "disabled")
        self.assertEqual(self.ui.game.attempts_left, 5)
        self.assertIn("Z", self.ui.wrong_letters_lbl.cget("text"))

    def test_keyboard_input_event(self):
        """Physical keyboard input event triggers guess correctly."""
        self.ui.show_gameplay_screen()
        self.ui.game.secret_word = "laptop"

        # Simulate keyboard press event for 'a'
        event = tk.Event()
        event.char = "a"
        self.ui._on_key_press(event)

        self.assertIn("a", self.ui.game.correct_guesses)
        self.assertEqual(str(self.ui.alphabet_buttons["a"].cget("state")), "disabled")

    def test_repeated_guess_handling(self):
        """Repeated guesses are ignored and attempts remain untouched."""
        self.ui.show_gameplay_screen()
        self.ui.game.secret_word = "laptop"

        self.ui._handle_guess("x")
        self.assertEqual(self.ui.game.attempts_left, 5)

        # Repeat same letter
        self.ui._handle_guess("x")
        self.assertEqual(self.ui.game.attempts_left, 5)

    def test_hint_usage(self):
        """Clicking hint reveals clue and disables hint button."""
        self.ui.show_gameplay_screen()
        self.assertFalse(self.ui.game.hint_used)

        self.ui._on_hint_clicked()
        self.assertTrue(self.ui.game.hint_used)
        self.assertEqual(str(self.ui.hint_btn.cget("state")), "disabled")
        self.assertIn("Clue:", self.ui.hint_text_lbl.cget("text"))

    def test_winning_condition_and_score(self):
        """Solving all letters displays victory banner and awards score."""
        self.ui.show_gameplay_screen()
        self.ui.game.secret_word = "byte"
        self.ui._render_word_slots()

        for ch in ("b", "y", "t", "e"):
            self.ui._handle_guess(ch)

        self.assertTrue(self.ui.game.is_won)
        self.assertTrue(self.ui.game.game_over)
        self.assertEqual(self.ui.result_banner.winfo_manager(), "pack")

        # Check recorded win in stats
        stats = self.ui.stats_manager.get_stats()
        self.assertEqual(stats["wins"], 1)
        self.assertEqual(stats["total_games"], 1)
        self.assertGreater(stats["total_score"], 0)

    def test_losing_condition_and_reveal(self):
        """Exhausting attempts displays game over banner and reveals answer."""
        self.ui.show_gameplay_screen()
        self.ui.game.secret_word = "byte"

        for ch in ("a", "c", "d", "f", "g", "h"):
            self.ui._handle_guess(ch)

        self.assertFalse(self.ui.game.is_won)
        self.assertTrue(self.ui.game.game_over)
        self.assertEqual(self.ui.game.attempts_left, 0)
        self.assertEqual(self.ui.result_banner.winfo_manager(), "pack")

        stats = self.ui.stats_manager.get_stats()
        self.assertEqual(stats["losses"], 1)
        self.assertEqual(stats["current_streak"], 0)

    def test_play_again_workflow(self):
        """Clicking play again starts fresh round without crashing."""
        self.ui.show_gameplay_screen()
        self.ui.game.secret_word = "byte"
        for ch in ("b", "y", "t", "e"):
            self.ui._handle_guess(ch)

        self.assertTrue(self.ui.game.game_over)

        # Start new round
        self.ui._start_new_round()
        self.assertFalse(self.ui.game.game_over)
        self.assertEqual(self.ui.game.attempts_left, 6)
        self.assertEqual(self.ui.result_banner.winfo_manager(), "")
        self.assertEqual(self.ui.keyboard_card.winfo_manager(), "pack")

    def test_canvas_drawing_stages(self):
        """HangmanCanvas correctly renders progressive mistakes and win scenes."""
        canvas = HangmanCanvas(self.root)
        for mistakes in range(0, 7):
            canvas.render(mistakes=mistakes, is_won=False, is_lost=(mistakes == 6))
            items = canvas.find_all()
            self.assertGreater(len(items), 0)

        # Victory scene
        canvas.render(mistakes=0, is_won=True, is_lost=False)
        items = canvas.find_all()
        self.assertGreater(len(items), 0)


if __name__ == "__main__":
    unittest.main()
