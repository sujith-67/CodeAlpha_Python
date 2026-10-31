"""
charts.py - Portfolio Allocation Visualization
===============================================
Renders Matplotlib allocation charts embedded directly into Tkinter/ttkbootstrap
with a sleek dark financial dashboard theme.
"""

import tkinter as tk
from typing import List, Dict, Any
import matplotlib
# Use TkAgg backend
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure


# Cohesive, modern dark theme color palette for charts
CHART_BG_COLOR = "#151c2c"       # Dark navy card background
CHART_TEXT_COLOR = "#e2e8f0"     # Light slate
CHART_MUTED_COLOR = "#94a3b8"    # Muted light grey
CHART_EDGE_COLOR = "#0b0f19"     # Dark edge between slices

SLICE_COLORS = [
    "#38bdf8",  # Sky blue
    "#34d399",  # Mint / Teal
    "#a78bfa",  # Soft purple
    "#fbbf24",  # Warm amber
    "#f87171",  # Coral / Rose
    "#22d3ee",  # Cyan
    "#fb923c",  # Orange
    "#818cf8",  # Indigo
]


class PortfolioChart:
    """Manages the embedded Matplotlib Donut Chart for portfolio allocation."""

    def __init__(self, parent_widget: tk.Widget):
        self.parent = parent_widget

        # Configure figure with dark styling
        self.fig = Figure(figsize=(4.6, 3.6), dpi=100)
        self.fig.patch.set_facecolor(CHART_BG_COLOR)

        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor(CHART_BG_COLOR)

        # Embed figure into Tkinter widget
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.parent)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.configure(bg=CHART_BG_COLOR, highlightthickness=0)
        self.canvas_widget.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        # Initial render with empty state
        self.update_chart([])

    def update_chart(self, holdings: List[Dict[str, Any]]) -> None:
        """
        Redraw the donut chart given the list of current holdings.
        If empty, displays a clean placeholder message.
        """
        self.ax.clear()
        self.ax.set_facecolor(CHART_BG_COLOR)

        # Filter out holdings with 0 or negative value
        valid_holdings = [h for h in holdings if h.get("total_value", 0) > 0]

        if not valid_holdings:
            # Render empty state placeholder
            self.ax.text(
                0.5, 0.5,
                "No Active Holdings\n\nAdd stocks to view\nportfolio allocation",
                horizontalalignment="center",
                verticalalignment="center",
                transform=self.ax.transAxes,
                color=CHART_MUTED_COLOR,
                fontsize=11,
                fontweight="normal",
                linespacing=1.4
            )
            self.ax.axis("off")
            self.fig.tight_layout(pad=1.2)
            self.canvas.draw_idle()
            return

        # Prepare chart data
        labels = [h["symbol"] for h in valid_holdings]
        values = [h["total_value"] for h in valid_holdings]
        total_val = sum(values)

        # Pick colors cyclically
        colors = [SLICE_COLORS[i % len(SLICE_COLORS)] for i in range(len(valid_holdings))]

        # Custom autopct formatting showing percentage
        def autopct_format(pct: float) -> str:
            return f"{pct:.1f}%" if pct >= 5 else ""

        # Draw donut chart (wedge with width=0.45)
        wedges, texts, autotexts = self.ax.pie(
            values,
            labels=labels,
            colors=colors,
            autopct=autopct_format,
            pctdistance=0.76,
            startangle=140,
            wedgeprops=dict(
                width=0.44,
                edgecolor=CHART_EDGE_COLOR,
                linewidth=2.0
            ),
            textprops=dict(
                color=CHART_TEXT_COLOR,
                fontsize=9.5,
                fontweight="bold"
            )
        )

        # Style percentage text labels inside slices
        for autotext in autotexts:
            autotext.set_color("#0f172a")
            autotext.set_fontsize(8.5)
            autotext.set_weight("bold")

        # Center summary text inside donut hole
        self.ax.text(
            0, 0,
            f"Holdings\n{len(valid_holdings)}",
            horizontalalignment="center",
            verticalalignment="center",
            color=CHART_MUTED_COLOR,
            fontsize=9.5,
            fontweight="bold"
        )

        self.ax.axis("equal")
        self.fig.tight_layout(pad=1.0)
        self.canvas.draw_idle()

    def get_widget(self) -> tk.Widget:
        """Return the Tkinter widget wrapping the chart canvas."""
        return self.canvas_widget
