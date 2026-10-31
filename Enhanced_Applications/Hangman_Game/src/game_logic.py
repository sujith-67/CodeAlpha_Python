"""Game logic module for Hangman Game.

Manages word lists, difficulty selection, word picking without immediate repetition,
guess processing, attempt tracking, hint usage, score computation, and win/loss states.
"""

from __future__ import annotations

import random
from typing import Dict, List, Optional, Set, Tuple

# Pre-defined word bank with difficulty tiers and educational/contextual hints.
# Easy: 4-5 letter words
# Medium: 6-8 letter words
# Hard: 9 or more letter words
WORD_BANK: Dict[str, List[Dict[str, str]]] = {
    "easy": [
        {"word": "code", "hint": "Instructions written for a computer program"},
        {"word": "data", "hint": "Raw facts, figures, and quantities processed by computers"},
        {"word": "byte", "hint": "A fundamental digital unit consisting of 8 binary bits"},
        {"word": "java", "hint": "Popular class-based, object-oriented programming language"},
        {"word": "node", "hint": "A connection point or data element inside a network or tree"},
        {"word": "file", "hint": "A named resource for recording digital data on storage"},
        {"word": "chip", "hint": "A tiny wafer of semiconducting material holding circuits"},
        {"word": "link", "hint": "A clickable reference or address pointing to another resource"},
        {"word": "loop", "hint": "A programming construct that repeats instructions until a condition is met"},
        {"word": "disk", "hint": "A magnetic or optical storage medium for digital content"},
        {"word": "host", "hint": "A computer or server connected to a network providing services"},
        {"word": "port", "hint": "A virtual communication endpoint identified by a number"},
        {"word": "user", "hint": "A person operating a computer or software application"},
        {"word": "root", "hint": "The superuser account with full administrative system privileges"},
        {"word": "cloud", "hint": "On-demand computing infrastructure accessed over the internet"},
        {"word": "pixel", "hint": "The smallest addressable visual element in a digital image"},
        {"word": "logic", "hint": "The fundamental reasoning and truth-evaluation behind code"},
        {"word": "stack", "hint": "A Last-In, First-Out (LIFO) linear data structure"},
        {"word": "queue", "hint": "A First-In, First-Out (FIFO) linear data structure"},
        {"word": "array", "hint": "An ordered sequence of values stored in contiguous memory"},
        {"word": "mouse", "hint": "A handheld hardware pointer used to navigate graphic interfaces"},
        {"word": "robot", "hint": "An autonomous or programmable machine executing tasks"},
        {"word": "cyber", "hint": "Relating to electronic computers, digital security, and the internet"},
        {"word": "smart", "hint": "Equipped with interactive, programmed processing capabilities"},
        {"word": "linux", "hint": "The famous open-source Unix-like operating system kernel"},
        {"word": "apple", "hint": "Major technology pioneer famous for macOS, iOS, and Macs"},
        {"word": "patch", "hint": "A software release intended to resolve bugs or security flaws"},
        {"word": "token", "hint": "A unique digital credential or authenticated security item"},
        {"word": "cache", "hint": "High-speed temporary hardware or software memory buffer"},
        {"word": "debug", "hint": "The process of identifying and removing errors from source code"},
    ],
    "medium": [
        {"word": "python", "hint": "High-level programming language known for readability and clean syntax"},
        {"word": "coding", "hint": "The creative craft of translating requirements into executable code"},
        {"word": "laptop", "hint": "A portable clamshell computer designed for mobile productivity"},
        {"word": "gaming", "hint": "Interactive entertainment through electronic video games"},
        {"word": "rocket", "hint": "An aerospace propulsion vehicle designed to reach the stars"},
        {"word": "server", "hint": "A dedicated computer system that hosts resources for network clients"},
        {"word": "memory", "hint": "Hardware storage holding active instructions and temporary data"},
        {"word": "binary", "hint": "Base-2 mathematical numbering system using only zeroes and ones"},
        {"word": "system", "hint": "An interconnected collection of hardware and software components"},
        {"word": "router", "hint": "A networking device that directs data packets between networks"},
        {"word": "screen", "hint": "The visual display panel showcasing graphics and text to users"},
        {"word": "script", "hint": "A program interpreted at runtime without manual compilation"},
        {"word": "syntax", "hint": "The grammatical rules governing valid statements in code"},
        {"word": "thread", "hint": "The smallest sequence of programmed execution managed by an OS"},
        {"word": "matrix", "hint": "A two-dimensional rectangular grid of numbers or data elements"},
        {"word": "widget", "hint": "A reusable interactive graphical component in a UI"},
        {"word": "backup", "hint": "A secondary copy of data stored for disaster recovery"},
        {"word": "cursor", "hint": "An on-screen pointer showing where the next user action will occur"},
        {"word": "domain", "hint": "A human-friendly address identifying a website on the internet"},
        {"word": "cookie", "hint": "A small text file saved by browsers to retain user state"},
        {"word": "packet", "hint": "A formatted unit of digital data transmitted over a network"},
        {"word": "socket", "hint": "One endpoint of a two-way network communication link"},
        {"word": "kernel", "hint": "The essential core module of an operating system"},
        {"word": "sensor", "hint": "A device that detects and measures physical signals"},
        {"word": "network", "hint": "A group of interconnected computing nodes exchanging data"},
        {"word": "browser", "hint": "Application used to navigate and view World Wide Web content"},
        {"word": "storage", "hint": "Persistent capacity for holding computer files and documents"},
        {"word": "program", "hint": "A set of written instructions executed by a computer processor"},
        {"word": "monitor", "hint": "An output display hardware device connected to a computer"},
        {"word": "command", "hint": "A specific directive issued to a computer shell or program"},
        {"word": "gateway", "hint": "A network point serving as an entrance to another network"},
        {"word": "security", "hint": "Measures protecting digital assets from threats and breaches"},
        {"word": "software", "hint": "Non-tangible programs and applications running on hardware"},
        {"word": "hardware", "hint": "Physical electronic and mechanical parts of a computer system"},
        {"word": "terminal", "hint": "Text-based user interface for communicating with an operating system"},
        {"word": "function", "hint": "A named block of reusable code that takes input and returns output"},
        {"word": "variable", "hint": "A named storage location whose value can vary during execution"},
        {"word": "protocol", "hint": "An established standard governing communication between systems"},
        {"word": "database", "hint": "An organized structured collection of electronically stored data"},
    ],
    "hard": [
        {"word": "algorithm", "hint": "A well-defined step-by-step procedure for solving a computational problem"},
        {"word": "framework", "hint": "A comprehensive foundation that provides structure for building apps"},
        {"word": "developer", "hint": "A professional software engineer who writes and maintains code"},
        {"word": "interface", "hint": "A shared boundary across which components exchange information"},
        {"word": "processor", "hint": "The primary integrated circuit performing fundamental calculations"},
        {"word": "bandwidth", "hint": "The maximum rate of data transfer across a network connection"},
        {"word": "dashboard", "hint": "A visual interface summarizing metrics, key stats, and statuses"},
        {"word": "analytics", "hint": "The systematic computational exploration and interpretation of data"},
        {"word": "microchip", "hint": "A microscopic collection of transistors built on silicon"},
        {"word": "hyperlink", "hint": "A reference in a digital document that leads directly to other data"},
        {"word": "blueprint", "hint": "A detailed technical design or architectural plan for a system"},
        {"word": "encryption", "hint": "The cryptographic process of encoding data to prevent unauthorized access"},
        {"word": "javascript", "hint": "The omnipresent scripting language driving modern web browsers"},
        {"word": "middleware", "hint": "Software acting as a bridge between an OS/database and applications"},
        {"word": "repository", "hint": "A centralized archive where source code and revision histories are kept"},
        {"word": "stylesheet", "hint": "A document defining visual design, layout, and colors for web pages"},
        {"word": "automation", "hint": "The use of scripts or technology to execute workflows without human effort"},
        {"word": "kubernetes", "hint": "An open-source container orchestration platform originally by Google"},
        {"word": "responsive", "hint": "UI design methodology allowing layouts to adapt dynamically to screen sizes"},
        {"word": "cybersecurity", "hint": "Practice of defending digital networks and devices from malicious attacks"},
        {"word": "architecture", "hint": "The high-level structural design and blueprint of a complex software system"},
        {"word": "cryptography", "hint": "The mathematical science of securing communications and data"},
        {"word": "infrastructure", "hint": "Foundational physical and virtual systems supporting IT services"},
    ],
}

