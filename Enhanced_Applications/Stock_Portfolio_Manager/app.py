"""
app.py - Application Entry Point
================================
Main entry point for the Stock Portfolio Manager application.
Initializes the database, business logic, theme, and desktop GUI.
"""

import sys
import os
import ttkbootstrap as tb

from src.database import DatabaseManager
from src.portfolio import PortfolioManager
from src.ui import StockPortfolioApp


def center_window(window: tb.Window, width: int = 1180, height: int = 760):
    """Calculate and set geometry to center window on the primary screen."""
    window.update_idletasks()
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()

    # Calculate coordinates
    x = max(0, (screen_width - width) // 2)
    y = max(0, (screen_height - height) // 2)

    window.geometry(f"{width}x{height}+{x}+{y}")


def main():
    """Initialize resources and launch the GUI event loop."""
    # Ensure current directory is in python path
    base_dir = os.path.dirname(os.path.abspath(__file__))
    if base_dir not in sys.path:
        sys.path.insert(0, base_dir)

    # 1. Initialize SQLite Database
    db_path = os.path.join(base_dir, "data", "portfolio.db")
    db_manager = DatabaseManager(db_path=db_path)

    # 2. Initialize Business Logic
    portfolio_manager = PortfolioManager(db_manager=db_manager)

    # 3. Create ttkbootstrap Window with Dark Navy Theme ("superhero")
    app_window = tb.Window(
        title="Stock Portfolio Manager",
        themename="superhero"
    )

    # Center window on screen
    center_window(app_window, width=1180, height=760)

    # 4. Mount Application UI
    app = StockPortfolioApp(root=app_window, portfolio_manager=portfolio_manager)

    # 5. Start GUI Event Loop
    try:
        app_window.mainloop()
    except KeyboardInterrupt:
        print("\nApplication terminated by user.")
        sys.exit(0)


if __name__ == "__main__":
    main()
