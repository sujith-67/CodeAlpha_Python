"""app.py - Main Application Entry Point for Smart Email Extractor
================================================================
Launches the themed desktop dashboard with ttkbootstrap, centers the application
window, sets responsive minimum boundaries, and connects the user interface controller.
"""

from __future__ import annotations

import sys
import ttkbootstrap as tb

from src.ui import SmartEmailExtractorUI


def center_window(window: tb.Window, width: int = 1120, height: int = 760) -> None:
    """Center the application window dynamically on the user's primary display screen."""
    window.update_idletasks()
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()

    x = max(0, (screen_width - width) // 2)
    y = max(0, (screen_height - height) // 2)

    window.geometry(f"{width}x{height}+{x}+{y}")


def main() -> None:
    """Initialize and run the Smart Email Extractor desktop application."""
    # Preferred dark themes in order of priority
    candidate_themes = ["nord-dark", "darkly", "superhero", "cyborg", "dark"]
    root = None

    for theme in candidate_themes:
        try:
            root = tb.Window(
                title="SMART EMAIL EXTRACTOR — Professional Desktop Utility",
                themename=theme,
                iconphoto="",
            )
            break
        except Exception:
            continue

    if root is None:
        root = tb.Window(
            title="SMART EMAIL EXTRACTOR — Professional Desktop Utility",
            iconphoto="",
        )

    # Apply dimensions and centering
    center_window(root, 1140, 760)

    # Initialize Controller
    SmartEmailExtractorUI(root)

    # Start main event loop
    try:
        root.mainloop()
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == "__main__":
    main()
