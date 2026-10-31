"""
test_database.py - Unit tests for SQLite DatabaseManager
=========================================================
Tests database initialization, schema creation, adding/removing shares,
transaction logging, audit history queries, and reset operations using
a disposable temporary database.
"""

import os
import tempfile
import unittest
from src.database import DatabaseManager


class TestDatabaseManager(unittest.TestCase):
    """Test suite for SQLite database operations and schema integrity."""

    def setUp(self):
        """Create a disposable SQLite database in a temporary directory."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "test_portfolio.db")
        self.db = DatabaseManager(self.db_path)

    def tearDown(self):
        """Clean up disposable test directory and database file."""
        self.temp_dir.cleanup()

    def test_schema_initialization(self):
        """Verify that tables 'holdings' and 'transactions' are created on init."""
        self.assertTrue(os.path.exists(self.db_path))
        holdings = self.db.get_holdings()
        self.assertEqual(len(holdings), 0)
        transactions = self.db.get_transactions()
        self.assertEqual(len(transactions), 0)

    def test_add_shares_new_and_existing(self):
        """Verify adding shares creates a new holding and increments existing."""
        # Add new holding
        success = self.db.add_shares("AAPL", "Apple Inc.", 10, 180.0)
        self.assertTrue(success)
        holding = self.db.get_holding("AAPL")
        self.assertIsNotNone(holding)
        self.assertEqual(holding["quantity"], 10)
        self.assertEqual(holding["total_value"], 1800.0)

        # Add additional shares to existing holding
        success2 = self.db.add_shares("AAPL", "Apple Inc.", 5, 180.0)
        self.assertTrue(success2)
        holding_updated = self.db.get_holding("AAPL")
        self.assertEqual(holding_updated["quantity"], 15)
        self.assertEqual(holding_updated["total_value"], 2700.0)

    def test_remove_shares_partial_and_full(self):
        """Verify partial share removal and complete liquidation when quantity reaches zero."""
        self.db.add_shares("TSLA", "Tesla Inc.", 10, 250.0)

        # Partial removal
        success = self.db.remove_shares("TSLA", 4)
        self.assertTrue(success)
        holding = self.db.get_holding("TSLA")
        self.assertIsNotNone(holding)
        self.assertEqual(holding["quantity"], 6)

        # Full removal (liquidate remaining 6)
        success_full = self.db.remove_shares("TSLA", 6)
        self.assertTrue(success_full)
        holding_empty = self.db.get_holding("TSLA")
        self.assertIsNone(holding_empty)

    def test_transaction_logging(self):
        """Verify recording and querying transaction audit entries."""
        self.db.record_transaction("AAPL", "Apple Inc.", "BUY", 10, 180.0)
        self.db.record_transaction("MSFT", "Microsoft Corporation", "BUY", 5, 420.0)
        self.db.record_transaction("AAPL", "Apple Inc.", "SELL", 3, 180.0)

        all_tx = self.db.get_transactions()
        self.assertEqual(len(all_tx), 3)

        # Verify transaction fields
        latest = all_tx[0]
        self.assertIn("symbol", latest)
        self.assertIn("transaction_type", latest)
        self.assertIn("quantity", latest)
        self.assertIn("price", latest)
        self.assertIn("total_value", latest)

        # Verify limit parameter
        limited_tx = self.db.get_transactions(limit=2)
        self.assertEqual(len(limited_tx), 2)

    def test_database_persistence_across_instances(self):
        """Verify that data persists when reconnecting with a new DatabaseManager instance."""
        self.db.add_shares("GOOGL", "Alphabet Inc.", 20, 140.0)
        self.db.record_transaction("GOOGL", "Alphabet Inc.", "BUY", 20, 140.0)

        # Create new manager pointing to same path
        new_db = DatabaseManager(self.db_path)
        holding = new_db.get_holding("GOOGL")
        self.assertIsNotNone(holding)
        self.assertEqual(holding["quantity"], 20)
        self.assertEqual(len(new_db.get_transactions()), 1)

    def test_reset_database(self):
        """Verify resetting clears holdings and transactions while preserving schema."""
        self.db.add_shares("AMZN", "Amazon.com Inc.", 15, 190.0)
        self.db.record_transaction("AMZN", "Amazon.com Inc.", "BUY", 15, 190.0)

        success = self.db.reset_database()
        self.assertTrue(success)
        self.assertEqual(len(self.db.get_holdings()), 0)
        self.assertEqual(len(self.db.get_transactions()), 0)


if __name__ == "__main__":
    unittest.main()
