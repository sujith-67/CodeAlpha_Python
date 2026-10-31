"""ui.py - Graphical User Interface for Smart Email Extractor
============================================================
Modern dark-themed desktop dashboard built with Tkinter and ttkbootstrap.
Features:
- Header with quick-action buttons (Import, Export CSV, Export TXT)
- Five live summary statistics cards
- File provenance and status notification banner
- Dynamic search-as-you-type and validation status filters
- Scrollable results table with color-coded syntax status and column sorting
- Selected & visible clipboard copy utilities
- Detailed syntax inspection pane for selected emails
- Clear Results with confirmation safety checks
- Strict local offline execution with no external data transmission
"""

from __future__ import annotations

import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import List, Optional

import ttkbootstrap as tb
from ttkbootstrap.constants import *

from src.email_engine import EmailExtractionEngine, EmailRecord, ExtractionStats
from src.file_operations import export_to_csv, export_to_txt, read_text_files_batch


# Color Palette Constants (Refined Dark Financial/Utility Theme)
COLOR_BG_DARK = "#131b2a"       # Deep dark navy root
COLOR_PANEL_BG = "#1a2436"      # Slightly lighter navy panel
COLOR_CARD_BG = "#1e293b"       # Card surface background
COLOR_CARD_BORDER = "#334155"   # Card border outline
COLOR_ACCENT_BLUE = "#38bdf8"   # Primary sky blue accent
COLOR_ACCENT_CYAN = "#06b6d4"   # Secondary cyan accent
COLOR_ACCENT_EMERALD = "#10b981"# Success green for Valid
COLOR_ACCENT_AMBER = "#f59e0b"  # Amber for Duplicates Removed
COLOR_ACCENT_ROSE = "#f43f5e"   # Rose red for Needs Review / Clear
COLOR_ACCENT_PURPLE = "#a855f7" # Purple for Unique Emails
COLOR_TEXT_PRIMARY = "#f8fafc"  # Crisp bright white
COLOR_TEXT_MUTED = "#94a3b8"    # Subtle muted grey
COLOR_TEXT_DIM = "#64748b"      # Dim explanatory text


class StatMetricCard(tb.Frame):
    """Modern summary metric card displaying an icon, title, large counter, and micro-label."""

    def __init__(
        self,
        parent: tk.Widget,
        icon: str,
        title: str,
        initial_value: str = "0",
        micro_label: str = "",
        accent_color: str = COLOR_ACCENT_BLUE,
    ) -> None:
        super().__init__(
            parent,
            bootstyle="dark",
            padding=(14, 10),
            relief="solid",
            borderwidth=1,
        )
        self.accent_color = accent_color

        # Top row: Icon and Title
        top_frame = tb.Frame(self, bootstyle="dark")
        top_frame.pack(fill=X, anchor="w")

        tb.Label(
            top_frame,
            text=icon,
            font=("Segoe UI Emoji", 13),
            bootstyle="dark",
            foreground=accent_color,
        ).pack(side=LEFT, padx=(0, 6))

        tb.Label(
            top_frame,
            text=title.upper(),
            font=("Segoe UI", 8, "bold"),
            bootstyle="dark",
            foreground=COLOR_TEXT_MUTED,
        ).pack(side=LEFT, anchor="center")

        # Large metric value
        self.value_label = tb.Label(
            self,
            text=initial_value,
            font=("Segoe UI", 20, "bold"),
            bootstyle="dark",
            foreground=COLOR_TEXT_PRIMARY,
        )
        self.value_label.pack(anchor="w", pady=(4, 1))

        # Bottom descriptive micro-label
        self.sub_label = tb.Label(
            self,
            text=micro_label,
            font=("Segoe UI", 7),
            bootstyle="dark",
            foreground=COLOR_TEXT_DIM,
        )
        self.sub_label.pack(anchor="w")

    def set_value(self, value: int | str) -> None:
        """Update the displayed metric value."""
        self.value_label.configure(text=str(value))


