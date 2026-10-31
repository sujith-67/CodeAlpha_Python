"""
ui.py - Graphical User Interface for Stock Portfolio Manager
=============================================================
Built with Tkinter and ttkbootstrap, featuring a modern dark financial
dashboard aesthetic with intuitive navigation, live calculation, charts,
and comprehensive portfolio management tools.
"""

import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
from typing import Optional, Dict, Any, List

import ttkbootstrap as tb
from ttkbootstrap.constants import *

from src.portfolio import PortfolioManager, DEFAULT_STOCKS
from src.charts import PortfolioChart


# Visual Styling Constants (Dark Navy Financial Palette)
COLOR_MAIN_BG = "#131b2a"       # Deep dark navy background
COLOR_SIDEBAR_BG = "#1a2436"    # Slightly lighter navy sidebar
COLOR_CARD_BG = "#1e293b"       # Card surface
COLOR_CARD_BORDER = "#334155"   # Border for subtle separation
COLOR_ACCENT_BLUE = "#38bdf8"   # Electric sky blue
COLOR_ACCENT_TEAL = "#34d399"   # Mint teal for gains / buy
COLOR_ACCENT_ROSE = "#f87171"   # Coral rose for sales / sell
COLOR_TEXT_PRIMARY = "#f8fafc"  # Bright white/off-white text
COLOR_TEXT_MUTED = "#94a3b8"    # Muted light grey text
COLOR_HOVER_BG = "#293548"      # Hover state for nav items
COLOR_ACTIVE_NAV = "#0284c7"    # Active navigation indicator


class ModernCard(tb.Frame):
    """Reusable styled card container with a modern dark navy background and subtle border."""

    def __init__(self, parent, padding: int = 15, **kwargs):
        super().__init__(
            parent,
            bootstyle="dark",
            **kwargs
        )
        self.configure(padding=padding)


class MetricCard(tb.Frame):
    """Summary metric card showing an icon, title, main value, and optional subtitle."""

    def __init__(self, parent, icon: str, title: str, value: str, subtitle: str = "", accent_color: str = COLOR_ACCENT_BLUE):
        super().__init__(parent, bootstyle="dark", padding=(16, 12))

        # Header row: Icon and Title
        header_frame = tb.Frame(self, bootstyle="dark")
        header_frame.pack(fill=X, anchor="w")

        tb.Label(
            header_frame,
            text=icon,
            font=("Segoe UI Emoji", 14),
            bootstyle="dark",
            foreground=accent_color
        ).pack(side=LEFT, padx=(0, 8))

        tb.Label(
            header_frame,
            text=title.upper(),
            font=("Segoe UI", 8, "bold"),
            bootstyle="dark",
            foreground=COLOR_TEXT_MUTED
        ).pack(side=LEFT, anchor="center")

        # Main Value
        self.value_label = tb.Label(
            self,
            text=value,
            font=("Segoe UI", 18, "bold"),
            bootstyle="dark",
            foreground=COLOR_TEXT_PRIMARY
        )
        self.value_label.pack(anchor="w", pady=(6, 2))

        # Subtitle
        self.subtitle_label = tb.Label(
            self,
            text=subtitle,
            font=("Segoe UI", 8),
            bootstyle="dark",
            foreground=COLOR_TEXT_MUTED
        )
        self.subtitle_label.pack(anchor="w")

    def update_value(self, value: str, subtitle: Optional[str] = None):
        """Update the displayed metric value and subtitle."""
        self.value_label.configure(text=value)
        if subtitle is not None:
            self.subtitle_label.configure(text=subtitle)


