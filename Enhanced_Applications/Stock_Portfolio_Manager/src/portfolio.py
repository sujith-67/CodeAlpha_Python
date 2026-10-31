"""
portfolio.py - Business Logic & Portfolio Operations
=====================================================
Contains the core business logic for stock trading, portfolio calculations,
and CSV exports. Keeps logic separate from the user interface.
"""

import csv
from typing import Dict, List, Tuple, Any, Optional
from src.database import DatabaseManager


# Predefined sample stocks and prices matching the original reference program
DEFAULT_STOCKS: Dict[str, Dict[str, Any]] = {
    "AAPL": {"name": "Apple Inc.", "price": 180.0},
    "TSLA": {"name": "Tesla Inc.", "price": 250.0},
    "GOOGL": {"name": "Alphabet Inc.", "price": 140.0},
    "MSFT": {"name": "Microsoft Corporation", "price": 420.0},
    "AMZN": {"name": "Amazon.com Inc.", "price": 190.0},
}


class PortfolioManager:
    """Coordinates portfolio data, trades, calculations, and reporting."""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.stock_catalog = DEFAULT_STOCKS

    def get_catalog(self) -> Dict[str, Dict[str, Any]]:
        """Return the dictionary of available predefined stocks and their prices."""
        return self.stock_catalog

    def get_stock_price(self, symbol: str) -> Optional[float]:
        """Return the fixed sample price for a stock symbol, or None if invalid."""
        stock = self.stock_catalog.get(symbol.upper())
        return stock["price"] if stock else None

    def get_stock_name(self, symbol: str) -> str:
        """Return the friendly company name for a symbol."""
        stock = self.stock_catalog.get(symbol.upper())
        return stock["name"] if stock else symbol.upper()

    def validate_quantity(self, quantity_input: Any) -> Tuple[bool, int, str]:
        """
        Validate that quantity is a positive whole number greater than 0.
        Returns: (is_valid, parsed_quantity, error_message)
        """
        if isinstance(quantity_input, str):
            quantity_input = quantity_input.strip()

        if not quantity_input:
            return False, 0, "Quantity cannot be empty."

        try:
            qty = int(quantity_input)
            if qty <= 0:
                return False, 0, "Quantity must be an integer greater than 0."
            return True, qty, ""
        except (ValueError, TypeError):
            return False, 0, "Please enter a valid whole number for quantity."

    def buy_stock(self, symbol: str, quantity: int) -> Tuple[bool, str]:
        """
        Buy or add shares of a stock.
        Updates persistent database and records the transaction.
        """
        sym = symbol.upper()
        if sym not in self.stock_catalog:
            return False, f"Stock '{symbol}' is not in the approved stock list."

        if quantity <= 0:
            return False, "Quantity must be greater than 0."

        stock_info = self.stock_catalog[sym]
        price = stock_info["price"]
        company_name = stock_info["name"]
        total_cost = quantity * price

        success = self.db.add_shares(sym, company_name, quantity, price)
        if success:
            self.db.record_transaction(
                symbol=sym,
                company_name=company_name,
                transaction_type="BUY",
                quantity=quantity,
                price=price
            )
            return True, f"Successfully purchased {quantity} share(s) of {sym} for ${total_cost:,.2f}."
        else:
            return False, "Database error: Could not complete purchase."

    def sell_stock(self, symbol: str, quantity: int) -> Tuple[bool, str]:
        """
        Sell or remove shares of a stock.
        Ensures the user owns enough shares before executing the transaction.
        """
        sym = symbol.upper()
        if sym not in self.stock_catalog:
            return False, f"Stock '{symbol}' is not recognized."

        if quantity <= 0:
            return False, "Quantity must be greater than 0."

        holding = self.db.get_holding(sym)
        if not holding:
            return False, f"You do not currently own any shares of {sym}."

        owned_qty = holding["quantity"]
        if quantity > owned_qty:
            return False, (
                f"Cannot sell {quantity} shares of {sym}. "
                f"You currently only hold {owned_qty} share(s)."
            )

        price = self.stock_catalog[sym]["price"]
        company_name = self.stock_catalog[sym]["name"]
        total_proceeds = quantity * price

        success = self.db.remove_shares(sym, quantity)
        if success:
            self.db.record_transaction(
                symbol=sym,
                company_name=company_name,
                transaction_type="SELL",
                quantity=quantity,
                price=price
            )
            remaining = owned_qty - quantity
            msg = (
                f"Successfully sold {quantity} share(s) of {sym} for ${total_proceeds:,.2f}. "
                f"Remaining shares: {remaining}."
            )
            return True, msg
        else:
            return False, "Database error: Could not complete sale."

    def get_portfolio_summary(self) -> Dict[str, Any]:
        """
        Compute portfolio statistics: total value, total stocks, total shares,
        and per-holding allocation percentages.
        """
        holdings = self.db.get_holdings()

        total_value = sum(h["total_value"] for h in holdings)
        total_shares = sum(h["quantity"] for h in holdings)
        total_stocks = len(holdings)

        # Calculate allocation percentage for each holding
        for h in holdings:
            if total_value > 0:
                h["allocation_pct"] = round((h["total_value"] / total_value) * 100, 2)
            else:
                h["allocation_pct"] = 0.0

        # Find top holding if any
        top_holding = None
        if holdings:
            sorted_holdings = sorted(holdings, key=lambda x: x["total_value"], reverse=True)
            top_holding = sorted_holdings[0]

        return {
            "total_value": total_value,
            "total_shares": total_shares,
            "total_stocks": total_stocks,
            "holdings": holdings,
            "top_holding": top_holding,
        }

    def get_transactions(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Retrieve recent or all transactions."""
        return self.db.get_transactions(limit=limit)

    def reset_portfolio(self) -> Tuple[bool, str]:
        """Reset the portfolio by clearing holdings and transaction history."""
        success = self.db.reset_database()
        if success:
            return True, "Portfolio and transaction history have been reset successfully."
        else:
            return False, "Failed to reset portfolio due to a database error."

    def export_portfolio_csv(self, file_path: str) -> Tuple[bool, str]:
        """Export current portfolio holdings to a CSV file."""
        try:
            summary = self.get_portfolio_summary()
            holdings = summary["holdings"]

            with open(file_path, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                # Write header
                writer.writerow([
                    "Symbol",
                    "Company Name",
                    "Shares Owned",
                    "Sample Price ($)",
                    "Total Value ($)",
                    "Portfolio Allocation (%)",
                    "Last Updated"
                ])

                # Write rows
                for h in holdings:
                    writer.writerow([
                        h["symbol"],
                        h["company_name"],
                        h["quantity"],
                        f"{h['price']:.2f}",
                        f"{h['total_value']:.2f}",
                        f"{h['allocation_pct']:.2f}%",
                        h["last_updated"]
                    ])

                # Write summary footer row
                writer.writerow([])
                writer.writerow([
                    "TOTAL",
                    f"{summary['total_stocks']} Stocks Held",
                    summary["total_shares"],
                    "",
                    f"${summary['total_value']:,.2f}",
                    "100.00%",
                    ""
                ])

            return True, f"Portfolio successfully exported to:\n{file_path}"
        except Exception as e:
            return False, f"Failed to export portfolio: {e}"

    def export_transactions_csv(self, file_path: str) -> Tuple[bool, str]:
        """Export complete transaction audit ledger to a CSV file."""
        try:
            transactions = self.get_transactions()

            with open(file_path, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                # Write header
                writer.writerow([
                    "Transaction ID",
                    "Date & Time",
                    "Symbol",
                    "Company Name",
                    "Action",
                    "Quantity",
                    "Unit Price ($)",
                    "Total Amount ($)"
                ])

                # Write rows
                for t in transactions:
                    writer.writerow([
                        t["id"],
                        t["timestamp"],
                        t["symbol"],
                        t["company_name"],
                        t["transaction_type"],
                        t["quantity"],
                        f"{t['price']:.2f}",
                        f"{t['total_value']:.2f}"
                    ])

            return True, f"Transaction history successfully exported to:\n{file_path}"
        except Exception as e:
            return False, f"Failed to export transaction history: {e}"