class SmartEmailExtractorUI:
    """Main dashboard user interface controller for Smart Email Extractor."""

    def __init__(self, root: tb.Window) -> None:
        self.root = root
        self.root.title("SMART EMAIL EXTRACTOR — Professional Desktop Utility")
        self.root.minsize(1050, 720)

        # Core logic engine
        self.engine = EmailExtractionEngine()

        # State tracking
        self.current_records: List[EmailRecord] = []
        self.visible_records: List[EmailRecord] = []
        self.imported_files_summary: str = "No files imported yet"
        self.active_filter: str = "ALL"  # "ALL", "VALID", "REVIEW"
        self.sort_column: str = "Occurrences"
        self.sort_descending: bool = True

        # Configure styles
        self._configure_custom_styles()

        # Build layout
        self._build_header()
        self._build_stats_section()
        self._build_file_banner()
        self._build_toolbar()
        self._build_table_section()
        self._build_detail_inspector()
        self._build_status_bar()

        # Initial render (empty state)
        self.refresh_ui()

    def _configure_custom_styles(self) -> None:
        """Configure ttk styles for Treeview and custom buttons."""
        style = tb.Style()

        # Treeview styling
        style.configure(
            "Treeview",
            font=("Segoe UI", 9),
            rowheight=28,
            background="#1e293b",
            fieldbackground="#1e293b",
            foreground="#f8fafc",
        )
        style.configure(
            "Treeview.Heading",
            font=("Segoe UI", 9, "bold"),
            background="#1a2436",
            foreground="#38bdf8",
            relief="flat",
        )
        style.map(
            "Treeview",
            background=[("selected", "#0284c7")],
            foreground=[("selected", "#ffffff")],
        )

    # -------------------------------------------------------------------------
    # Layout Builders
    # -------------------------------------------------------------------------

    def _build_header(self) -> None:
        """Build the top header with application branding and quick-export buttons."""
        header_frame = tb.Frame(self.root, padding=(20, 16, 20, 10), bootstyle="dark")
        header_frame.pack(fill=X)

        # Left branding block
        title_block = tb.Frame(header_frame, bootstyle="dark")
        title_block.pack(side=LEFT, fill=X, expand=True)

        title_row = tb.Frame(title_block, bootstyle="dark")
        title_row.pack(anchor="w")

        tb.Label(
            title_row,
            text="⚡ SMART EMAIL EXTRACTOR",
            font=("Segoe UI", 16, "bold"),
            bootstyle="info",
        ).pack(side=LEFT, padx=(0, 10))

        tb.Label(
            title_row,
            text="v2.0 Desktop",
            font=("Segoe UI", 9, "bold"),
            bootstyle="secondary",
            foreground="#64748b",
        ).pack(side=LEFT, pady=(3, 0))

        tb.Label(
            title_block,
            text="Extract, validate, organise and export email addresses from your text files.",
            font=("Segoe UI", 9),
            bootstyle="dark",
            foreground=COLOR_TEXT_MUTED,
        ).pack(anchor="w", pady=(2, 0))

        # Right action buttons
        btn_box = tb.Frame(header_frame, bootstyle="dark")
        btn_box.pack(side=RIGHT, anchor="center")

        tb.Button(
            btn_box,
            text="📂  Import Files",
            bootstyle="info",
            command=self.on_import_files,
            cursor="hand2",
            width=14,
        ).pack(side=LEFT, padx=4)

        tb.Button(
            btn_box,
            text="📊  Export CSV",
            bootstyle="success-outline",
            command=self.on_export_csv,
            cursor="hand2",
            width=13,
        ).pack(side=LEFT, padx=4)

        tb.Button(
            btn_box,
            text="📝  Export TXT",
            bootstyle="secondary-outline",
            command=self.on_export_txt,
            cursor="hand2",
            width=13,
        ).pack(side=LEFT, padx=4)

    def _build_stats_section(self) -> None:
        """Build five live metric cards summarizing extraction statistics."""
        stats_container = tb.Frame(self.root, padding=(20, 4, 20, 10), bootstyle="dark")
        stats_container.pack(fill=X)

        # Configure 5 equal-weight columns
        for col_idx in range(5):
            stats_container.columnconfigure(col_idx, weight=1, uniform="stat_cards")

        self.card_total = StatMetricCard(
            stats_container,
            icon="🔢",
            title="Total Matches",
            initial_value="0",
            micro_label="All occurrences found",
            accent_color=COLOR_ACCENT_BLUE,
        )
        self.card_total.grid(row=0, column=0, sticky="nsew", padx=4)

        self.card_unique = StatMetricCard(
            stats_container,
            icon="📧",
            title="Unique Emails",
            initial_value="0",
            micro_label="Distinct addresses",
            accent_color=COLOR_ACCENT_PURPLE,
        )
        self.card_unique.grid(row=0, column=1, sticky="nsew", padx=4)

        self.card_duplicates = StatMetricCard(
            stats_container,
            icon="✂️",
            title="Duplicates Removed",
            initial_value="0",
            micro_label="Case-insensitive merges",
            accent_color=COLOR_ACCENT_AMBER,
        )
        self.card_duplicates.grid(row=0, column=2, sticky="nsew", padx=4)

        self.card_valid = StatMetricCard(
            stats_container,
            icon="✅",
            title="Valid Emails",
            initial_value="0",
            micro_label="Passed RFC syntax rules",
            accent_color=COLOR_ACCENT_EMERALD,
        )
        self.card_valid.grid(row=0, column=3, sticky="nsew", padx=4)

        self.card_review = StatMetricCard(
            stats_container,
            icon="⚠️",
            title="Needs Review",
            initial_value="0",
            micro_label="Flagged syntax defects",
            accent_color=COLOR_ACCENT_ROSE,
        )
        self.card_review.grid(row=0, column=4, sticky="nsew", padx=4)

    def _build_file_banner(self) -> None:
        """Display provenance information about imported and failed files."""
        banner_frame = tb.Frame(self.root, padding=(20, 0, 20, 8), bootstyle="dark")
        banner_frame.pack(fill=X)

        inner = tb.Frame(
            banner_frame,
            bootstyle="secondary",
            padding=(12, 6),
            relief="solid",
            borderwidth=1,
        )
        inner.pack(fill=X)

        self.file_info_label = tb.Label(
            inner,
            text="📁  Ready. Click 'Import Files' to select one or more .txt documents.",
            font=("Segoe UI", 8),
            bootstyle="secondary",
            foreground="#cbd5e1",
        )
        self.file_info_label.pack(side=LEFT, fill=X, expand=True)

        # Syntax check badge notice
        tb.Label(
            inner,
            text="🛡️  Local Syntax Validation Only (Mailbox existence is not queried)",
            font=("Segoe UI", 8, "italic"),
            bootstyle="secondary",
            foreground="#94a3b8",
        ).pack(side=RIGHT)

    def _build_toolbar(self) -> None:
        """Build search, filter, and clipboard action controls."""
        toolbar = tb.Frame(self.root, padding=(20, 4, 20, 8), bootstyle="dark")
        toolbar.pack(fill=X)

        # Left: Search box
        search_box = tb.Frame(toolbar, bootstyle="dark")
        search_box.pack(side=LEFT, fill=X, expand=True)

        tb.Label(
            search_box,
            text="🔍  Search:",
            font=("Segoe UI", 9, "bold"),
            bootstyle="dark",
            foreground=COLOR_TEXT_MUTED,
        ).pack(side=LEFT, padx=(0, 6))

        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self.on_search_or_filter_changed())

        self.search_entry = tb.Entry(
            search_box,
            textvariable=self.search_var,
            font=("Segoe UI", 9),
            width=32,
            bootstyle="info",
        )
        self.search_entry.pack(side=LEFT, padx=(0, 6))

        tb.Button(
            search_box,
            text="✕ Clear",
            bootstyle="dark-outline",
            command=self.on_clear_search,
            cursor="hand2",
            width=7,
        ).pack(side=LEFT)

        # Center: Filter buttons (All / Valid / Needs Review)
        filter_box = tb.Frame(toolbar, bootstyle="dark")
        filter_box.pack(side=LEFT, padx=(20, 20))

        tb.Label(
            filter_box,
            text="Filter:",
            font=("Segoe UI", 9, "bold"),
            bootstyle="dark",
            foreground=COLOR_TEXT_MUTED,
        ).pack(side=LEFT, padx=(0, 6))

        self.btn_filter_all = tb.Button(
            filter_box,
            text="All (0)",
            bootstyle="primary",
            command=lambda: self.set_active_filter("ALL"),
            cursor="hand2",
            width=10,
        )
        self.btn_filter_all.pack(side=LEFT, padx=2)

        self.btn_filter_valid = tb.Button(
            filter_box,
            text="Valid (0)",
            bootstyle="dark-outline",
            command=lambda: self.set_active_filter("VALID"),
            cursor="hand2",
            width=10,
        )
        self.btn_filter_valid.pack(side=LEFT, padx=2)

        self.btn_filter_review = tb.Button(
            filter_box,
            text="Needs Review (0)",
            bootstyle="dark-outline",
            command=lambda: self.set_active_filter("REVIEW"),
            cursor="hand2",
            width=14,
        )
        self.btn_filter_review.pack(side=LEFT, padx=2)

        # Right: Clipboard & Reset Buttons
        right_box = tb.Frame(toolbar, bootstyle="dark")
        right_box.pack(side=RIGHT)

        tb.Button(
            right_box,
            text="📋 Copy Selected",
            bootstyle="info-outline",
            command=self.on_copy_selected,
            cursor="hand2",
            width=14,
        ).pack(side=LEFT, padx=3)

        tb.Button(
            right_box,
            text="📋 Copy Visible",
            bootstyle="info-outline",
            command=self.on_copy_visible,
            cursor="hand2",
            width=14,
        ).pack(side=LEFT, padx=3)

        tb.Button(
            right_box,
            text="🗑️ Clear All",
            bootstyle="danger-outline",
            command=self.on_clear_results,
            cursor="hand2",
            width=11,
        ).pack(side=LEFT, padx=(6, 0))

    def _build_table_section(self) -> None:
        """Build the scrollable Treeview table displaying extracted email records."""
        table_container = tb.Frame(self.root, padding=(20, 0, 20, 6), bootstyle="dark")
        table_container.pack(fill=BOTH, expand=True)

        columns = ("Email Address", "Validation Status", "Occurrences", "Source Files")
        self.tree = ttk.Treeview(
            table_container,
            columns=columns,
            show="headings",
            selectmode="extended",
            style="Treeview",
        )

        # Column configuration
        self.tree.heading(
            "Email Address",
            text="Email Address",
            command=lambda: self.sort_by_column("Email Address"),
        )
        self.tree.heading(
            "Validation Status",
            text="Validation Status",
            command=lambda: self.sort_by_column("Validation Status"),
        )
        self.tree.heading(
            "Occurrences",
            text="Occurrences",
            command=lambda: self.sort_by_column("Occurrences"),
        )
        self.tree.heading(
            "Source Files",
            text="Source Files",
            command=lambda: self.sort_by_column("Source Files"),
        )

        self.tree.column("Email Address", width=340, minwidth=200, anchor="w")
        self.tree.column("Validation Status", width=150, minwidth=130, anchor="center")
        self.tree.column("Occurrences", width=110, minwidth=90, anchor="center")
        self.tree.column("Source Files", width=380, minwidth=200, anchor="w")

        # Vertical Scrollbar
        scrollbar = tb.Scrollbar(
            table_container,
            orient=VERTICAL,
            command=self.tree.yview,
            bootstyle="round",
        )
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar.pack(side=RIGHT, fill=Y)

        # Row tag colors
        self.tree.tag_configure("valid_row", foreground="#4ade80")       # Bright mint green
        self.tree.tag_configure("review_row", foreground="#fbbf24")      # Warm amber warning

        # Selection listener for inspector
        self.tree.bind("<<TreeviewSelect>>", self.on_row_selected)

    def _build_detail_inspector(self) -> None:
        """Build bottom inspection card showing selected email validation details."""
        self.inspector_frame = tb.Frame(self.root, padding=(20, 0, 20, 6), bootstyle="dark")
        self.inspector_frame.pack(fill=X)

        card = tb.Frame(
            self.inspector_frame,
            bootstyle="dark",
            padding=(14, 8),
            relief="solid",
            borderwidth=1,
        )
        card.pack(fill=X)

        self.inspector_title_label = tb.Label(
            card,
            text="🔎  Email Inspector",
            font=("Segoe UI", 9, "bold"),
            bootstyle="dark",
            foreground="#38bdf8",
        )
        self.inspector_title_label.pack(anchor="w")

        self.inspector_detail_label = tb.Label(
            card,
            text="Select an email in the table above to view complete syntax analysis and source files.",
            font=("Segoe UI", 8),
            bootstyle="dark",
            foreground=COLOR_TEXT_MUTED,
            wraplength=950,
        )
        self.inspector_detail_label.pack(anchor="w", pady=(2, 0))

    def _build_status_bar(self) -> None:
        """Build bottom status bar with row counts and active notifications."""
        status_frame = tb.Frame(self.root, padding=(20, 4, 20, 8), bootstyle="dark")
        status_frame.pack(fill=X)

        self.status_left_label = tb.Label(
            status_frame,
            text="Showing 0 of 0 unique emails",
            font=("Segoe UI", 8),
            bootstyle="dark",
            foreground=COLOR_TEXT_MUTED,
        )
        self.status_left_label.pack(side=LEFT)

        self.status_notification_label = tb.Label(
            status_frame,
            text="",
            font=("Segoe UI", 8, "bold"),
            bootstyle="info",
            foreground="#38bdf8",
        )
        self.status_notification_label.pack(side=RIGHT)

    # -------------------------------------------------------------------------
    # Event Handlers & Core Interactions
    # -------------------------------------------------------------------------

    def on_import_files(self) -> None:
        """Open file dialog for selecting multiple text files and run extraction."""
        filetypes = [
            ("Text Files", "*.txt"),
            ("Log Files", "*.log"),
            ("CSV Files", "*.csv"),
            ("All Supported Files", "*.txt;*.log;*.csv"),
            ("All Files", "*.*"),
        ]

        selected_paths = filedialog.askopenfilenames(
            title="Select Text Files for Email Extraction",
            filetypes=filetypes,
        )

        if not selected_paths:
            return  # User cancelled dialog gracefully

        # Read batch of selected files
        load_summary = read_text_files_batch(selected_paths)

        if not load_summary.successful_files:
            error_details = "\n".join(
                f"• {name}: {err}" for name, err in load_summary.failed_files
            )
            messagebox.showerror(
                "File Import Error",
                f"None of the selected files could be loaded:\n\n{error_details}",
            )
            return

        # Execute extraction across loaded sources
        stats = self.engine.process_sources(load_summary.successful_files)
        self.current_records = self.engine.get_records()

        # Update file provenance summary banner
        success_names = [name for name, _ in load_summary.successful_files]
        summary_parts = [
            f"📁 Processed {len(success_names)} file(s): {', '.join(success_names)}"
        ]
        if load_summary.failed_files:
            failed_names = [f"{name} ({err})" for name, err in load_summary.failed_files]
            summary_parts.append(f"❌ Failed ({len(failed_names)}): {', '.join(failed_names)}")

        self.imported_files_summary = "  |  ".join(summary_parts)

        # Refresh entire interface
        self.refresh_ui()

        # Toast notification
        self.notify_status(
            f"✓ Extraction complete: {stats.unique_emails} unique emails from {stats.total_matches} total matches."
        )

        # Success message box
        if stats.unique_emails == 0:
            messagebox.showinfo(
                "Extraction Finished",
                f"Processed {len(success_names)} file(s).\n\nNo email addresses were found in the selected files.",
            )
        else:
            messagebox.showinfo(
                "Extraction Successful",
                f"Successfully processed {len(success_names)} file(s)!\n\n"
                f"• Total Matches: {stats.total_matches}\n"
                f"• Unique Emails: {stats.unique_emails}\n"
                f"• Duplicates Removed: {stats.duplicates_removed}\n"
                f"• Valid Syntax: {stats.valid_emails}\n"
                f"• Needs Review: {stats.needs_review}",
            )

    def on_export_csv(self) -> None:
        """Export currently visible filtered email records to CSV."""
        if not self.visible_records:
            messagebox.showwarning(
                "No Data to Export",
                "There are no visible email records in the table to export.",
            )
            return

        dest_path = filedialog.asksaveasfilename(
            title="Export Visible Email Records to CSV",
            defaultextension=".csv",
            filetypes=[("CSV (Comma Separated Values)", "*.csv"), ("All Files", "*.*")],
            initialfile="extracted_emails.csv",
        )

        if not dest_path:
            return  # Cancelled

        success, count, err = export_to_csv(self.visible_records, dest_path)
        if success:
            self.notify_status(f"✓ Exported {count} records to CSV")
            messagebox.showinfo(
                "Export Complete",
                f"Successfully exported {count} email records to:\n{dest_path}",
            )
        else:
            messagebox.showerror("Export Error", f"Failed to export CSV:\n{err}")

    def on_export_txt(self) -> None:
        """Export currently visible unique email addresses to plain TXT."""
        if not self.visible_records:
            messagebox.showwarning(
                "No Data to Export",
                "There are no visible email records in the table to export.",
            )
            return

        dest_path = filedialog.asksaveasfilename(
            title="Export Visible Email Addresses to TXT",
            defaultextension=".txt",
            filetypes=[("Text Document", "*.txt"), ("All Files", "*.*")],
            initialfile="unique_emails.txt",
        )

        if not dest_path:
            return  # Cancelled

        success, count, err = export_to_txt(self.visible_records, dest_path)
        if success:
            self.notify_status(f"✓ Exported {count} unique emails to TXT")
            messagebox.showinfo(
                "Export Complete",
                f"Successfully exported {count} unique email addresses to:\n{dest_path}",
            )
        else:
            messagebox.showerror("Export Error", f"Failed to export TXT:\n{err}")

    def on_copy_selected(self) -> None:
        """Copy selected rows in the table to the system clipboard."""
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showinfo(
                "Copy to Clipboard",
                "Please select one or more rows from the table first.",
            )
            return

        copied_emails: List[str] = []
        for item_id in selected_items:
            values = self.tree.item(item_id, "values")
            if values:
                copied_emails.append(values[0])

        clipboard_text = "\n".join(copied_emails)
        self.root.clipboard_clear()
        self.root.clipboard_append(clipboard_text)

        count = len(copied_emails)
        self.notify_status(f"✓ Copied {count} selected email(s) to clipboard")

    def on_copy_visible(self) -> None:
        """Copy all currently visible / filtered email addresses to system clipboard."""
        if not self.visible_records:
            messagebox.showinfo(
                "Copy to Clipboard",
                "There are no visible email addresses in the table to copy.",
            )
            return

        copied_emails = [record.address for record in self.visible_records]
        clipboard_text = "\n".join(copied_emails)
        self.root.clipboard_clear()
        self.root.clipboard_append(clipboard_text)

        count = len(copied_emails)
        self.notify_status(f"✓ Copied {count} visible email(s) to clipboard")

    def on_clear_results(self) -> None:
        """Clear all loaded records, statistics, and filters after confirmation."""
        if not self.current_records:
            return

        confirm = messagebox.askyesno(
            "Confirm Clear Results",
            "Are you sure you want to clear all extracted email records and statistics?\n\nThis will reset the current session.",
            icon="warning",
        )
        if not confirm:
            return

        self.engine.reset()
        self.current_records = []
        self.visible_records = []
        self.imported_files_summary = "No files imported yet"
        self.search_var.set("")
        self.active_filter = "ALL"

        self.refresh_ui()
        self.notify_status("Session cleared. Ready for new files.")

    def on_clear_search(self) -> None:
        """Reset the search box."""
        self.search_var.set("")

    def set_active_filter(self, filter_mode: str) -> None:
        """Set active validation status filter ('ALL', 'VALID', 'REVIEW')."""
        self.active_filter = filter_mode
        self._update_filter_button_styles()
        self.filter_and_populate_table()

    def _update_filter_button_styles(self) -> None:
        """Update active/inactive visual styles on filter buttons."""
        self.btn_filter_all.configure(
            bootstyle="primary" if self.active_filter == "ALL" else "dark-outline"
        )
        self.btn_filter_valid.configure(
            bootstyle="success" if self.active_filter == "VALID" else "dark-outline"
        )
        self.btn_filter_review.configure(
            bootstyle="warning" if self.active_filter == "REVIEW" else "dark-outline"
        )

    def on_search_or_filter_changed(self) -> None:
        """Re-filter the visible records when search query changes."""
        self.filter_and_populate_table()

    def on_row_selected(self, _event: Optional[tk.Event] = None) -> None:
        """Update the bottom inspector card when the user clicks a row."""
        selected_items = self.tree.selection()
        if not selected_items:
            self.inspector_title_label.configure(
                text="🔎  Email Inspector",
                foreground="#38bdf8",
            )
            self.inspector_detail_label.configure(
                text="Select an email in the table above to view complete syntax analysis and source files."
            )
            return

        first_item = selected_items[0]
        values = self.tree.item(first_item, "values")
        if not values:
            return

        email_addr = values[0]
        status_text = values[1]
        occurrences = values[2]
        source_files = values[3]

        # Find matching record for complete validation notes
        matched_rec = next((r for r in self.current_records if r.address == email_addr), None)
        reason = matched_rec.validation.reason if matched_rec else "N/A"

        color = COLOR_ACCENT_EMERALD if "Valid" in status_text else COLOR_ACCENT_AMBER

        self.inspector_title_label.configure(
            text=f"🔎  {email_addr}   •   [{status_text}]   •   {occurrences} occurrence(s)",
            foreground=color,
        )
        self.inspector_detail_label.configure(
            text=f"Validation Note: {reason}   |   Source File(s): {source_files}"
        )

    def sort_by_column(self, col: str) -> None:
        """Sort the table by clicking column headers."""
        if self.sort_column == col:
            self.sort_descending = not self.sort_descending
        else:
            self.sort_column = col
            self.sort_descending = False

        self.filter_and_populate_table()

    # -------------------------------------------------------------------------
    # Filtering, Sorting & Table Population
    # -------------------------------------------------------------------------

    def filter_and_populate_table(self) -> None:
        """Filter current records by active search query and validation category."""
        query = self.search_var.get().strip().lower()

        # 1. Category Filter
        if self.active_filter == "VALID":
            filtered = [r for r in self.current_records if r.validation.is_valid]
        elif self.active_filter == "REVIEW":
            filtered = [r for r in self.current_records if not r.validation.is_valid]
        else:
            filtered = list(self.current_records)

        # 2. Search Query Filter
        if query:
            filtered = [
                r for r in filtered
                if (
                    query in r.normalized
                    or any(query in src.lower() for src in r.source_files)
                    or query in r.validation.reason.lower()
                )
            ]

        # 3. Sorting
        def sort_key(rec: EmailRecord):
            if self.sort_column == "Email Address":
                return rec.normalized
            elif self.sort_column == "Validation Status":
                return rec.validation.status
            elif self.sort_column == "Occurrences":
                return rec.occurrences
            elif self.sort_column == "Source Files":
                return ", ".join(rec.source_files)
            return rec.occurrences

        filtered.sort(key=sort_key, reverse=self.sort_descending)
        self.visible_records = filtered

        # 4. Populate Treeview
        self.tree.delete(*self.tree.get_children())

        if not self.visible_records:
            # Empty state
            if not self.current_records:
                empty_msg = "No files imported yet. Click 'Import Files' above to begin."
            else:
                empty_msg = "No email records match your current filter and search query."
            self.tree.insert(
                "",
                END,
                values=(f"({empty_msg})", "-", "-", "-"),
                tags=("review_row",),
            )
        else:
            for rec in self.visible_records:
                status_icon = "✔ Valid" if rec.validation.is_valid else "⚠ Needs Review"
                tag = "valid_row" if rec.validation.is_valid else "review_row"
                source_str = ", ".join(rec.source_files) if rec.source_files else "Unknown"

                self.tree.insert(
                    "",
                    END,
                    values=(rec.address, status_icon, rec.occurrences, source_str),
                    tags=(tag,),
                )

        # Update status count label
        total_unique = len(self.current_records)
        visible_count = len(self.visible_records) if self.current_records else 0
        self.status_left_label.configure(
            text=f"Showing {visible_count} of {total_unique} unique emails"
        )

    def refresh_ui(self) -> None:
        """Update all live metric cards, file banners, and filter button labels."""
        stats = self.engine.get_statistics()

        # Update metric cards
        self.card_total.set_value(stats.total_matches)
        self.card_unique.set_value(stats.unique_emails)
        self.card_duplicates.set_value(stats.duplicates_removed)
        self.card_valid.set_value(stats.valid_emails)
        self.card_review.set_value(stats.needs_review)

        # Update filter pill counts
        self.btn_filter_all.configure(text=f"All ({stats.unique_emails})")
        self.btn_filter_valid.configure(text=f"Valid ({stats.valid_emails})")
        self.btn_filter_review.configure(text=f"Needs Review ({stats.needs_review})")

        # Update file provenance text
        self.file_info_label.configure(text=self.imported_files_summary)

        # Refresh table
        self.filter_and_populate_table()

        # Clear inspector
        self.on_row_selected(None)

    def notify_status(self, message: str) -> None:
        """Display a temporary notification message in the status bar."""
        self.status_notification_label.configure(text=message)
        # Clear after 6 seconds
        self.root.after(6000, lambda: self.status_notification_label.configure(text=""))
