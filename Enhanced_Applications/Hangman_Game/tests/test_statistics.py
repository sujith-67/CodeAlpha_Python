"""Unit tests for the Hangman statistics and persistence system."""

import json
import tempfile
import unittest
from pathlib import Path
from src.statistics import DEFAULT_STATS, StatsManager


class TestStatistics(unittest.TestCase):
    """Test statistics persistence, calculation, and recovery."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.stats_file = Path(self.temp_dir.name) / "test_stats.json"
        self.manager = StatsManager(filepath=self.stats_file)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_default_stats_creation(self):
        """New manager creates default stats file."""
        stats = self.manager.get_stats()
        self.assertEqual(stats["total_games"], 0)
        self.assertEqual(stats["wins"], 0)
        self.assertEqual(stats["losses"], 0)
        self.assertEqual(stats["win_percentage"], 0.0)
        self.assertEqual(stats["current_streak"], 0)
        self.assertEqual(stats["best_streak"], 0)
        self.assertEqual(stats["total_score"], 0)
        self.assertTrue(self.stats_file.exists())

    def test_record_win(self):
        """Winning updates games, wins, streaks, score, and percentage."""
        self.manager.record_game(is_won=True, score=250)
        stats = self.manager.get_stats()

        self.assertEqual(stats["total_games"], 1)
        self.assertEqual(stats["wins"], 1)
        self.assertEqual(stats["losses"], 0)
        self.assertEqual(stats["win_percentage"], 100.0)
        self.assertEqual(stats["current_streak"], 1)
        self.assertEqual(stats["best_streak"], 1)
        self.assertEqual(stats["total_score"], 250)
        self.assertEqual(stats["high_score"], 250)

    def test_record_loss(self):
        """Losing updates games, losses, and resets current streak."""
        # Win first
        self.manager.record_game(is_won=True, score=200)
        # Then lose
        self.manager.record_game(is_won=False, score=0)
        stats = self.manager.get_stats()

        self.assertEqual(stats["total_games"], 2)
        self.assertEqual(stats["wins"], 1)
        self.assertEqual(stats["losses"], 1)
        self.assertEqual(stats["win_percentage"], 50.0)
        self.assertEqual(stats["current_streak"], 0)
        self.assertEqual(stats["best_streak"], 1)
        self.assertEqual(stats["total_score"], 200)

    def test_persistence_across_instances(self):
        """Creating a new manager on existing file preserves data."""
        self.manager.record_game(is_won=True, score=300)
        self.manager.record_game(is_won=True, score=150)

        # Create new instance with same file
        new_manager = StatsManager(filepath=self.stats_file)
        stats = new_manager.get_stats()

        self.assertEqual(stats["total_games"], 2)
        self.assertEqual(stats["wins"], 2)
        self.assertEqual(stats["total_score"], 450)
        self.assertEqual(stats["high_score"], 300)
        self.assertEqual(stats["best_streak"], 2)

    def test_corrupted_json_recovery(self):
        """Corrupted JSON file is safely caught and reset to defaults."""
        with open(self.stats_file, "w", encoding="utf-8") as f:
            f.write("{ invalid json content ...")

        recovered = StatsManager(filepath=self.stats_file)
        stats = recovered.get_stats()
        self.assertEqual(stats["total_games"], 0)
        self.assertEqual(stats["wins"], 0)


if __name__ == "__main__":
    unittest.main()