class StockPortfolioApp:
    """Main application interface orchestrating navigation, views, and data binding."""

    def __init__(self, root: tb.Window, portfolio_manager: PortfolioManager):
        self.root = root
        self.manager = portfolio_manager

        # Set window properties
        self.root.title("Stock Portfolio Manager — CodeAlpha")
        self.root.geometry("1180x760")
        self.root.minsize(1040, 680)

        # Try to set window icon
        icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "icon.ico")
        if os.path.exists(icon_path):
            try:
                self.root.iconbitmap(icon_path)
            except Exception:
                pass

        # Navigation state
        self.nav_buttons: Dict[str, tb.Button] = {}
        self.current_view_name = "dashboard"

        # Trading form input variables
        self.buy_stock_var = tk.StringVar()
        self.buy_qty_var = tk.StringVar(value="1")
        self.buy_cost_estimate_var = tk.StringVar(value="$0.00")

        self.sell_stock_var = tk.StringVar()
        self.sell_qty_var = tk.StringVar(value="1")
        self.sell_proceeds_estimate_var = tk.StringVar(value="$0.00")

        # Setup custom dark styles
        self._setup_custom_styles()

        # Build application shell
        self._build_layout()

        # Initial data population
        self.refresh_all_views()

    def _setup_custom_styles(self):
        """Configure ttk styles to enforce polished dark navy UI."""
        style = tb.Style()

        # Style Treeview for dark theme
        style.configure(
            "Treeview",
            background="#1a2436",
            foreground="#f8fafc",
            fieldbackground="#1a2436",
            rowheight=32,
            font=("Segoe UI", 9)
        )
        style.configure(
            "Treeview.Heading",
            background="#131b2a",
            foreground="#94a3b8",
            font=("Segoe UI", 9, "bold"),
            padding=(6, 8)
        )
        style.map(
            "Treeview",
            background=[("selected", "#0284c7")],
            foreground=[("selected", "#ffffff")]
        )

    def _build_layout(self):
        """Build the master frame with a left sidebar and main content display."""
        # Top-level container
        self.main_container = tb.Frame(self.root, bootstyle="dark")
        self.main_container.pack(fill=BOTH, expand=True)

        # 1. Left Sidebar Navigation
        self.sidebar = tb.Frame(self.main_container, bootstyle="dark", width=220)
        self.sidebar.pack(side=LEFT, fill=Y)
        self.sidebar.pack_propagate(False)

        self._build_sidebar()

        # 2. Main Content Area
        self.content_container = tb.Frame(self.main_container, bootstyle="dark", padding=(20, 16))
        self.content_container.pack(side=RIGHT, fill=BOTH, expand=True)

        # Header Bar
        self._build_header_bar()

        # View Pages Container (Stacked Frames)
        self.views_frame = tb.Frame(self.content_container, bootstyle="dark")
        self.views_frame.pack(fill=BOTH, expand=True, pady=(12, 0))

        # Instantiate View Pages
        self.views = {
            "dashboard": self._create_dashboard_view(),
            "portfolio": self._create_portfolio_view(),
            "trade": self._create_trade_view(),
            "history": self._create_history_view(),
            "settings": self._create_settings_view()
        }

        # Bottom Status Bar (built before initial refresh)
        self._build_status_bar()

        # Show Dashboard initially
        self.show_view("dashboard")

    def _build_sidebar(self):
        """Build sidebar logo, navigation links, and student credit footer."""
        # Logo / Brand Frame
        brand_frame = tb.Frame(self.sidebar, bootstyle="dark", padding=(16, 20))
        brand_frame.pack(fill=X)

        title_label = tb.Label(
            brand_frame,
            text="📈 FolioManager",
            font=("Segoe UI", 13, "bold"),
            foreground=COLOR_ACCENT_BLUE,
            bootstyle="dark"
        )
        title_label.pack(anchor="w")

        subtitle_label = tb.Label(
            brand_frame,
            text="Student Portfolio Tracker",
            font=("Segoe UI", 8),
            foreground=COLOR_TEXT_MUTED,
            bootstyle="dark"
        )
        subtitle_label.pack(anchor="w", pady=(2, 0))

        # Separator line
        tb.Separator(self.sidebar, bootstyle="secondary").pack(fill=X, padx=12, pady=(0, 16))

        # Navigation Menu Items
        nav_items = [
            ("dashboard", "📊  Dashboard"),
            ("portfolio", "💼  My Portfolio"),
            ("trade", "🔄  Trade Stocks"),
            ("history", "📜  Transaction History"),
            ("settings", "⚙️  Settings & Tools"),
        ]

        self.nav_container = tb.Frame(self.sidebar, bootstyle="dark")
        self.nav_container.pack(fill=X, padx=10)

        for view_id, label in nav_items:
            btn = tb.Button(
                self.nav_container,
                text=label,
                bootstyle="dark",
                command=lambda v=view_id: self.show_view(v),
                cursor="hand2"
            )
            btn.pack(fill=X, pady=4, ipady=6)
            self.nav_buttons[view_id] = btn

        # Sidebar Footer
        footer_frame = tb.Frame(self.sidebar, bootstyle="dark", padding=(12, 16))
        footer_frame.pack(side=BOTTOM, fill=X)

        tb.Label(
            footer_frame,
            text="CodeAlpha Internship",
            font=("Segoe UI", 8, "bold"),
            foreground=COLOR_TEXT_MUTED,
            bootstyle="dark"
        ).pack(anchor="w")

        tb.Label(
            footer_frame,
            text="Python Desktop v1.0",
            font=("Segoe UI", 7),
            foreground="#64748b",
            bootstyle="dark"
        ).pack(anchor="w")

    def _build_header_bar(self):
        """Top bar displaying current view title, live clock, and quick action buttons."""
        self.header_frame = tb.Frame(self.content_container, bootstyle="dark")
        self.header_frame.pack(fill=X)

        # Title & Subtitle
        title_box = tb.Frame(self.header_frame, bootstyle="dark")
        title_box.pack(side=LEFT, anchor="w")

        self.view_title_label = tb.Label(
            title_box,
            text="Dashboard Overview",
            font=("Segoe UI", 16, "bold"),
            foreground=COLOR_TEXT_PRIMARY,
            bootstyle="dark"
        )
        self.view_title_label.pack(anchor="w")

        self.view_subtitle_label = tb.Label(
            title_box,
            text="Real-time summary of your portfolio performance and holdings.",
            font=("Segoe UI", 9),
            foreground=COLOR_TEXT_MUTED,
            bootstyle="dark"
        )
        self.view_subtitle_label.pack(anchor="w")

        # Header Right Actions: Quick Refresh & Quick Buy shortcut
        actions_box = tb.Frame(self.header_frame, bootstyle="dark")
        actions_box.pack(side=RIGHT, anchor="center")

        refresh_btn = tb.Button(
            actions_box,
            text="🔄 Refresh",
            bootstyle="secondary-outline",
            command=self.refresh_all_views,
            cursor="hand2"
        )
        refresh_btn.pack(side=RIGHT, padx=(6, 0))

        trade_btn = tb.Button(
            actions_box,
            text="➕ New Trade",
            bootstyle="info",
            command=lambda: self.show_view("trade"),
            cursor="hand2"
        )
        trade_btn.pack(side=RIGHT)

    def _build_status_bar(self):
        """Bottom status bar with database and application readiness info."""
        self.status_bar = tb.Frame(self.content_container, bootstyle="dark", padding=(4, 6))
        self.status_bar.pack(side=BOTTOM, fill=X, pady=(8, 0))

        self.status_db_label = tb.Label(
            self.status_bar,
            text="● SQLite Database: Connected (data/portfolio.db)",
            font=("Segoe UI", 8),
            foreground=COLOR_ACCENT_TEAL,
            bootstyle="dark"
        )
        self.status_db_label.pack(side=LEFT)

        self.status_info_label = tb.Label(
            self.status_bar,
            text="Ready",
            font=("Segoe UI", 8),
            foreground=COLOR_TEXT_MUTED,
            bootstyle="dark"
        )
        self.status_info_label.pack(side=RIGHT)

    def set_status(self, message: str):
        """Update the status bar informational message."""
        self.status_info_label.configure(text=message)

    def show_view(self, view_name: str):
        """Switch active view frame and highlight selected sidebar button."""
        self.current_view_name = view_name

        # Hide all view frames and unpack
        for v in self.views.values():
            v.pack_forget()

        # Show target view
        if view_name in self.views:
            self.views[view_name].pack(fill=BOTH, expand=True)

        # Update sidebar button appearances
        for v_id, btn in self.nav_buttons.items():
            if v_id == view_name:
                btn.configure(bootstyle="primary")
            else:
                btn.configure(bootstyle="dark")

        # Update header title and subtitle
        headers = {
            "dashboard": ("Dashboard Overview", "Real-time summary of your portfolio performance and holdings."),
            "portfolio": ("My Portfolio Holdings", "Detailed breakdown of all active stock positions."),
            "trade": ("Trade & Stock Management", "Execute buy and sell transactions using fixed reference prices."),
            "history": ("Transaction Audit History", "Complete historical ledger of all stock purchases and sales."),
            "settings": ("Settings & Data Management", "Export portfolio data or reset the database safely.")
        }
        title, subtitle = headers.get(view_name, ("Portfolio Manager", ""))
        self.view_title_label.configure(text=title)
        self.view_subtitle_label.configure(text=subtitle)

        # Refresh data when switching to any view
        self.refresh_all_views()

    # =========================================================================
    # VIEW 1: DASHBOARD
    # =========================================================================
    def _create_dashboard_view(self) -> tb.Frame:
        page = tb.Frame(self.views_frame, bootstyle="dark")

        # 1. Top Metric Cards Row
        metrics_row = tb.Frame(page, bootstyle="dark")
        metrics_row.pack(fill=X, pady=(0, 14))

        # 4 Metric Cards
        self.card_val = MetricCard(metrics_row, "💰", "Total Portfolio Value", "$0.00", "0 holdings", COLOR_ACCENT_TEAL)
        self.card_val.pack(side=LEFT, fill=X, expand=True, padx=(0, 8))

        self.card_stocks = MetricCard(metrics_row, "🏷️", "Stocks Held", "0", "0% market coverage", COLOR_ACCENT_BLUE)
        self.card_stocks.pack(side=LEFT, fill=X, expand=True, padx=(0, 8))

        self.card_shares = MetricCard(metrics_row, "📦", "Total Shares", "0", "Across all positions", "#a78bfa")
        self.card_shares.pack(side=LEFT, fill=X, expand=True, padx=(0, 8))

        self.card_top = MetricCard(metrics_row, "🏆", "Top Holding", "None", "0.0% of portfolio", "#fbbf24")
        self.card_top.pack(side=LEFT, fill=X, expand=True)

        # 2. Main Body Split: Left Chart | Right Recent Transactions
        split_body = tb.Frame(page, bootstyle="dark")
        split_body.pack(fill=BOTH, expand=True)

        # Left Column: Portfolio Allocation Donut Chart
        left_card = ModernCard(split_body)
        left_card.pack(side=LEFT, fill=BOTH, expand=True, padx=(0, 8))

        chart_header = tb.Frame(left_card, bootstyle="dark")
        chart_header.pack(fill=X, pady=(0, 6))

        tb.Label(
            chart_header,
            text="Portfolio Allocation",
            font=("Segoe UI", 11, "bold"),
            foreground=COLOR_TEXT_PRIMARY,
            bootstyle="dark"
        ).pack(side=LEFT)

        tb.Label(
            chart_header,
            text="By market value",
            font=("Segoe UI", 8),
            foreground=COLOR_TEXT_MUTED,
            bootstyle="dark"
        ).pack(side=LEFT, padx=(8, 0))

        # Embedded Matplotlib Chart Canvas
        self.chart_container = tb.Frame(left_card, bootstyle="dark")
        self.chart_container.pack(fill=BOTH, expand=True)
        self.chart = PortfolioChart(self.chart_container)

        # Right Column: Recent Activity Table
        right_card = ModernCard(split_body)
        right_card.pack(side=RIGHT, fill=BOTH, expand=True)

        recent_header = tb.Frame(right_card, bootstyle="dark")
        recent_header.pack(fill=X, pady=(0, 6))

        tb.Label(
            recent_header,
            text="Recent Activity",
            font=("Segoe UI", 11, "bold"),
            foreground=COLOR_TEXT_PRIMARY,
            bootstyle="dark"
        ).pack(side=LEFT)

        view_all_btn = tb.Button(
            recent_header,
            text="View All →",
            bootstyle="link",
            command=lambda: self.show_view("history"),
            cursor="hand2"
        )
        view_all_btn.pack(side=RIGHT)

        # Recent transactions treeview
        columns = ("time", "symbol", "type", "qty", "total")
        self.recent_tree = tb.Treeview(
            right_card,
            columns=columns,
            show="headings",
            height=8,
            bootstyle="dark"
        )
        self.recent_tree.heading("time", text="Time")
        self.recent_tree.heading("symbol", text="Symbol")
        self.recent_tree.heading("type", text="Action")
        self.recent_tree.heading("qty", text="Shares")
        self.recent_tree.heading("total", text="Amount")

        self.recent_tree.column("time", width=120, anchor="w")
        self.recent_tree.column("symbol", width=65, anchor="center")
        self.recent_tree.column("type", width=65, anchor="center")
        self.recent_tree.column("qty", width=60, anchor="e")
        self.recent_tree.column("total", width=85, anchor="e")

        self.recent_tree.pack(fill=BOTH, expand=True)

        return page

    # =========================================================================
    # VIEW 2: MY PORTFOLIO
    # =========================================================================
    def _create_portfolio_view(self) -> tb.Frame:
        page = tb.Frame(self.views_frame, bootstyle="dark")

        # Top Action Bar
        top_bar = tb.Frame(page, bootstyle="dark")
        top_bar.pack(fill=X, pady=(0, 10))

        tb.Label(
            top_bar,
            text="Current Stock Holdings",
            font=("Segoe UI", 12, "bold"),
            foreground=COLOR_TEXT_PRIMARY,
            bootstyle="dark"
        ).pack(side=LEFT)

        export_btn = tb.Button(
            top_bar,
            text="📥 Export to CSV",
            bootstyle="success-outline",
            command=self._handle_export_portfolio,
            cursor="hand2"
        )
        export_btn.pack(side=RIGHT, padx=(8, 0))

        buy_more_btn = tb.Button(
            top_bar,
            text="➕ Buy More Stocks",
            bootstyle="info",
            command=lambda: self.show_view("trade"),
            cursor="hand2"
        )
        buy_more_btn.pack(side=RIGHT)

        # Main Table Card
        table_card = ModernCard(page, padding=8)
        table_card.pack(fill=BOTH, expand=True)

        # Treeview with full portfolio details
        cols = ("symbol", "company", "quantity", "price", "total_val", "allocation", "updated")
        self.portfolio_tree = tb.Treeview(
            table_card,
            columns=cols,
            show="headings",
            bootstyle="dark"
        )

        self.portfolio_tree.heading("symbol", text="Symbol")
        self.portfolio_tree.heading("company", text="Company Name")
        self.portfolio_tree.heading("quantity", text="Shares Owned")
        self.portfolio_tree.heading("price", text="Sample Price")
        self.portfolio_tree.heading("total_val", text="Total Value")
        self.portfolio_tree.heading("allocation", text="Allocation")
        self.portfolio_tree.heading("updated", text="Last Updated")

        self.portfolio_tree.column("symbol", width=90, anchor="center")
        self.portfolio_tree.column("company", width=220, anchor="w")
        self.portfolio_tree.column("quantity", width=110, anchor="e")
        self.portfolio_tree.column("price", width=110, anchor="e")
        self.portfolio_tree.column("total_val", width=130, anchor="e")
        self.portfolio_tree.column("allocation", width=100, anchor="center")
        self.portfolio_tree.column("updated", width=160, anchor="center")

        # Scrollbar
        scrollbar = tb.Scrollbar(table_card, orient=VERTICAL, command=self.portfolio_tree.yview)
        self.portfolio_tree.configure(yscrollcommand=scrollbar.set)

        self.portfolio_tree.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar.pack(side=RIGHT, fill=Y)

        # Bottom Portfolio Summary Banner
        self.portfolio_summary_banner = tb.Frame(page, bootstyle="dark", padding=(12, 10))
        self.portfolio_summary_banner.pack(fill=X, pady=(10, 0))

        self.port_summary_label = tb.Label(
            self.portfolio_summary_banner,
            text="Total Portfolio Value: $0.00 | 0 Shares across 0 Stocks",
            font=("Segoe UI", 11, "bold"),
            foreground=COLOR_ACCENT_TEAL,
            bootstyle="dark"
        )
        self.port_summary_label.pack(side=LEFT)

        return page

    # =========================================================================
    # VIEW 3: TRADE & STOCK MANAGEMENT
    # =========================================================================
    def _create_trade_view(self) -> tb.Frame:
        page = tb.Frame(self.views_frame, bootstyle="dark")

        # Upper row: Side-by-side Buy and Sell Cards
        forms_row = tb.Frame(page, bootstyle="dark")
        forms_row.pack(fill=X, pady=(0, 12))

        # --- LEFT: BUY CARD ---
        buy_card = ModernCard(forms_row)
        buy_card.pack(side=LEFT, fill=BOTH, expand=True, padx=(0, 8))

        tb.Label(
            buy_card,
            text="➕ Buy / Add Shares",
            font=("Segoe UI", 12, "bold"),
            foreground=COLOR_ACCENT_TEAL,
            bootstyle="dark"
        ).pack(anchor="w", pady=(0, 4))

        tb.Label(
            buy_card,
            text="Purchase new shares or add to your existing holdings.",
            font=("Segoe UI", 8),
            foreground=COLOR_TEXT_MUTED,
            bootstyle="dark"
        ).pack(anchor="w", pady=(0, 12))

        # Stock selection
        tb.Label(buy_card, text="Select Stock:", font=("Segoe UI", 9, "bold"), bootstyle="dark").pack(anchor="w")
        self.buy_combo = tb.Combobox(
            buy_card,
            textvariable=self.buy_stock_var,
            state="readonly",
            bootstyle="info"
        )
        self.buy_combo.pack(fill=X, pady=(3, 8))
        self.buy_combo.bind("<<ComboboxSelected>>", lambda e: self._on_buy_selection_change())

        # Price & Owned info badge
        self.buy_info_label = tb.Label(
            buy_card,
            text="Unit Price: -- | Currently Owned: 0 shares",
            font=("Segoe UI", 8),
            foreground=COLOR_ACCENT_BLUE,
            bootstyle="dark"
        )
        self.buy_info_label.pack(anchor="w", pady=(0, 8))

        # Quantity input
        tb.Label(buy_card, text="Quantity to Buy:", font=("Segoe UI", 9, "bold"), bootstyle="dark").pack(anchor="w")
        qty_box = tb.Frame(buy_card, bootstyle="dark")
        qty_box.pack(fill=X, pady=(3, 8))

        self.buy_qty_entry = tb.Entry(qty_box, textvariable=self.buy_qty_var, bootstyle="info")
        self.buy_qty_entry.pack(side=LEFT, fill=X, expand=True)
        self.buy_qty_var.trace_add("write", lambda *args: self._calculate_buy_estimate())

        # Quick quantity increment buttons (+1, +5, +10)
        for inc in [1, 5, 10]:
            tb.Button(
                qty_box,
                text=f"+{inc}",
                bootstyle="secondary-outline",
                command=lambda val=inc: self._increment_buy_qty(val),
                cursor="hand2"
            ).pack(side=LEFT, padx=(4, 0))

        # Estimated cost display
        cost_box = tb.Frame(buy_card, bootstyle="dark", padding=(8, 8))
        cost_box.pack(fill=X, pady=(4, 12))

        tb.Label(
            cost_box,
            text="Estimated Total Cost:",
            font=("Segoe UI", 9),
            foreground=COLOR_TEXT_MUTED,
            bootstyle="dark"
        ).pack(side=LEFT)

        self.buy_cost_label = tb.Label(
            cost_box,
            textvariable=self.buy_cost_estimate_var,
            font=("Segoe UI", 12, "bold"),
            foreground=COLOR_ACCENT_TEAL,
            bootstyle="dark"
        )
        self.buy_cost_label.pack(side=RIGHT)

        # Confirm Buy Button
        buy_execute_btn = tb.Button(
            buy_card,
            text="Confirm Purchase",
            bootstyle="success",
            command=self._execute_buy_transaction,
            cursor="hand2"
        )
        buy_execute_btn.pack(fill=X, ipady=4)

        # --- RIGHT: SELL CARD ---
        sell_card = ModernCard(forms_row)
        sell_card.pack(side=RIGHT, fill=BOTH, expand=True)

        tb.Label(
            sell_card,
            text="➖ Sell / Remove Shares",
            font=("Segoe UI", 12, "bold"),
            foreground=COLOR_ACCENT_ROSE,
            bootstyle="dark"
        ).pack(anchor="w", pady=(0, 4))

        tb.Label(
            sell_card,
            text="Sell a selected quantity or liquidate an entire position.",
            font=("Segoe UI", 8),
            foreground=COLOR_TEXT_MUTED,
            bootstyle="dark"
        ).pack(anchor="w", pady=(0, 12))

        # Stock selection (from owned stocks)
        tb.Label(sell_card, text="Select Owned Stock:", font=("Segoe UI", 9, "bold"), bootstyle="dark").pack(anchor="w")
        self.sell_combo = tb.Combobox(
            sell_card,
            textvariable=self.sell_stock_var,
            state="readonly",
            bootstyle="danger"
        )
        self.sell_combo.pack(fill=X, pady=(3, 8))
        self.sell_combo.bind("<<ComboboxSelected>>", lambda e: self._on_sell_selection_change())

        # Owned shares info badge
        self.sell_info_label = tb.Label(
            sell_card,
            text="Available to Sell: 0 shares | Unit Price: --",
            font=("Segoe UI", 8),
            foreground=COLOR_ACCENT_ROSE,
            bootstyle="dark"
        )
        self.sell_info_label.pack(anchor="w", pady=(0, 8))

        # Quantity input
        tb.Label(sell_card, text="Quantity to Sell:", font=("Segoe UI", 9, "bold"), bootstyle="dark").pack(anchor="w")
        sell_qty_box = tb.Frame(sell_card, bootstyle="dark")
        sell_qty_box.pack(fill=X, pady=(3, 8))

        self.sell_qty_entry = tb.Entry(sell_qty_box, textvariable=self.sell_qty_var, bootstyle="danger")
        self.sell_qty_entry.pack(side=LEFT, fill=X, expand=True)
        self.sell_qty_var.trace_add("write", lambda *args: self._calculate_sell_estimate())

        # "Sell Max" button
        sell_max_btn = tb.Button(
            sell_qty_box,
            text="Sell Max",
            bootstyle="danger-outline",
            command=self._set_sell_max,
            cursor="hand2"
        )
        sell_max_btn.pack(side=LEFT, padx=(6, 0))

        # Estimated proceeds display
        proceeds_box = tb.Frame(sell_card, bootstyle="dark", padding=(8, 8))
        proceeds_box.pack(fill=X, pady=(4, 12))

        tb.Label(
            proceeds_box,
            text="Estimated Total Proceeds:",
            font=("Segoe UI", 9),
            foreground=COLOR_TEXT_MUTED,
            bootstyle="dark"
        ).pack(side=LEFT)

        self.sell_proceeds_label = tb.Label(
            proceeds_box,
            textvariable=self.sell_proceeds_estimate_var,
            font=("Segoe UI", 12, "bold"),
            foreground=COLOR_ACCENT_ROSE,
            bootstyle="dark"
        )
        self.sell_proceeds_label.pack(side=RIGHT)

        # Confirm Sell Button
        sell_execute_btn = tb.Button(
            sell_card,
            text="Confirm Sale",
            bootstyle="danger",
            command=self._execute_sell_transaction,
            cursor="hand2"
        )
        sell_execute_btn.pack(fill=X, ipady=4)

        # --- LOWER SECTION: REFERENCE STOCKS CATALOG ---
        catalog_card = ModernCard(page)
        catalog_card.pack(fill=BOTH, expand=True)

        cat_header = tb.Frame(catalog_card, bootstyle="dark")
        cat_header.pack(fill=X, pady=(0, 8))

        tb.Label(
            cat_header,
            text="Predefined Stocks Reference",
            font=("Segoe UI", 11, "bold"),
            foreground=COLOR_TEXT_PRIMARY,
            bootstyle="dark"
        ).pack(side=LEFT)

        tb.Label(
            cat_header,
            text="Fixed sample prices from project specifications",
            font=("Segoe UI", 8),
            foreground=COLOR_TEXT_MUTED,
            bootstyle="dark"
        ).pack(side=LEFT, padx=(8, 0))

        # Catalog Table
        cat_cols = ("symbol", "name", "price", "status", "action")
        self.catalog_tree = tb.Treeview(
            catalog_card,
            columns=cat_cols,
            show="headings",
            height=5,
            bootstyle="dark"
        )
        self.catalog_tree.heading("symbol", text="Symbol")
        self.catalog_tree.heading("name", text="Company Name")
        self.catalog_tree.heading("price", text="Fixed Sample Price")
        self.catalog_tree.heading("status", text="Current Holding")
        self.catalog_tree.heading("action", text="Action")

        self.catalog_tree.column("symbol", width=100, anchor="center")
        self.catalog_tree.column("name", width=260, anchor="w")
        self.catalog_tree.column("price", width=140, anchor="e")
        self.catalog_tree.column("status", width=140, anchor="center")
        self.catalog_tree.column("action", width=120, anchor="center")

        self.catalog_tree.pack(fill=BOTH, expand=True)

        # Double click row to quick select in Buy dropdown
        self.catalog_tree.bind("<Double-1>", self._on_catalog_row_select)

        return page

    # =========================================================================
    # VIEW 4: TRANSACTION HISTORY
    # =========================================================================
    def _create_history_view(self) -> tb.Frame:
        page = tb.Frame(self.views_frame, bootstyle="dark")

        # Top Filter & Export Bar
        top_bar = tb.Frame(page, bootstyle="dark")
        top_bar.pack(fill=X, pady=(0, 10))

        tb.Label(
            top_bar,
            text="All Recorded Transactions",
            font=("Segoe UI", 12, "bold"),
            foreground=COLOR_TEXT_PRIMARY,
            bootstyle="dark"
        ).pack(side=LEFT)

        export_tx_btn = tb.Button(
            top_bar,
            text="📥 Export History (CSV)",
            bootstyle="success-outline",
            command=self._handle_export_transactions,
            cursor="hand2"
        )
        export_tx_btn.pack(side=RIGHT, padx=(8, 0))

        # Filter buttons
        filter_box = tb.Frame(top_bar, bootstyle="dark")
        filter_box.pack(side=RIGHT, padx=(0, 12))

        tb.Label(
            filter_box,
            text="Filter:",
            font=("Segoe UI", 9),
            foreground=COLOR_TEXT_MUTED,
            bootstyle="dark"
        ).pack(side=LEFT, padx=(0, 6))

        self.history_filter_var = tk.StringVar(value="ALL")
        for f_label, f_val in [("All", "ALL"), ("Buy Only", "BUY"), ("Sell Only", "SELL")]:
            tb.Radiobutton(
                filter_box,
                text=f_label,
                value=f_val,
                variable=self.history_filter_var,
                command=self._populate_history_table,
                bootstyle="info-toolbutton"
            ).pack(side=LEFT, padx=2)

        # History Table Card
        hist_card = ModernCard(page, padding=8)
        hist_card.pack(fill=BOTH, expand=True)

        hist_cols = ("id", "time", "symbol", "company", "type", "qty", "price", "total")
        self.history_tree = tb.Treeview(
            hist_card,
            columns=hist_cols,
            show="headings",
            bootstyle="dark"
        )

        self.history_tree.heading("id", text="# ID")
        self.history_tree.heading("time", text="Date & Time")
        self.history_tree.heading("symbol", text="Symbol")
        self.history_tree.heading("company", text="Company")
        self.history_tree.heading("type", text="Action")
        self.history_tree.heading("qty", text="Quantity")
        self.history_tree.heading("price", text="Unit Price")
        self.history_tree.heading("total", text="Total Value")

        self.history_tree.column("id", width=60, anchor="center")
        self.history_tree.column("time", width=150, anchor="center")
        self.history_tree.column("symbol", width=80, anchor="center")
        self.history_tree.column("company", width=200, anchor="w")
        self.history_tree.column("type", width=80, anchor="center")
        self.history_tree.column("qty", width=80, anchor="e")
        self.history_tree.column("price", width=100, anchor="e")
        self.history_tree.column("total", width=120, anchor="e")

        # Scrollbar
        hist_scroll = tb.Scrollbar(hist_card, orient=VERTICAL, command=self.history_tree.yview)
        self.history_tree.configure(yscrollcommand=hist_scroll.set)

        self.history_tree.pack(side=LEFT, fill=BOTH, expand=True)
        hist_scroll.pack(side=RIGHT, fill=Y)

        return page

    # =========================================================================
    # VIEW 5: SETTINGS & TOOLS
    # =========================================================================
    def _create_settings_view(self) -> tb.Frame:
        page = tb.Frame(self.views_frame, bootstyle="dark")

        # Left Column: Export Tools & Database Status
        left_col = tb.Frame(page, bootstyle="dark")
        left_col.pack(side=LEFT, fill=BOTH, expand=True, padx=(0, 8))

        # 1. Export Tools Card
        export_card = ModernCard(left_col)
        export_card.pack(fill=X, pady=(0, 12))

        tb.Label(
            export_card,
            text="📁 Data Export Tools",
            font=("Segoe UI", 12, "bold"),
            foreground=COLOR_ACCENT_BLUE,
            bootstyle="dark"
        ).pack(anchor="w", pady=(0, 4))

        tb.Label(
            export_card,
            text="Export your portfolio data and complete audit logs as standard CSV files.",
            font=("Segoe UI", 8),
            foreground=COLOR_TEXT_MUTED,
            bootstyle="dark"
        ).pack(anchor="w", pady=(0, 10))

        btn_row = tb.Frame(export_card, bootstyle="dark")
        btn_row.pack(fill=X)

        tb.Button(
            btn_row,
            text="📥 Export Current Portfolio (CSV)",
            bootstyle="primary-outline",
            command=self._handle_export_portfolio,
            cursor="hand2"
        ).pack(fill=X, pady=3)

        tb.Button(
            btn_row,
            text="📥 Export Transaction Audit History (CSV)",
            bootstyle="secondary-outline",
            command=self._handle_export_transactions,
            cursor="hand2"
        ).pack(fill=X, pady=3)

        # 2. Database Diagnostics Card
        db_card = ModernCard(left_col)
        db_card.pack(fill=BOTH, expand=True)

        tb.Label(
            db_card,
            text="🗄️ Database Status & Diagnostics",
            font=("Segoe UI", 12, "bold"),
            foreground=COLOR_ACCENT_TEAL,
            bootstyle="dark"
        ).pack(anchor="w", pady=(0, 8))

        self.diag_path_label = tb.Label(
            db_card,
            text=f"Location: {self.manager.db.db_path}",
            font=("Segoe UI", 8),
            foreground=COLOR_TEXT_MUTED,
            bootstyle="dark"
        )
        self.diag_path_label.pack(anchor="w", pady=2)

        self.diag_holdings_label = tb.Label(
            db_card,
            text="Holdings Records: 0",
            font=("Segoe UI", 9),
            foreground=COLOR_TEXT_PRIMARY,
            bootstyle="dark"
        )
        self.diag_holdings_label.pack(anchor="w", pady=2)

        self.diag_tx_label = tb.Label(
            db_card,
            text="Transactions Logged: 0",
            font=("Segoe UI", 9),
            foreground=COLOR_TEXT_PRIMARY,
            bootstyle="dark"
        )
        self.diag_tx_label.pack(anchor="w", pady=2)

        self.diag_size_label = tb.Label(
            db_card,
            text="Database File Size: 0 KB",
            font=("Segoe UI", 8),
            foreground=COLOR_TEXT_MUTED,
            bootstyle="dark"
        )
        self.diag_size_label.pack(anchor="w", pady=2)

        # Right Column: Danger Zone (Reset) & About Project
        right_col = tb.Frame(page, bootstyle="dark")
        right_col.pack(side=RIGHT, fill=BOTH, expand=True)

        # 3. Danger Zone Reset Card
        danger_card = ModernCard(right_col)
        danger_card.pack(fill=X, pady=(0, 12))

        tb.Label(
            danger_card,
            text="⚠️ Danger Zone — Portfolio Reset",
            font=("Segoe UI", 12, "bold"),
            foreground=COLOR_ACCENT_ROSE,
            bootstyle="dark"
        ).pack(anchor="w", pady=(0, 4))

        tb.Label(
            danger_card,
            text=(
                "Permanently delete all active stock holdings and transaction history.\n"
                "The database file itself is preserved, but all data entries will be purged."
            ),
            font=("Segoe UI", 8),
            foreground=COLOR_TEXT_MUTED,
            bootstyle="dark",
            wraplength=420,
            justify=LEFT
        ).pack(anchor="w", pady=(0, 12))

        reset_btn = tb.Button(
            danger_card,
            text="🗑️ Reset Entire Portfolio",
            bootstyle="danger",
            command=self._handle_portfolio_reset,
            cursor="hand2"
        )
        reset_btn.pack(fill=X, ipady=4)

        # 4. About Project Card
        about_card = ModernCard(right_col)
        about_card.pack(fill=BOTH, expand=True)

        tb.Label(
            about_card,
            text="ℹ️ About Stock Portfolio Manager",
            font=("Segoe UI", 12, "bold"),
            foreground=COLOR_TEXT_PRIMARY,
            bootstyle="dark"
        ).pack(anchor="w", pady=(0, 6))

        about_text = (
            "CodeAlpha Python Internship — Task 2 Project\n\n"
            "• Technology: Python 3, Tkinter, ttkbootstrap, Matplotlib, SQLite3\n"
            "• Architecture: Model-View-Controller (MVC) modular design\n"
            "• Predefined Sample Stocks: AAPL ($180), TSLA ($250), GOOGL ($140), "
            "MSFT ($420), AMZN ($190)\n"
            "• Permanent Data Persistence: SQLite with parameterized queries\n"
            "• Visualization: Embedded Matplotlib Donut Chart\n"
            "• Export: RFC-compliant CSV portfolio & transaction audit logs\n\n"
            "Designed and developed as a polished, student-level desktop application."
        )

        tb.Label(
            about_card,
            text=about_text,
            font=("Segoe UI", 8),
            foreground=COLOR_TEXT_MUTED,
            bootstyle="dark",
            justify=LEFT,
            wraplength=420
        ).pack(anchor="w")

        return page

    # =========================================================================
    # DATA REFRESH & POPULATION LOGIC
    # =========================================================================
    def refresh_all_views(self):
        """Fetch latest database data and update all dashboard and view widgets."""
        summary = self.manager.get_portfolio_summary()
        holdings = summary["holdings"]
        transactions = self.manager.get_transactions()

        # 1. Update Dashboard Metric Cards
        self.card_val.update_value(
            f"${summary['total_value']:,.2f}",
            f"{summary['total_stocks']} active stock(s)"
        )
        self.card_stocks.update_value(
            str(summary["total_stocks"]),
            f"{summary['total_stocks']}/5 reference stocks"
        )
        self.card_shares.update_value(
            str(summary["total_shares"]),
            "Total shares in portfolio"
        )

        top_h = summary["top_holding"]
        if top_h:
            self.card_top.update_value(
                f"{top_h['symbol']} ({top_h['allocation_pct']}%)",
                f"${top_h['total_value']:,.2f}"
            )
        else:
            self.card_top.update_value("None", "0.0% of portfolio")

        # 2. Update Matplotlib Allocation Chart
        self.chart.update_chart(holdings)

        # 3. Update Dashboard Recent Transactions Table (last 6)
        for item in self.recent_tree.get_children():
            self.recent_tree.delete(item)

        for tx in transactions[:6]:
            self.recent_tree.insert(
                "",
                "end",
                values=(
                    tx["timestamp"],
                    tx["symbol"],
                    tx["transaction_type"],
                    tx["quantity"],
                    f"${tx['total_value']:,.2f}"
                )
            )

        # 4. Update Portfolio View Table
        for item in self.portfolio_tree.get_children():
            self.portfolio_tree.delete(item)

        for h in holdings:
            self.portfolio_tree.insert(
                "",
                "end",
                values=(
                    h["symbol"],
                    h["company_name"],
                    h["quantity"],
                    f"${h['price']:,.2f}",
                    f"${h['total_value']:,.2f}",
                    f"{h['allocation_pct']:.1f}%",
                    h["last_updated"]
                )
            )

        self.port_summary_label.configure(
            text=f"Total Portfolio Value: ${summary['total_value']:,.2f}  |  "
                 f"{summary['total_shares']} Shares across {summary['total_stocks']} Stocks"
        )

        # 5. Update Trade View Dropdowns & Predefined Catalog
        self._populate_trade_dropdowns(holdings)
        self._populate_reference_catalog(holdings)

        # 6. Update Transaction History Table
        self._populate_history_table()

        # 7. Update Settings Diagnostics
        self._populate_diagnostics(summary, transactions)

        self.set_status(f"Last updated: {datetime.now().strftime('%H:%M:%S')}")

    def _populate_trade_dropdowns(self, holdings: List[Dict[str, Any]]):
        """Update the stock options available in the Buy and Sell comboboxes."""
        catalog = self.manager.get_catalog()

        # Buy combo options: all available predefined stocks
        buy_options = [f"{sym} — {info['name']} (${info['price']:.2f})" for sym, info in catalog.items()]
        self.buy_combo["values"] = buy_options

        if not self.buy_stock_var.get() and buy_options:
            self.buy_combo.current(0)
            self._on_buy_selection_change()

        # Sell combo options: only stocks currently held
        sell_options = []
        for h in holdings:
            sell_options.append(f"{h['symbol']} — {h['company_name']} ({h['quantity']} owned)")
        self.sell_combo["values"] = sell_options

        if sell_options:
            # Keep selection or default to first
            current = self.sell_stock_var.get()
            matched = [opt for opt in sell_options if current and current.split()[0] in opt]
            if matched:
                self.sell_combo.set(matched[0])
            else:
                self.sell_combo.current(0)
            self._on_sell_selection_change()
        else:
            self.sell_stock_var.set("")
            self.sell_info_label.configure(text="No stocks currently owned to sell.")
            self.sell_proceeds_estimate_var.set("$0.00")

    def _populate_reference_catalog(self, holdings: List[Dict[str, Any]]):
        """Update the predefined catalog table showing ownership status."""
        for item in self.catalog_tree.get_children():
            self.catalog_tree.delete(item)

        holdings_map = {h["symbol"]: h["quantity"] for h in holdings}
        catalog = self.manager.get_catalog()

        for sym, info in catalog.items():
            owned_qty = holdings_map.get(sym, 0)
            status_text = f"Owned ({owned_qty} shares)" if owned_qty > 0 else "Not Owned"
            self.catalog_tree.insert(
                "",
                "end",
                values=(
                    sym,
                    info["name"],
                    f"${info['price']:.2f}",
                    status_text,
                    "Double-click to Buy"
                )
            )

    def _populate_history_table(self):
        """Filter and populate the full transaction history table."""
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)

        filter_mode = self.history_filter_var.get()
        all_txns = self.manager.get_transactions()

        for tx in all_txns:
            if filter_mode != "ALL" and tx["transaction_type"] != filter_mode:
                continue

            self.history_tree.insert(
                "",
                "end",
                values=(
                    f"#{tx['id']}",
                    tx["timestamp"],
                    tx["symbol"],
                    tx["company_name"],
                    tx["transaction_type"],
                    tx["quantity"],
                    f"${tx['price']:,.2f}",
                    f"${tx['total_value']:,.2f}"
                )
            )

    def _populate_diagnostics(self, summary: Dict[str, Any], transactions: List[Dict[str, Any]]):
        """Update system diagnostics in the settings view."""
        self.diag_holdings_label.configure(
            text=f"Active Holdings Records: {summary['total_stocks']}"
        )
        self.diag_tx_label.configure(
            text=f"Total Transactions Logged: {len(transactions)}"
        )
        try:
            db_size_bytes = os.path.getsize(self.manager.db.db_path)
            self.diag_size_label.configure(
                text=f"Database File Size: {db_size_bytes / 1024:.1f} KB"
            )
        except OSError:
            self.diag_size_label.configure(text="Database File Size: Unknown")

    # =========================================================================
    # EVENT HANDLERS & CALCULATIONS
    # =========================================================================
    def _get_symbol_from_combo(self, combo_text: str) -> Optional[str]:
        """Extract uppercase ticker symbol from formatted combobox string."""
        if not combo_text:
            return None
        return combo_text.split()[0].upper()

    def _on_buy_selection_change(self):
        """Update price and ownership labels when a stock is selected in Buy form."""
        sym = self._get_symbol_from_combo(self.buy_stock_var.get())
        if not sym:
            return

        price = self.manager.get_stock_price(sym) or 0.0
        holding = self.manager.db.get_holding(sym)
        owned_qty = holding["quantity"] if holding else 0

        self.buy_info_label.configure(
            text=f"Unit Price: ${price:.2f} | Currently Owned: {owned_qty} share(s)"
        )
        self._calculate_buy_estimate()

    def _calculate_buy_estimate(self):
        """Dynamically compute estimated total cost for the buy form."""
        sym = self._get_symbol_from_combo(self.buy_stock_var.get())
        if not sym:
            self.buy_cost_estimate_var.set("$0.00")
            return

        price = self.manager.get_stock_price(sym) or 0.0
        is_valid, qty, _ = self.manager.validate_quantity(self.buy_qty_var.get())
        if is_valid:
            total = qty * price
            self.buy_cost_estimate_var.set(f"${total:,.2f}")
        else:
            self.buy_cost_estimate_var.set("--")

    def _increment_buy_qty(self, delta: int):
        """Increment buy quantity entry by +1, +5, +10."""
        is_valid, current_qty, _ = self.manager.validate_quantity(self.buy_qty_var.get())
        new_qty = (current_qty if is_valid else 0) + delta
        self.buy_qty_var.set(str(new_qty))

    def _on_sell_selection_change(self):
        """Update available shares and price labels when an owned stock is selected to sell."""
        sym = self._get_symbol_from_combo(self.sell_stock_var.get())
        if not sym:
            return

        price = self.manager.get_stock_price(sym) or 0.0
        holding = self.manager.db.get_holding(sym)
        owned_qty = holding["quantity"] if holding else 0

        self.sell_info_label.configure(
            text=f"Available to Sell: {owned_qty} share(s) | Unit Price: ${price:.2f}"
        )
        self._calculate_sell_estimate()

    def _calculate_sell_estimate(self):
        """Dynamically compute estimated proceeds for the sell form."""
        sym = self._get_symbol_from_combo(self.sell_stock_var.get())
        if not sym:
            self.sell_proceeds_estimate_var.set("$0.00")
            return

        price = self.manager.get_stock_price(sym) or 0.0
        is_valid, qty, _ = self.manager.validate_quantity(self.sell_qty_var.get())
        if is_valid:
            total = qty * price
            self.sell_proceeds_estimate_var.set(f"${total:,.2f}")
        else:
            self.sell_proceeds_estimate_var.set("--")

    def _set_sell_max(self):
        """Quickly fill the sell quantity entry with all available shares of selected stock."""
        sym = self._get_symbol_from_combo(self.sell_stock_var.get())
        if not sym:
            return

        holding = self.manager.db.get_holding(sym)
        if holding:
            self.sell_qty_var.set(str(holding["quantity"]))

    def _on_catalog_row_select(self, event):
        """Double clicking a catalog row selects it in the Buy dropdown and switches to Trade view."""
        selected_item = self.catalog_tree.focus()
        if not selected_item:
            return

        values = self.catalog_tree.item(selected_item, "values")
        if values:
            sym = values[0]
            # Match in buy combo
            for opt in self.buy_combo["values"]:
                if opt.startswith(sym):
                    self.buy_stock_var.set(opt)
                    self._on_buy_selection_change()
                    break

    # =========================================================================
    # TRADE EXECUTION & CONFIRMATIONS
    # =========================================================================
    def _execute_buy_transaction(self):
        """Validate input and execute stock purchase with confirmation dialog."""
        sym = self._get_symbol_from_combo(self.buy_stock_var.get())
        if not sym:
            messagebox.showwarning("Selection Required", "Please select a stock to purchase.")
            return

        qty_input = self.buy_qty_var.get()
        is_valid, quantity, err_msg = self.manager.validate_quantity(qty_input)
        if not is_valid:
            messagebox.showerror("Invalid Quantity", err_msg)
            return

        price = self.manager.get_stock_price(sym) or 0.0
        total_cost = quantity * price
        company_name = self.manager.get_stock_name(sym)

        # Confirmation Dialog
        confirmed = messagebox.askyesno(
            "Confirm Stock Purchase",
            f"Are you sure you want to buy {quantity} share(s) of {sym} ({company_name})?\n\n"
            f"• Price per share: ${price:.2f}\n"
            f"• Total Investment: ${total_cost:,.2f}"
        )
        if not confirmed:
            return

        # Execute purchase
        success, message = self.manager.buy_stock(sym, quantity)
        if success:
            messagebox.showinfo("Purchase Successful", message)
            self.buy_qty_var.set("1")
            self.refresh_all_views()
        else:
            messagebox.showerror("Purchase Failed", message)

    def _execute_sell_transaction(self):
        """Validate input and execute stock sale with confirmation dialog."""
        sym = self._get_symbol_from_combo(self.sell_stock_var.get())
        if not sym:
            messagebox.showwarning("Selection Required", "Please select a stock to sell.")
            return

        qty_input = self.sell_qty_var.get()
        is_valid, quantity, err_msg = self.manager.validate_quantity(qty_input)
        if not is_valid:
            messagebox.showerror("Invalid Quantity", err_msg)
            return

        holding = self.manager.db.get_holding(sym)
        if not holding:
            messagebox.showerror("Stock Not Owned", f"You do not currently hold any shares of {sym}.")
            return

        if quantity > holding["quantity"]:
            messagebox.showerror(
                "Insufficient Shares",
                f"Cannot sell {quantity} shares of {sym}.\n"
                f"You only own {holding['quantity']} share(s)."
            )
            return

        price = self.manager.get_stock_price(sym) or 0.0
        total_proceeds = quantity * price
        company_name = self.manager.get_stock_name(sym)

        # Confirmation Dialog
        confirmed = messagebox.askyesno(
            "Confirm Stock Sale",
            f"Are you sure you want to sell {quantity} share(s) of {sym} ({company_name})?\n\n"
            f"• Price per share: ${price:.2f}\n"
            f"• Total Proceeds: ${total_proceeds:,.2f}\n"
            f"• Remaining shares: {holding['quantity'] - quantity}"
        )
        if not confirmed:
            return

        # Execute sale
        success, message = self.manager.sell_stock(sym, quantity)
        if success:
            messagebox.showinfo("Sale Successful", message)
            self.sell_qty_var.set("1")
            self.refresh_all_views()
        else:
            messagebox.showerror("Sale Failed", message)

    # =========================================================================
    # EXPORT & RESET HANDLERS
    # =========================================================================
    def _handle_export_portfolio(self):
        """Prompt user with file dialog to export current portfolio as CSV."""
        summary = self.manager.get_portfolio_summary()
        if summary["total_stocks"] == 0:
            messagebox.showinfo("Export Portfolio", "Portfolio is currently empty. Nothing to export.")
            return

        default_filename = f"portfolio_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")],
            initialfile=default_filename,
            title="Export Portfolio Holdings to CSV"
        )
        if not file_path:
            return

        success, msg = self.manager.export_portfolio_csv(file_path)
        if success:
            messagebox.showinfo("Export Complete", msg)
            self.set_status(f"Exported portfolio to {os.path.basename(file_path)}")
        else:
            messagebox.showerror("Export Failed", msg)

    def _handle_export_transactions(self):
        """Prompt user with file dialog to export transaction audit ledger as CSV."""
        transactions = self.manager.get_transactions()
        if not transactions:
            messagebox.showinfo("Export Transactions", "Transaction history is currently empty.")
            return

        default_filename = f"transactions_audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")],
            initialfile=default_filename,
            title="Export Transaction History to CSV"
        )
        if not file_path:
            return

        success, msg = self.manager.export_transactions_csv(file_path)
        if success:
            messagebox.showinfo("Export Complete", msg)
            self.set_status(f"Exported transactions to {os.path.basename(file_path)}")
        else:
            messagebox.showerror("Export Failed", msg)

    def _handle_portfolio_reset(self):
        """Confirm and execute complete reset of portfolio and transactions."""
        confirmed = messagebox.askyesno(
            "⚠️ Reset Entire Portfolio",
            "Are you sure you want to completely reset the portfolio?\n\n"
            "• This will PERMANENTLY delete all active holdings.\n"
            "• This will PERMANENTLY delete all transaction history.\n"
            "• The database file itself will NOT be deleted.\n\n"
            "Do you wish to proceed?",
            icon=messagebox.WARNING
        )
        if not confirmed:
            return

        # Double confirmation for safety
        double_confirm = messagebox.askyesno(
            "Final Confirmation",
            "This action CANNOT be undone. Please confirm once more to reset all data.",
            icon=messagebox.WARNING
        )
        if not double_confirm:
            return

        success, msg = self.manager.reset_portfolio()
        if success:
            messagebox.showinfo("Portfolio Reset", msg)
            self.refresh_all_views()
            self.set_status("Portfolio reset successfully.")
        else:
            messagebox.showerror("Reset Failed", msg)
