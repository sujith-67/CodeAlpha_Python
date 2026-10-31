"""Application entry point for the Hangman Desktop Game.

Launches the ttkbootstrap window with modern superhero dark navy theme
and initializes the application controller.
"""

from __future__ import annotations

import sys
import ttkbootstrap as tb

from src.ui import HangmanUI


def center_window(window: tb.Window, width: int = 1060, height: int = 740) -> None:
    """Center the application window on the active monitor screen."""
    window.update_idletasks()
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()

    x = max(0, (screen_width - width) // 2)
    y = max(0, (screen_height - height) // 2)

    window.geometry(f"{width}x{height}+{x}+{y}")


def main() -> None:
    """Initialize and run the Hangman game."""
    # Create main themed window using modern dark navy theme
    theme = "nord-dark"
    try:
        root = tb.Window(
            title="Hangman - Modern Python Word Game",
            themename=theme,
            iconphoto="",
        )
    except Exception:
        root = tb.Window(
            title="Hangman - Modern Python Word Game",
            themename="superhero",
            iconphoto="",
        )

    # Center window
    center_window(root, 1060, 740)

    # Initialize UI
    HangmanUI(root)

    # Run application mainloop
    try:
        root.mainloop()
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == "__main__":
    main()