DIFFICULTIES = ("easy", "medium", "hard")
DEFAULT_MAX_ATTEMPTS = 6

BASE_POINTS = {
    "easy": 100,
    "medium": 200,
    "hard": 300,
}
BONUS_PER_ATTEMPT = 25
HINT_PENALTY = 30


class GameLogic:
    """Core state and mechanics for a game of Hangman."""

    def __init__(self, difficulty: str = "medium") -> None:
        """Initialize the game logic engine.

        Args:
            difficulty: Starting difficulty level ('easy', 'medium', 'hard').
        """
        self.difficulty: str = difficulty if difficulty in DIFFICULTIES else "medium"
        self.secret_word: str = ""
        self.hint: str = ""
        self.guessed_letters: Set[str] = set()
        self.correct_guesses: Set[str] = set()
        self.incorrect_guesses: List[str] = []
        self.max_attempts: int = DEFAULT_MAX_ATTEMPTS
        self.attempts_left: int = DEFAULT_MAX_ATTEMPTS
        self.hint_used: bool = False
        self.game_over: bool = False
        self.is_won: bool = False

        # Track last chosen word per difficulty to prevent immediate repetition
        self._last_word: Dict[str, str] = {}

        # Pick initial word
        self.start_new_game(self.difficulty)

    def start_new_game(self, difficulty: Optional[str] = None) -> None:
        """Start a new game round with fresh state.

        Args:
            difficulty: Optional new difficulty level. If None, reuses current.
        """
        if difficulty in DIFFICULTIES:
            self.difficulty = difficulty

        word_list = WORD_BANK.get(self.difficulty, WORD_BANK["medium"])
        last = self._last_word.get(self.difficulty)

        # Filter out the immediately previous word if alternative words exist
        choices = [entry for entry in word_list if entry["word"] != last]
        if not choices:
            choices = word_list

        selected = random.choice(choices)
        self.secret_word = selected["word"].lower().strip()
        self.hint = selected["hint"]
        self._last_word[self.difficulty] = self.secret_word

        self.guessed_letters.clear()
        self.correct_guesses.clear()
        self.incorrect_guesses.clear()
        self.max_attempts = DEFAULT_MAX_ATTEMPTS
        self.attempts_left = DEFAULT_MAX_ATTEMPTS
        self.hint_used = False
        self.game_over = False
        self.is_won = False

    def make_guess(self, raw_input: str) -> Dict[str, object]:
        """Process a letter guess.

        Args:
            raw_input: The character guessed by player.

        Returns:
            Dictionary describing result status:
            - status: 'correct', 'incorrect', 'repeated', 'invalid', 'game_over'
            - letter: guessed letter (if valid)
            - is_won: boolean
            - game_over: boolean
            - attempts_left: remaining count
            - message: human-readable feedback
        """
        if self.game_over:
            return {
                "status": "game_over",
                "message": "Game is already finished. Start a new round to play.",
                "game_over": True,
                "is_won": self.is_won,
                "attempts_left": self.attempts_left,
            }

        letter = raw_input.strip().lower()

        # Reject non-single-alphabet input
        if len(letter) != 1 or not letter.isalpha() or not letter.isascii():
            return {
                "status": "invalid",
                "message": "Please enter a single English alphabet letter (A-Z).",
                "game_over": False,
                "is_won": False,
                "attempts_left": self.attempts_left,
            }

        # Check for duplicate guesses
        if letter in self.guessed_letters:
            return {
                "status": "repeated",
                "letter": letter,
                "message": f"Letter '{letter.upper()}' has already been guessed.",
                "game_over": False,
                "is_won": False,
                "attempts_left": self.attempts_left,
            }

        self.guessed_letters.add(letter)

        # Check if guess is correct
        if letter in self.secret_word:
            self.correct_guesses.add(letter)

            # Win condition: all unique letters in secret word are guessed
            if set(self.secret_word).issubset(self.correct_guesses):
                self.game_over = True
                self.is_won = True
                return {
                    "status": "correct",
                    "letter": letter,
                    "message": f"Great job! '{letter.upper()}' is in the word.",
                    "game_over": True,
                    "is_won": True,
                    "attempts_left": self.attempts_left,
                }

            return {
                "status": "correct",
                "letter": letter,
                "message": f"Nice! '{letter.upper()}' is in the word.",
                "game_over": False,
                "is_won": False,
                "attempts_left": self.attempts_left,
            }

        # Incorrect guess
        self.incorrect_guesses.append(letter)
        self.attempts_left -= 1

        if self.attempts_left <= 0:
            self.game_over = True
            self.is_won = False
            return {
                "status": "incorrect",
                "letter": letter,
                "message": f"Sorry! '{letter.upper()}' is not in the word.",
                "game_over": True,
                "is_won": False,
                "attempts_left": 0,
            }

        return {
            "status": "incorrect",
            "letter": letter,
            "message": f"Sorry! '{letter.upper()}' is not in the word.",
            "game_over": False,
            "is_won": False,
            "attempts_left": self.attempts_left,
        }

    def use_hint(self) -> str:
        """Activate the hint for the current round.

        Returns:
            The hint string.
        """
        self.hint_used = True
        return self.hint

    def get_display_slots(self) -> List[Optional[str]]:
        """Get the current word slots for UI rendering.

        Returns:
            List of characters for revealed letters, or None for hidden slots.
        """
        return [ch.upper() if ch in self.correct_guesses else None for ch in self.secret_word]

    def get_display_string(self) -> str:
        """Get formatted display string with revealed letters or underscores.

        Returns:
            Space-delimited string (e.g. 'P Y _ H O N').
        """
        return " ".join(ch.upper() if ch in self.correct_guesses else "_" for ch in self.secret_word)

    def calculate_score_breakdown(self) -> Dict[str, int]:
        """Calculate detailed score breakdown for the round.

        Returns:
            Dictionary with base score, attempts bonus, hint penalty, and total.
        """
        if not self.is_won:
            return {"base": 0, "bonus": 0, "penalty": 0, "total": 0}

        base = BASE_POINTS.get(self.difficulty, 200)
        bonus = self.attempts_left * BONUS_PER_ATTEMPT
        penalty = HINT_PENALTY if self.hint_used else 0
        total = max(10, base + bonus - penalty)

        return {
            "base": base,
            "bonus": bonus,
            "penalty": -penalty,
            "total": total,
        }
