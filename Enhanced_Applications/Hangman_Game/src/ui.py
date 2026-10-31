"""Modern Dark-Themed User Interface for Hangman Game.

Built with Tkinter and ttkbootstrap, featuring a dark navy gaming dashboard,
progressive canvas Hangman illustration, interactive letter slots, QWERTY keyboard,
and comprehensive career statistics.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox
from typing import Callable, Dict, List, Optional
import ttkbootstrap as tb
from ttkbootstrap.constants import *

from src.game_logic import DIFFICULTIES, GameLogic
from src.statistics import StatsManager

# Visual Palette Constants
COLOR_BG_DARK = "#1a2634"       # Deep dark navy
COLOR_CARD_BG = "#243345"       # Card navy background
COLOR_CANVAS_BG = "#131e2b"     # Darker navy for gallows canvas
COLOR_TEXT_WHITE = "#f8fafc"    # Bright text
COLOR_TEXT_MUTED = "#94a3b8"    # Subtle secondary text
COLOR_CYAN_ACCENT = "#38bdf8"   # Bright cyan accent
COLOR_AMBER_ACCENT = "#f59e0b"  # Amber accent for rope / warnings
COLOR_EMERALD = "#22c55e"       # Success green
COLOR_ROSE = "#ef4444"          # Danger / error red
COLOR_SLATE_BORDER = "#334155"  # Subtle card border


class HangmanCanvas(tk.Canvas):
    """Custom Tkinter Canvas that progressively renders the Hangman gallows and figure."""

    def __init__(self, master: tk.Widget, **kwargs) -> None:
        defaults = {
            "width": 310,
            "height": 330,
            "bg": COLOR_CANVAS_BG,
            "highlightthickness": 1,
            "highlightbackground": COLOR_SLATE_BORDER,
        }
        defaults.update(kwargs)
        super().__init__(master, **defaults)
        self.render(mistakes=0, is_won=False, is_lost=False)

    def render(self, mistakes: int, is_won: bool = False, is_lost: bool = False) -> None:
        """Render the complete scene based on current game state.

        Args:
            mistakes: Number of incorrect guesses (0 through 6).
            is_won: True if player has won the game.
            is_lost: True if attempts are exhausted.
        """
        self.delete("all")

        if is_won:
            self._render_victory_scene()
            return

        # Base Gallows (Ground, Post, Beam, Brace, Rope)
        self._render_gallows()

        # Progressive stick figure parts based on incorrect guesses (1 to 6)
        if mistakes >= 1:
            self._render_head(is_lost)
        if mistakes >= 2:
            self._render_body()
        if mistakes >= 3:
            self._render_left_arm()
        if mistakes >= 4:
            self._render_right_arm()
        if mistakes >= 5:
            self._render_left_leg()
        if mistakes >= 6:
            self._render_right_leg()

    def _render_gallows(self) -> None:
        """Draw the wooden gallows frame."""
        # Ground platform
        self.create_line(40, 290, 190, 290, width=6, fill="#64748b", capstyle="round")
        # Vertical post
        self.create_line(80, 290, 80, 45, width=7, fill="#94a3b8", capstyle="round")
        # Top beam
        self.create_line(76, 45, 235, 45, width=7, fill="#94a3b8", capstyle="round")
        # Diagonal support brace
        self.create_line(80, 95, 130, 45, width=4, fill="#64748b", capstyle="round")
        # Hanging rope
        self.create_line(210, 45, 210, 82, width=3, fill=COLOR_AMBER_ACCENT, capstyle="round")
        # Noose loop / knot
        self.create_oval(206, 78, 214, 86, fill=COLOR_AMBER_ACCENT, outline="#d97706")

    def _render_head(self, is_lost: bool) -> None:
        """Draw head with expressions."""
        color = COLOR_ROSE if is_lost else COLOR_CYAN_ACCENT
        # Head circle
        self.create_oval(188, 86, 232, 130, width=3, outline=color, fill=COLOR_CARD_BG)

        if is_lost:
            # Dead 'X' eyes
            self.create_line(198, 100, 204, 106, width=2, fill=COLOR_ROSE, capstyle="round")
            self.create_line(198, 106, 204, 100, width=2, fill=COLOR_ROSE, capstyle="round")

            self.create_line(216, 100, 222, 106, width=2, fill=COLOR_ROSE, capstyle="round")
            self.create_line(216, 106, 222, 100, width=2, fill=COLOR_ROSE, capstyle="round")

            # Frown
            self.create_line(204, 120, 216, 120, width=2, fill=COLOR_ROSE, capstyle="round")
        else:
            # Neutral eyes
            self.create_oval(201, 103, 204, 106, fill=color, outline=color)
            self.create_oval(216, 103, 219, 106, fill=color, outline=color)
            # Neutral mouth
            self.create_line(206, 118, 214, 118, width=2, fill=color, capstyle="round")

    def _render_body(self) -> None:
        """Draw torso line."""
        self.create_line(210, 130, 210, 195, width=4, fill=COLOR_CYAN_ACCENT, capstyle="round")

    def _render_left_arm(self) -> None:
        """Draw left arm."""
        self.create_line(210, 148, 180, 178, width=4, fill=COLOR_CYAN_ACCENT, capstyle="round")

    def _render_right_arm(self) -> None:
        """Draw right arm."""
        self.create_line(210, 148, 240, 178, width=4, fill=COLOR_CYAN_ACCENT, capstyle="round")

    def _render_left_leg(self) -> None:
        """Draw left leg."""
        self.create_line(210, 195, 185, 248, width=4, fill=COLOR_CYAN_ACCENT, capstyle="round")

    def _render_right_leg(self) -> None:
        """Draw right leg."""
        self.create_line(210, 195, 235, 248, width=4, fill=COLOR_CYAN_ACCENT, capstyle="round")

    def _render_victory_scene(self) -> None:
        """Draw celebratory stick figure standing free on grass with arms raised."""
        # Celebration ground
        self.create_line(30, 270, 280, 270, width=5, fill=COLOR_EMERALD, capstyle="round")

        # Free happy stickman standing proudly
        cx, cy = 155, 120  # Head center

        # Golden winner star above
        self.create_text(cx, cy - 50, text="★ WINNER ★", fill="#fbbf24", font=("Segoe UI", 12, "bold"))

        # Head
        self.create_oval(cx - 22, cy - 22, cx + 22, cy + 22, width=3, outline=COLOR_EMERALD, fill=COLOR_CARD_BG)
        # Happy eyes
        self.create_oval(cx - 10, cy - 6, cx - 6, cy - 2, fill=COLOR_EMERALD, outline=COLOR_EMERALD)
        self.create_oval(cx + 6, cy - 6, cx + 10, cy - 2, fill=COLOR_EMERALD, outline=COLOR_EMERALD)
        # Big smile
        self.create_arc(cx - 12, cy - 8, cx + 12, cy + 14, start=200, extent=140, style="arc", outline=COLOR_EMERALD, width=2)

        # Torso
        self.create_line(cx, cy + 22, cx, cy + 85, width=4, fill=COLOR_EMERALD, capstyle="round")

        # Arms raised in victory \o/
        self.create_line(cx, cy + 38, cx - 35, cy - 5, width=4, fill=COLOR_EMERALD, capstyle="round")
        self.create_line(cx, cy + 38, cx + 35, cy - 5, width=4, fill=COLOR_EMERALD, capstyle="round")

        # Legs
        self.create_line(cx, cy + 85, cx - 28, 270, width=4, fill=COLOR_EMERALD, capstyle="round")
        self.create_line(cx, cy + 85, cx + 28, 270, width=4, fill=COLOR_EMERALD, capstyle="round")

        # Confetti sparkles
        sparkles = [
            (cx - 70, cy + 10, COLOR_CYAN_ACCENT),
            (cx + 70, cy + 20, COLOR_AMBER_ACCENT),
            (cx - 60, cy + 80, "#a855f7"),
            (cx + 65, cy + 90, COLOR_CYAN_ACCENT),
            (cx - 40, cy - 40, COLOR_AMBER_ACCENT),
            (cx + 45, cy - 35, COLOR_EMERALD),
        ]
        for sx, sy, sc in sparkles:
            self.create_text(sx, sy, text="✦", fill=sc, font=("Segoe UI", 12))


class HangmanUI:
    """Main application controller managing Welcome and Gameplay views."""

    def __init__(self, root: tb.Window) -> None:
        """Initialize UI inside the provided root ttkbootstrap window."""
        self.root = root
        self.root.title("Hangman - The Modern Python Word Challenge")
        self.root.geometry("1060x740")
        self.root.minsize(960, 680)

        # Initialize core logic and statistics
        self.stats_manager = StatsManager()
        self.game = GameLogic(difficulty="medium")

        # UI state variables
        self.selected_difficulty = tk.StringVar(value="medium")
        self.alphabet_buttons: Dict[str, tb.Button] = {}
        self.letter_slot_widgets: List[tk.Widget] = []

        # Main container holds screens
        self.container = tb.Frame(self.root, padding=0)
        self.container.pack(fill=BOTH, expand=True)

        # Build view frames
        self.welcome_frame = tb.Frame(self.container, padding=25)
        self.game_frame = tb.Frame(self.container, padding=20)

        self._build_welcome_screen()
        self._build_gameplay_screen()

        # Keyboard listener
        self.root.bind("<Key>", self._on_key_press)

        # Show welcome screen first
        self.show_welcome_screen()

    # -------------------------------------------------------------------------
    # Screen Switching
    # -------------------------------------------------------------------------

    def show_welcome_screen(self) -> None:
        """Switch view to Welcome screen and refresh stats."""
        self.game_frame.pack_forget()
        self._refresh_stats_display()
        self.welcome_frame.pack(fill=BOTH, expand=True)

    def show_gameplay_screen(self) -> None:
        """Switch view to Gameplay screen and start round."""
        self.welcome_frame.pack_forget()
        self.game_frame.pack(fill=BOTH, expand=True)
        self._start_new_round()

    # -------------------------------------------------------------------------
    # Welcome Screen Builder
    # -------------------------------------------------------------------------

    def _build_welcome_screen(self) -> None:
        """Build the polished welcome dashboard screen."""
        # Top Hero Header
        header_frame = tb.Frame(self.welcome_frame)
        header_frame.pack(fill=X, pady=(5, 20))

        title_label = tb.Label(
            header_frame,
            text="🎯 HANGMAN",
            font=("Segoe UI", 32, "bold"),
            bootstyle="primary",
        )
        title_label.pack(anchor=CENTER)

        subtitle_label = tb.Label(
            header_frame,
            text="The Ultimate Desktop Word-Guessing Challenge",
            font=("Segoe UI", 13),
            bootstyle="secondary",
        )
        subtitle_label.pack(anchor=CENTER, pady=(2, 0))

        # Main Split Content (Left: Config & Play; Right: Statistics)
        content_frame = tb.Frame(self.welcome_frame)
        content_frame.pack(fill=BOTH, expand=True)
        content_frame.columnconfigure(0, weight=1, uniform="group1")
        content_frame.columnconfigure(1, weight=1, uniform="group1")

        # ----------------- Left Panel: Game Setup -----------------
        left_card = tb.Labelframe(
            content_frame,
            text=" ⚙️ Game Setup & Mode ",
            padding=20,
            bootstyle="primary",
        )
        left_card.grid(row=0, column=0, sticky="nsew", padx=(0, 12), pady=5)

        diff_title = tb.Label(
            left_card,
            text="Select Difficulty Tier:",
            font=("Segoe UI", 12, "bold"),
        )
        diff_title.pack(anchor=W, pady=(0, 10))

        # Difficulty Radio Buttons
        diff_options = [
            ("🟢 Easy Mode", "easy", "4–5 Letter Words • Relaxed & Casual"),
            ("🟡 Medium Mode", "medium", "6–8 Letter Words • Standard Challenge"),
            ("🔴 Hard Mode", "hard", "9+ Letter Words • Expert Vocabulary"),
        ]

        for text, val, desc in diff_options:
            opt_box = tb.Frame(left_card, padding=8)
            opt_box.pack(fill=X, pady=4)
            rb = tb.Radiobutton(
                opt_box,
                text=text,
                value=val,
                variable=self.selected_difficulty,
                bootstyle="info-toolbutton",
            )
            rb.pack(anchor=W)
            desc_lbl = tb.Label(
                opt_box,
                text=f"   {desc}",
                font=("Segoe UI", 9),
                bootstyle="secondary",
            )
            desc_lbl.pack(anchor=W, pady=(2, 0))

        # Play Game Button
        play_btn = tb.Button(
            left_card,
            text="🎮 START GAME",
            bootstyle="success",
            command=self.show_gameplay_screen,
            width=22,
        )
        play_btn.pack(pady=(20, 15))

        # Instructions Sub-card
        inst_card = tb.Labelframe(
            left_card,
            text=" 📖 Quick Rules ",
            padding=12,
            bootstyle="secondary",
        )
        inst_card.pack(fill=X, pady=(5, 0))

        rules_text = (
            "• Guess the hidden word one letter at a time.\n"
            "• You have 6 incorrect attempts before the hangman is complete.\n"
            "• 1 Hint available per round (bonus points if solved without it).\n"
            "• Use your keyboard or click on-screen buttons to guess."
        )
        tb.Label(
            inst_card,
            text=rules_text,
            font=("Segoe UI", 9),
            justify=LEFT,
            bootstyle="secondary",
        ).pack(anchor=W)

        # ----------------- Right Panel: Career Dashboard -----------------
        right_card = tb.Labelframe(
            content_frame,
            text=" 📊 Player Career Statistics ",
            padding=20,
            bootstyle="info",
        )
        right_card.grid(row=0, column=1, sticky="nsew", padx=(12, 0), pady=5)

        self.stats_grid = tb.Frame(right_card)
        self.stats_grid.pack(fill=BOTH, expand=True, pady=10)
        self.stats_grid.columnconfigure(0, weight=1)
        self.stats_grid.columnconfigure(1, weight=1)

        # Dictionary of stat label references for easy updates
        self.stat_value_labels: Dict[str, tb.Label] = {}
        stat_items = [
            ("total_games", "Total Games", "🎮", 0, 0),
            ("win_rate", "Win Rate", "📈", 0, 1),
            ("wins", "Victories", "🏆", 1, 0),
            ("losses", "Defeats", "💀", 1, 1),
            ("streaks", "Streaks (Cur/Best)", "🔥", 2, 0),
            ("scores", "Total / High Score", "⭐", 2, 1),
        ]

        for key, title, icon, r, c in stat_items:
            tile = tb.Frame(self.stats_grid, padding=12, bootstyle="secondary")
            tile.grid(row=r, column=c, padx=6, pady=6, sticky="nsew")

            tb.Label(
                tile,
                text=f"{icon} {title}",
                font=("Segoe UI", 9, "bold"),
                bootstyle="light",
            ).pack(anchor=W)

            val_lbl = tb.Label(
                tile,
                text="0",
                font=("Segoe UI", 16, "bold"),
                bootstyle="primary",
            )
            val_lbl.pack(anchor=W, pady=(4, 0))
            self.stat_value_labels[key] = val_lbl

        # Reset Stats Button
        reset_btn = tb.Button(
            right_card,
            text="↺ Reset Career Statistics",
            bootstyle="secondary-link",
            command=self._confirm_reset_stats,
        )
        reset_btn.pack(anchor=E, pady=(15, 0))

    def _refresh_stats_display(self) -> None:
        """Fetch latest statistics and update all dashboard metric cards."""
        stats = self.stats_manager.get_stats()

        self.stat_value_labels["total_games"].config(text=str(stats["total_games"]))
        self.stat_value_labels["win_rate"].config(text=f"{stats['win_percentage']}%")
        self.stat_value_labels["wins"].config(text=str(stats["wins"]))
        self.stat_value_labels["losses"].config(text=str(stats["losses"]))
        self.stat_value_labels["streaks"].config(
            text=f"{stats['current_streak']} / {stats['best_streak']}"
        )
        self.stat_value_labels["scores"].config(
            text=f"{stats['total_score']} (Top: {stats['high_score']})"
        )

    def _confirm_reset_stats(self) -> None:
        """Show confirmation dialog before wiping saved career statistics."""
        if messagebox.askyesno(
            "Reset Statistics",
            "Are you sure you want to reset all saved career statistics? This cannot be undone.",
        ):
            self.stats_manager.reset_stats()
            self._refresh_stats_display()

    # -------------------------------------------------------------------------
    # Gameplay Screen Builder
    # -------------------------------------------------------------------------

    def _build_gameplay_screen(self) -> None:
        """Build the gameplay screen with gallows, hidden slots, and keyboard."""
        # Top Header Bar
        top_bar = tb.Frame(self.game_frame)
        top_bar.pack(fill=X, pady=(0, 10))

        # Left action buttons
        nav_box = tb.Frame(top_bar)
        nav_box.pack(side=LEFT)

        home_btn = tb.Button(
            nav_box,
            text="⌂ Home",
            bootstyle="secondary-outline",
            command=self.show_welcome_screen,
        )
        home_btn.pack(side=LEFT, padx=(0, 8))

        new_btn = tb.Button(
            nav_box,
            text="↺ New Word",
            bootstyle="info-outline",
            command=self._start_new_round,
        )
        new_btn.pack(side=LEFT)

        # Center: Difficulty Badge
        self.diff_badge = tb.Label(
            top_bar,
            text="[ MEDIUM ]",
            font=("Segoe UI", 11, "bold"),
            bootstyle="primary",
        )
        self.diff_badge.pack(side=LEFT, padx=30)

        # Right: Live Score & Streak
        self.score_streak_lbl = tb.Label(
            top_bar,
            text="Score: 0  |  Streak: 0 🔥",
            font=("Segoe UI", 11, "bold"),
            bootstyle="light",
        )
        self.score_streak_lbl.pack(side=RIGHT)

        # Main Play Area Split
        main_play_frame = tb.Frame(self.game_frame)
        main_play_frame.pack(fill=BOTH, expand=True)
        main_play_frame.columnconfigure(0, weight=0)  # Canvas card fixed width
        main_play_frame.columnconfigure(1, weight=1)  # Interactive board takes rest

        # ----------------- Left: Hangman Canvas Card -----------------
        canvas_card = tb.Labelframe(
            main_play_frame,
            text=" 🎨 Gallows Illustration ",
            padding=12,
            bootstyle="secondary",
        )
        canvas_card.grid(row=0, column=0, sticky="nsew", padx=(0, 15), pady=5)

        self.canvas = HangmanCanvas(canvas_card)
        self.canvas.pack(padx=5, pady=5)

        # Attempts remaining display
        self.attempts_lbl = tb.Label(
            canvas_card,
            text="Remaining Attempts: 6 / 6",
            font=("Segoe UI", 11, "bold"),
            bootstyle="info",
        )
        self.attempts_lbl.pack(pady=(8, 2))

        # Visual heart / dot indicators
        self.attempts_visual_lbl = tb.Label(
            canvas_card,
            text="● ● ● ● ● ●",
            font=("Segoe UI", 14, "bold"),
            bootstyle="success",
        )
        self.attempts_visual_lbl.pack(pady=(0, 5))

        # ----------------- Right: Board & Alphabet -----------------
        self.board_card = tb.Labelframe(
            main_play_frame,
            text=" 🎯 Word Board ",
            padding=15,
            bootstyle="primary",
        )
        self.board_card.grid(row=0, column=1, sticky="nsew", pady=5)

        # 1. Word Letter Slots Container
        self.word_slots_frame = tb.Frame(self.board_card, padding=10)
        self.word_slots_frame.pack(fill=X, pady=(5, 15))

        # 2. Hint Banner / Trigger Container
        self.hint_frame = tb.Frame(self.board_card, padding=6)
        self.hint_frame.pack(fill=X, pady=(0, 12))

        self.hint_btn = tb.Button(
            self.hint_frame,
            text="💡 Need a Hint? Click to Reveal (-30 pts)",
            bootstyle="warning-outline",
            command=self._on_hint_clicked,
        )
        self.hint_btn.pack(side=LEFT)

        self.hint_text_lbl = tb.Label(
            self.hint_frame,
            text="",
            font=("Segoe UI", 10, "italic"),
            bootstyle="warning",
            wraplength=450,
        )
        self.hint_text_lbl.pack(side=LEFT, padx=10, fill=X, expand=True)

        # 3. Incorrect Guesses Display
        self.wrong_letters_frame = tb.Frame(self.board_card, padding=6)
        self.wrong_letters_frame.pack(fill=X, pady=(0, 15))

        tb.Label(
            self.wrong_letters_frame,
            text="Wrong Guesses:",
            font=("Segoe UI", 10, "bold"),
            bootstyle="secondary",
        ).pack(side=LEFT, padx=(0, 8))

        self.wrong_letters_lbl = tb.Label(
            self.wrong_letters_frame,
            text="None yet",
            font=("Segoe UI", 10, "bold"),
            bootstyle="danger",
        )
        self.wrong_letters_lbl.pack(side=LEFT)

        # 4. Interactive QWERTY Alphabet Keyboard
        self.keyboard_card = tb.Labelframe(
            self.board_card,
            text=" ⌨️ Alphabet Keyboard (Press keys or click buttons) ",
            padding=10,
            bootstyle="secondary",
        )
        self.keyboard_card.pack(fill=BOTH, expand=True)

        self._build_keyboard()

        # 5. Round Result Banner (Initially hidden)
        self.result_banner = tb.Frame(self.board_card, padding=12, bootstyle="secondary")

    def _build_keyboard(self) -> None:
        """Create the QWERTY keyboard layout buttons."""
        qwerty_rows = [
            list("QWERTYUIOP"),
            list("ASDFGHJKL"),
            list("ZXCVBNM"),
        ]

        for row_idx, row_letters in enumerate(qwerty_rows):
            row_frame = tb.Frame(self.keyboard_card)
            row_frame.pack(pady=4)

            for char in row_letters:
                btn = tb.Button(
                    row_frame,
                    text=char,
                    width=3,
                    bootstyle="secondary",
                    command=lambda c=char: self._handle_guess(c),
                )
                btn.pack(side=LEFT, padx=3)
                self.alphabet_buttons[char.lower()] = btn

    # -------------------------------------------------------------------------
    # Game Loop & Interaction Handlers
    # -------------------------------------------------------------------------

    def _start_new_round(self) -> None:
        """Initialize or reset a gameplay round."""
        diff = self.selected_difficulty.get()
        self.game.start_new_game(difficulty=diff)

        # Hide any active result banner
        self.result_banner.pack_forget()
        self.keyboard_card.pack(fill=BOTH, expand=True)

        # Update difficulty badge
        self.diff_badge.config(
            text=f"[ {diff.upper()} ]",
            bootstyle="success" if diff == "easy" else ("warning" if diff == "medium" else "danger"),
        )

        # Reset Hint
        self.hint_btn.config(
            text="💡 Need a Hint? Click to Reveal (-30 pts)",
            state=NORMAL,
            bootstyle="warning-outline",
        )
        self.hint_text_lbl.config(text="")

        # Reset Alphabet Buttons
        for btn in self.alphabet_buttons.values():
            btn.config(state=NORMAL, bootstyle="secondary")

        # Reset Incorrect Guesses display
        self.wrong_letters_lbl.config(text="None yet")

        # Reset Canvas & Attempts
        self.canvas.render(mistakes=0, is_won=False, is_lost=False)
        self._update_attempts_display()
        self._update_header_stats()
        self._render_word_slots()

    def _render_word_slots(self) -> None:
        """Render individual styled tiles for each letter in the secret word."""
        for widget in self.letter_slot_widgets:
            widget.destroy()
        self.letter_slot_widgets.clear()

        slots = self.game.get_display_slots()
        for char in slots:
            slot_frame = tb.Frame(
                self.word_slots_frame,
                padding=(12, 8),
                bootstyle="dark",
            )
            slot_frame.pack(side=LEFT, padx=5)

            display_char = char if char is not None else "_"
            char_style = "light" if char is not None else "secondary"

            lbl = tb.Label(
                slot_frame,
                text=display_char,
                font=("Segoe UI", 20, "bold"),
                bootstyle=char_style,
                width=2,
                anchor=CENTER,
            )
            lbl.pack()
            self.letter_slot_widgets.append(slot_frame)

    def _update_attempts_display(self) -> None:
        """Update the textual and visual attempt dots."""
        rem = self.game.attempts_left
        self.attempts_lbl.config(
            text=f"Remaining Attempts: {rem} / {self.game.max_attempts}",
            bootstyle="success" if rem >= 4 else ("warning" if rem >= 2 else "danger"),
        )

        # Colored dot indicators
        dots = ("● " * rem).strip()
        empty = ("○ " * (self.game.max_attempts - rem)).strip()
        full_display = f"{dots} {empty}".strip() if empty else dots

        self.attempts_visual_lbl.config(
            text=full_display,
            bootstyle="success" if rem >= 4 else ("warning" if rem >= 2 else "danger"),
        )

    def _update_header_stats(self) -> None:
        """Update top bar score and streak counters."""
        stats = self.stats_manager.get_stats()
        self.score_streak_lbl.config(
            text=f"Score: {stats['total_score']}  |  Streak: {stats['current_streak']} 🔥"
        )

    def _handle_guess(self, raw_letter: str) -> None:
        """Process a guess made by user via keyboard or on-screen click."""
        if self.game.game_over:
            return

        letter = raw_letter.strip().lower()
        if not letter or letter not in self.alphabet_buttons:
            return

        # Disable button immediately
        btn = self.alphabet_buttons.get(letter)

        result = self.game.make_guess(letter)
        status = result.get("status")

        if status == "correct":
            if btn:
                btn.config(bootstyle="success", state=DISABLED)
            self._render_word_slots()

        elif status == "incorrect":
            if btn:
                btn.config(bootstyle="danger", state=DISABLED)
            wrongs = ", ".join(k.upper() for k in self.game.incorrect_guesses)
            self.wrong_letters_lbl.config(text=wrongs if wrongs else "None yet")
            self._update_attempts_display()
            self.canvas.render(
                mistakes=len(self.game.incorrect_guesses),
                is_won=False,
                is_lost=self.game.game_over,
            )

        elif status == "repeated":
            if btn:
                btn.config(state=DISABLED)

        # Check round termination
        if self.game.game_over:
            self._on_round_completed()

    def _on_hint_clicked(self) -> None:
        """Handle hint button activation."""
        if self.game.game_over or self.game.hint_used:
            return

        hint_text = self.game.use_hint()
        self.hint_btn.config(
            text="💡 Hint Used (-30 pts applied)",
            state=DISABLED,
            bootstyle="secondary",
        )
        self.hint_text_lbl.config(text=f"Clue: {hint_text}")

    def _on_key_press(self, event: tk.Event) -> None:
        """Global key event listener for physical keyboard gameplay."""
        # Only process if gameplay screen is currently visible
        if self.game_frame.winfo_manager() != "pack":
            return
        if self.game.game_over:
            return

        char = event.char.lower()
        if char.isalpha() and char.isascii():
            self._handle_guess(char)

    def _on_round_completed(self) -> None:
        """Handle game over (win or loss) state, update stats, and show results."""
        # Disable all remaining alphabet buttons
        for btn in self.alphabet_buttons.values():
            btn.config(state=DISABLED)

        score_info = self.game.calculate_score_breakdown()
        round_score = score_info["total"]

        # Record outcome in persistent statistics
        self.stats_manager.record_game(is_won=self.game.is_won, score=round_score)
        self._update_header_stats()

        # Update canvas for final win or loss expressions
        self.canvas.render(
            mistakes=len(self.game.incorrect_guesses),
            is_won=self.game.is_won,
            is_lost=not self.game.is_won,
        )

        # Show round outcome banner
        self._display_round_result_banner(score_info)

    def _display_round_result_banner(self, score_info: Dict[str, int]) -> None:
        """Display an attractive outcome panel with score breakdown and actions."""
        # Clear previous banner contents
        for child in self.result_banner.winfo_children():
            child.destroy()

        self.keyboard_card.pack_forget()
        self.result_banner.pack(fill=BOTH, expand=True, pady=10)

        secret_word_upper = self.game.secret_word.upper()

        if self.game.is_won:
            tb.Label(
                self.result_banner,
                text="🎉 VICTORY! YOU SOLVED IT!",
                font=("Segoe UI", 16, "bold"),
                bootstyle="success",
            ).pack(pady=(10, 4))

            tb.Label(
                self.result_banner,
                text=f"The secret word was: {secret_word_upper}",
                font=("Segoe UI", 12, "bold"),
                bootstyle="light",
            ).pack(pady=(0, 8))

            breakdown_text = (
                f"Base Points: +{score_info['base']}  |  "
                f"Mistake Bonus: +{score_info['bonus']}  |  "
                f"Hint: {score_info['penalty']}  |  "
                f"Total Earned: +{score_info['total']} pts"
            )
            tb.Label(
                self.result_banner,
                text=breakdown_text,
                font=("Segoe UI", 10),
                bootstyle="info",
            ).pack(pady=(0, 15))

        else:
            tb.Label(
                self.result_banner,
                text="💀 GAME OVER! ATTEMPTS EXHAUSTED",
                font=("Segoe UI", 16, "bold"),
                bootstyle="danger",
            ).pack(pady=(10, 4))

            tb.Label(
                self.result_banner,
                text=f"The correct word was: {secret_word_upper}",
                font=("Segoe UI", 13, "bold"),
                bootstyle="warning",
            ).pack(pady=(0, 8))

            tb.Label(
                self.result_banner,
                text="Don't give up! Try another round to rebuild your streak.",
                font=("Segoe UI", 10),
                bootstyle="secondary",
            ).pack(pady=(0, 15))

        # Action Buttons
        btn_box = tb.Frame(self.result_banner)
        btn_box.pack(pady=(0, 10))

        again_btn = tb.Button(
            btn_box,
            text="▶ Play Again",
            bootstyle="success" if self.game.is_won else "warning",
            command=self._start_new_round,
            width=14,
        )
        again_btn.pack(side=LEFT, padx=6)

        home_btn = tb.Button(
            btn_box,
            text="⌂ Return Home",
            bootstyle="secondary-outline",
            command=self.show_welcome_screen,
            width=14,
        )
        home_btn.pack(side=LEFT, padx=6)
