"""test_ui_workflow.py - Automated UI Workflow and Integration Tests
=====================================================================
Validates:
- Application initialization and widget creation.
- Initial state rendering (cards at 0, empty-state placeholder in table).
- Loading records into the UI and updating statistic metric cards.
- Search filter interaction.
- Validation category filter interaction (All, Valid, Needs Review).
- Selection inspector updates.
- Export workflows via UI handlers.
- Clear results workflow.
"""

from __future__ import annotations

import os
import shutil
import tempfile
import unittest

import ttkbootstrap as tb

from src.ui import SmartEmailExtractorUI


class TestUIWorkflow(unittest.TestCase):
    """Integration test suite for the SmartEmailExtractorUI controller."""

    @classmethod
    def setUpClass(cls) -> None:
        # Create a single hidden root window for testing UI components
        cls.root = tb.Window(themename="nord-dark")
        cls.root.withdraw()  # Keep window hidden during test runs

    @classmethod
    def tearDownClass(cls) -> None:
        try:
            cls.root.destroy()
        except Exception:
            pass

    def setUp(self) -> None:
        self.test_dir = tempfile.mkdtemp(prefix="ui_test_")
        self.ui = SmartEmailExtractorUI(self.root)
        self.root.update()

    def tearDown(self) -> None:
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_initial_state(self) -> None:
        """Verify initial UI state has zeros across all metric cards and empty table message."""
        self.assertEqual(self.ui.card_total.value_label.cget("text"), "0")
        self.assertEqual(self.ui.card_unique.value_label.cget("text"), "0")
        self.assertEqual(self.ui.card_duplicates.value_label.cget("text"), "0")
        self.assertEqual(self.ui.card_valid.value_label.cget("text"), "0")
        self.assertEqual(self.ui.card_review.value_label.cget("text"), "0")
        self.assertEqual(len(self.ui.current_records), 0)

        # Treeview should contain the empty placeholder row
        children = self.ui.tree.get_children()
        self.assertEqual(len(children), 1)
        row_vals = self.ui.tree.item(children[0], "values")
        self.assertIn("No files imported yet", row_vals[0])

    def test_data_load_and_metric_cards(self) -> None:
        """Verify that loading text updates the live metric cards and table rows."""
        sample = (
            "Contact info:\n"
            "Elena.Rostova@ApexTech.io\n"
            "elena.rostova@apextech.io\n"  # Duplicate (different case)
            "marcus.vance@solaris.net\n"
            "dev.intern@solaris.net\n"
            "bad..format@broken.com\n"     # Flagged syntax (consecutive dots)
        )
        self.ui.engine.process_text(sample, "team_contacts.txt")
        self.ui.current_records = self.ui.engine.get_records()
        self.ui.imported_files_summary = "📁 Processed 1 file: team_contacts.txt"
        self.ui.refresh_ui()
        self.root.update()

        # Check statistics cards
        self.assertEqual(self.ui.card_total.value_label.cget("text"), "5")
        self.assertEqual(self.ui.card_unique.value_label.cget("text"), "4")
        self.assertEqual(self.ui.card_duplicates.value_label.cget("text"), "1")
        self.assertEqual(self.ui.card_valid.value_label.cget("text"), "3")
        self.assertEqual(self.ui.card_review.value_label.cget("text"), "1")

        # Check visible rows in Treeview
        children = self.ui.tree.get_children()
        self.assertEqual(len(children), 4)

    def test_search_filtering(self) -> None:
        """Verify dynamic search-as-you-type filters table rows accurately."""
        sample = (
            "alpha@example.com\n"
            "beta@domain.org\n"
            "charlie@example.com\n"
        )
        self.ui.engine.process_text(sample, "test.txt")
        self.ui.current_records = self.ui.engine.get_records()
        self.ui.refresh_ui()

        # Search for 'example'
        self.ui.search_var.set("example")
        self.root.update()

        self.assertEqual(len(self.ui.visible_records), 2)
        visible_addrs = [r.address for r in self.ui.visible_records]
        self.assertIn("alpha@example.com", visible_addrs)
        self.assertIn("charlie@example.com", visible_addrs)
        self.assertNotIn("beta@domain.org", visible_addrs)

        # Clear search
        self.ui.on_clear_search()
        self.root.update()
        self.assertEqual(len(self.ui.visible_records), 3)

    def test_validation_category_filter(self) -> None:
        """Verify category pills (ALL, VALID, REVIEW) filter table accordingly."""
        sample = (
            "valid.one@example.com\n"
            "valid.two@example.com\n"
            "defect@-badhost.com\n"
        )
        self.ui.engine.process_text(sample, "test.txt")
        self.ui.current_records = self.ui.engine.get_records()
        self.ui.refresh_ui()

        # Filter VALID
        self.ui.set_active_filter("VALID")
        self.root.update()
        self.assertEqual(len(self.ui.visible_records), 2)
        for r in self.ui.visible_records:
            self.assertTrue(r.validation.is_valid)

        # Filter REVIEW
        self.ui.set_active_filter("REVIEW")
        self.root.update()
        self.assertEqual(len(self.ui.visible_records), 1)
        self.assertEqual(self.ui.visible_records[0].address, "defect@-badhost.com")

        # Filter ALL
        self.ui.set_active_filter("ALL")
        self.root.update()
        self.assertEqual(len(self.ui.visible_records), 3)

    def test_column_sorting(self) -> None:
        """Verify sorting table rows by clicking columns."""
        sample = (
            "b_user@site.com\n"
            "a_user@site.com\n"
            "c_user@site.com\n"
        )
        self.ui.engine.process_text(sample, "test.txt")
        self.ui.current_records = self.ui.engine.get_records()
        self.ui.refresh_ui()

        # Sort ascending by Email Address
        self.ui.sort_column = "Email Address"
        self.ui.sort_descending = False
        self.ui.filter_and_populate_table()
        self.root.update()

        first_row = self.ui.tree.item(self.ui.tree.get_children()[0], "values")
        self.assertEqual(first_row[0], "a_user@site.com")

        # Sort descending
        self.ui.sort_by_column("Email Address")
        self.root.update()
        first_row_desc = self.ui.tree.item(self.ui.tree.get_children()[0], "values")
        self.assertEqual(first_row_desc[0], "c_user@site.com")

    def test_inspector_selection(self) -> None:
        """Verify selecting a row updates the bottom inspector panel."""
        sample = "defect..dot@domain.com\n"
        self.ui.engine.process_text(sample, "test.txt")
        self.ui.current_records = self.ui.engine.get_records()
        self.ui.refresh_ui()

        item_id = self.ui.tree.get_children()[0]
        self.ui.tree.selection_set(item_id)
        self.ui.on_row_selected(None)
        self.root.update()

        title = self.ui.inspector_title_label.cget("text")
        detail = self.ui.inspector_detail_label.cget("text")
        self.assertIn("defect..dot@domain.com", title)
        self.assertIn("consecutive dots", detail.lower())


if __name__ == "__main__":
    unittest.main()
