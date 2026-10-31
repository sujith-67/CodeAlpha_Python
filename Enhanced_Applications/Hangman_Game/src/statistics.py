"""Statistics management module for Hangman Game.

Handles persistent tracking of player performance including games played,
wins, losses, win percentage, streaks, and scores using local JSON storage.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict

# Set up logging for statistical operations
logger = logging.getLogger(__name__)

# Base project paths
BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_STATS_PATH = BASE_DIR / "data" / "stats.json"

DEFAULT_STATS: Dict[str, Any] = {
    "total_games": 0,
    "wins": 0,
    "losses": 0,
    "win_percentage": 0.0,
    "current_streak": 0,
    "best_streak": 0,
    "total_score": 0,
    "high_score": 0,
}


class StatsManager:
    """Manages reading, updating, and persisting game statistics to a JSON file."""

    def __init__(self, filepath: Path | str | None = None) -> None:
        """Initialize the StatsManager with a target file path.

        Args:
            filepath: Custom path to stats.json. If None, defaults to data/stats.json.
        """
        if filepath is None:
            self.filepath = DEFAULT_STATS_PATH
        else:
            self.filepath = Path(filepath)

        self.stats: Dict[str, Any] = self.load_stats()

    def load_stats(self) -> Dict[str, Any]:
        """Load statistics from the JSON file.

        If the file does not exist, is empty, or contains corrupt data,
        it initializes and returns the default statistics structure.

        Returns:
            Dictionary containing current player statistics.
        """
        if not self.filepath.exists():
            data = dict(DEFAULT_STATS)
            self._write_to_file(data)
            return data

        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    logger.warning("Stats file was empty. Resetting to defaults.")
                    data = dict(DEFAULT_STATS)
                    self._write_to_file(data)
                    return data
                data = json.loads(content)

            # Ensure all required keys exist (schema migration / sanity check)
            for key, default_val in DEFAULT_STATS.items():
                if key not in data:
                    data[key] = default_val

            return data
        except (json.JSONDecodeError, OSError) as e:
            logger.error("Failed to read stats file (%s). Falling back to defaults.", e)
            data = dict(DEFAULT_STATS)
            self._write_to_file(data)
            return data

    def _write_to_file(self, data: Dict[str, Any]) -> bool:
        """Helper to write data to disk safely.

        Args:
            data: The statistics dictionary to serialize.

        Returns:
            True if write succeeded, False otherwise.
        """
        try:
            self.filepath.parent.mkdir(parents=True, exist_ok=True)
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
            return True
        except OSError as e:
            logger.error("Error writing stats file: %s", e)
            return False

    def save_stats(self) -> bool:
        """Save current statistics to file.

        Returns:
            True if write succeeded, False otherwise.
        """
        return self._write_to_file(self.stats)

    def record_game(self, is_won: bool, score: int = 0) -> Dict[str, Any]:
        """Record the outcome of a completed round and update stats.

        Args:
            is_won: True if player won, False if hanged/lost.
            score: Points scored in the round (0 if lost).

        Returns:
            Updated statistics dictionary.
        """
        self.stats["total_games"] += 1

        if is_won:
            self.stats["wins"] += 1
            self.stats["current_streak"] += 1
            if self.stats["current_streak"] > self.stats["best_streak"]:
                self.stats["best_streak"] = self.stats["current_streak"]
            self.stats["total_score"] += score
            if score > self.stats["high_score"]:
                self.stats["high_score"] = score
        else:
            self.stats["losses"] += 1
            self.stats["current_streak"] = 0

        total = self.stats["total_games"]
        wins = self.stats["wins"]
        self.stats["win_percentage"] = round((wins / total * 100.0), 1) if total > 0 else 0.0

        self.save_stats()
        return dict(self.stats)

    def get_stats(self) -> Dict[str, Any]:
        """Get a copy of current statistics.

        Returns:
            Dictionary copy of statistics.
        """
        return dict(self.stats)

    def reset_stats(self) -> Dict[str, Any]:
        """Reset all statistics to initial defaults and persist to disk.

        Returns:
            Dictionary of fresh default statistics.
        """
        self.stats = dict(DEFAULT_STATS)
        self.save_stats()
        return dict(self.stats)
