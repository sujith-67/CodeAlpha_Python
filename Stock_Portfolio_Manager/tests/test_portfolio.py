"""
test_portfolio.py - Unit tests for PortfolioManager Business Logic
===================================================================
Tests stock catalog retrieval, sample pricing, input validation, buy/sell
execution, overselling protection, financial calculations, and CSV exports
using a disposable temporary database.
"""

import os
import tempfile
import unittest
from src.database import DatabaseManager
from src.portfolio import PortfolioManager, DEFAULT_STOCKS


class TestPortfolioManager(unittest.TestCase):
    """Test suite for business logic, trading rules, and portfolio metrics."""

    def setUp(self):
        """Set up a disposable database and PortfolioManager instance."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "test_portfolio.db")
        self.db = DatabaseManager(self.db_path)
        self.pm = PortfolioManager(self.db)

    def tearDown(self):
        """Clean up temporary directory."""
        self.temp_dir.cleanup()

    def test_stock_catalog_and_sample_prices(self):
        """Verify predefined stock catalog and fixed sample prices."""
        catalog = self.pm.get_catalog()
        self.assertIn("AAPL", catalog)
        self.assertIn("TSLA", catalog)
        self.assertIn("GOOGL", catalog)
        self.assertIn("MSFT", catalog)
        self.assertIn("AMZN", catalog)

        self.assertEqual(self.pm.get_stock_price("AAPL"), 180.0)
        self.assertEqual(self.pm.get_stock_price("TSLA"), 250.0)
        self.assertEqual(self.pm.get_stock_price("GOOGL"), 140.0)
        self.assertEqual(self.pm.get_stock_price("MSFT"), 420.0)
        self.assertEqual(self.pm.get_stock_price("AMZN"), 190.0)
        self.assertIsNone(self.pm.get_stock_price("UNKNOWN"))

    def test_validate_quantity(self):
        """Verify quantity validation rules."""
        # Valid positive integers
        valid, qty, msg = self.pm.validate_quantity("10")
        self.assertTrue(valid)
        self.assertEqual(qty, 10)

        valid, qty, msg = self.pm.validate_quantity(5)
        self.assertTrue(valid)
        self.assertEqual(qty, 5)

        # Invalid cases
        self.assertFalse(self.pm.validate_quantity("0")[0])
        self.assertFalse(self.pm.validate_quantity("-5")[0])
        self.assertFalse(self.pm.validate_quantity("abc")[0])
        self.assertFalse(self.pm.validate_quantity("")[0])
        self.assertFalse(self.pm.validate_quantity("3.14")[0])

    def test_buy_stock_success_and_validation(self):
        """Verify buying shares of approved stocks and rejection of unapproved stocks."""
        success, msg = self.pm.buy_stock("AAPL", 5)
        self.assertTrue(success)
        self.assertIn("Successfully purchased", msg)

        # Verify holding updated
        holding = self.db.get_holding("AAPL")
        self.assertIsNotNone(holding)
        self.assertEqual(holding["quantity"], 5)
        self.assertEqual(holding["total_value"], 5 * 180.0)

        # Invalid stock symbol
        fail, err = self.pm.buy_stock("INVALID", 10)
        self.assertFalse(fail)

        # Invalid quantity
        fail2, err2 = self.pm.buy_stock("AAPL", 0)
        self.assertFalse(fail2)

    def test_sell_stock_and_overselling_prevention(self):
        """Verify partial selling, overselling prevention, and selling unowned stock."""
        self.pm.buy_stock("TSLA", 10)

        # Overselling prevention
        fail, err = self.pm.sell_stock("TSLA", 15)
        self.assertFalse(fail)
        self.assertIn("Cannot sell 15 shares", err)

        # Selling stock not owned
        fail_unowned, err_unowned = self.pm.sell_stock("MSFT", 1)
        self.assertFalse(fail_unowned)
        self.assertIn("do not currently own", err_unowned)

        # Partial sell
        success, msg = self.pm.sell_stock("TSLA", 4)
        self.assertTrue(success)
        holding = self.db.get_holding("TSLA")
        self.assertEqual(holding["quantity"], 6)

        # Full liquidation
        success2, msg2 = self.pm.sell_stock("TSLA", 6)
        self.assertTrue(success2)
        self.assertIsNone(self.db.get_holding("TSLA"))

    def test_portfolio_summary_and_allocations(self):
        """Verify summary calculations, aggregate totals, and allocation percentages."""
        # Empty portfolio initially
        summary = self.pm.get_portfolio_summary()
        self.assertEqual(summary["total_value"], 0.0)
        self.assertEqual(summary["total_shares"], 0)
        self.assertEqual(summary["total_stocks"], 0)
        self.assertIsNone(summary["top_holding"])

        # Buy 10 AAPL ($1,800) and 10 TSLA ($2,500) -> Total $4,300
        self.pm.buy_stock("AAPL", 10)
        self.pm.buy_stock("TSLA", 10)

        updated_summary = self.pm.get_portfolio_summary()
        self.assertEqual(updated_summary["total_value"], 4300.0)
        self.assertEqual(updated_summary["total_shares"], 20)
        self.assertEqual(updated_summary["total_stocks"], 2)
        self.assertEqual(updated_summary["top_holding"]["symbol"], "TSLA")

        # Allocation checks
        holdings = updated_summary["holdings"]
        for h in holdings:
            if h["symbol"] == "AAPL":
                self.assertAlmostEqual(h["allocation_pct"], (1800 / 4300) * 100, places=1)
            elif h["symbol"] == "TSLA":
                self.assertAlmostEqual(h["allocation_pct"], (2500 / 4300) * 100, places=1)

    def test_csv_exports(self):
        """Verify RFC-compliant export of holdings snapshot and transaction audit log."""
        self.pm.buy_stock("MSFT", 2)
        self.pm.buy_stock("GOOGL", 5)

        holdings_csv = os.path.join(self.temp_dir.name, "holdings.csv")
        success, msg = self.pm.export_portfolio_csv(holdings_csv)
        self.assertTrue(success)
        self.assertTrue(os.path.exists(holdings_csv))

        tx_csv = os.path.join(self.temp_dir.name, "transactions.csv")
        success_tx, msg_tx = self.pm.export_transactions_csv(tx_csv)
        self.assertTrue(success_tx)
        self.assertTrue(os.path.exists(tx_csv))


if __name__ == "__main__":
    unittest.main()
