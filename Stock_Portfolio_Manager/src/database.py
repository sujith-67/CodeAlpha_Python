"""
database.py - SQLite Database Management
=========================================
Handles all persistent storage operations for the Stock Portfolio Manager.
Uses parameterized queries to ensure data integrity and prevent SQL injection.
"""

import sqlite3
import os
from datetime import datetime
from contextlib import contextmanager
from typing import List, Dict, Optional, Any, Generator


class DatabaseManager:
    """Manages the SQLite database connection, tables, holdings, and transactions."""

    def __init__(self, db_path: Optional[str] = None):
        """Initialize database path and ensure tables exist."""
        if db_path is None:
            # Default to data/portfolio.db relative to project root
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            data_dir = os.path.join(base_dir, "data")
            os.makedirs(data_dir, exist_ok=True)
            self.db_path = os.path.join(data_dir, "portfolio.db")
        else:
            self.db_path = db_path
            os.makedirs(os.path.dirname(os.path.abspath(self.db_path)), exist_ok=True)

        # Initialize the database schema
        self.init_db()

    @contextmanager
    def _get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Context manager that opens and guarantees connection closure."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def init_db(self) -> None:
        """Create holdings and transactions tables if they do not exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Holdings table: Stores currently owned stocks.
            # Symbol is PRIMARY KEY to avoid duplicate records.
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS holdings (
                    symbol TEXT PRIMARY KEY,
                    company_name TEXT NOT NULL,
                    quantity INTEGER NOT NULL CHECK (quantity > 0),
                    price REAL NOT NULL,
                    last_updated TEXT NOT NULL
                )
            """)

            # Transactions table: Keeps an audit trail of all buy and sell actions.
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    company_name TEXT NOT NULL,
                    transaction_type TEXT NOT NULL,
                    quantity INTEGER NOT NULL CHECK (quantity > 0),
                    price REAL NOT NULL,
                    total_value REAL NOT NULL
                )
            """)

            conn.commit()

    def get_holdings(self) -> List[Dict[str, Any]]:
        """Retrieve all currently held stocks ordered alphabetically by symbol."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT symbol, company_name, quantity, price, last_updated
                    FROM holdings
                    ORDER BY symbol ASC
                """)
                rows = cursor.fetchall()
                holdings = []
                for row in rows:
                    holdings.append({
                        "symbol": row["symbol"],
                        "company_name": row["company_name"],
                        "quantity": row["quantity"],
                        "price": float(row["price"]),
                        "total_value": round(row["quantity"] * float(row["price"]), 2),
                        "last_updated": row["last_updated"]
                    })
                return holdings
        except sqlite3.Error as e:
            print(f"[Database Error in get_holdings]: {e}")
            return []

    def get_holding(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Retrieve a single holding by symbol, or None if not owned."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT symbol, company_name, quantity, price, last_updated
                    FROM holdings
                    WHERE symbol = ?
                """, (symbol.upper(),))
                row = cursor.fetchone()
                if row:
                    return {
                        "symbol": row["symbol"],
                        "company_name": row["company_name"],
                        "quantity": row["quantity"],
                        "price": float(row["price"]),
                        "total_value": round(row["quantity"] * float(row["price"]), 2),
                        "last_updated": row["last_updated"]
                    }
                return None
        except sqlite3.Error as e:
            print(f"[Database Error in get_holding]: {e}")
            return None

    def add_shares(self, symbol: str, company_name: str, quantity: int, price: float) -> bool:
        """
        Add shares of a stock to the portfolio.
        If already held, increments quantity; otherwise inserts a new record.
        """
        if quantity <= 0:
            return False

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                # Check if stock exists
                cursor.execute("SELECT quantity FROM holdings WHERE symbol = ?", (symbol.upper(),))
                existing = cursor.fetchone()

                if existing:
                    new_qty = existing["quantity"] + quantity
                    cursor.execute("""
                        UPDATE holdings
                        SET quantity = ?, price = ?, last_updated = ?
                        WHERE symbol = ?
                    """, (new_qty, price, now_str, symbol.upper()))
                else:
                    cursor.execute("""
                        INSERT INTO holdings (symbol, company_name, quantity, price, last_updated)
                        VALUES (?, ?, ?, ?, ?)
                    """, (symbol.upper(), company_name, quantity, price, now_str))

                conn.commit()
                return True
        except sqlite3.Error as e:
            print(f"[Database Error in add_shares]: {e}")
            return False

    def remove_shares(self, symbol: str, quantity: int) -> bool:
        """
        Reduce shares of a stock or delete the holding if all shares are sold.
        Returns False if the user tries to sell more shares than owned.
        """
        if quantity <= 0:
            return False

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT quantity FROM holdings WHERE symbol = ?", (symbol.upper(),))
                existing = cursor.fetchone()

                if not existing or existing["quantity"] < quantity:
                    return False

                current_qty = existing["quantity"]
                if current_qty == quantity:
                    # Sold all shares - remove record
                    cursor.execute("DELETE FROM holdings WHERE symbol = ?", (symbol.upper(),))
                else:
                    new_qty = current_qty - quantity
                    cursor.execute("""
                        UPDATE holdings
                        SET quantity = ?, last_updated = ?
                        WHERE symbol = ?
                    """, (new_qty, now_str, symbol.upper()))

                conn.commit()
                return True
        except sqlite3.Error as e:
            print(f"[Database Error in remove_shares]: {e}")
            return False

    def record_transaction(
        self,
        symbol: str,
        company_name: str,
        transaction_type: str,
        quantity: int,
        price: float
    ) -> bool:
        """Record an audit entry for a BUY or SELL transaction."""
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        total_value = round(quantity * price, 2)
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO transactions (
                        timestamp, symbol, company_name, transaction_type, quantity, price, total_value
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    now_str,
                    symbol.upper(),
                    company_name,
                    transaction_type.upper(),
                    quantity,
                    price,
                    total_value
                ))
                conn.commit()
                return True
        except sqlite3.Error as e:
            print(f"[Database Error in record_transaction]: {e}")
            return False

    def get_transactions(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Retrieve past transactions in reverse chronological order."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                query = """
                    SELECT id, timestamp, symbol, company_name, transaction_type, quantity, price, total_value
                    FROM transactions
                    ORDER BY id DESC
                """
                if limit and limit > 0:
                    query += f" LIMIT {int(limit)}"

                cursor.execute(query)
                rows = cursor.fetchall()
                txns = []
                for row in rows:
                    txns.append({
                        "id": row["id"],
                        "timestamp": row["timestamp"],
                        "symbol": row["symbol"],
                        "company_name": row["company_name"],
                        "transaction_type": row["transaction_type"],
                        "quantity": row["quantity"],
                        "price": float(row["price"]),
                        "total_value": float(row["total_value"])
                    })
                return txns
        except sqlite3.Error as e:
            print(f"[Database Error in get_transactions]: {e}")
            return []

    def reset_database(self) -> bool:
        """
        Clear all holdings and transaction history safely without deleting the database file.
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM holdings")
                cursor.execute("DELETE FROM transactions")
                # Reset SQLite autoincrement sequence
                cursor.execute("DELETE FROM sqlite_sequence WHERE name IN ('holdings', 'transactions')")
                conn.commit()
                return True
        except sqlite3.Error as e:
            print(f"[Database Error in reset_database]: {e}")
            return False
