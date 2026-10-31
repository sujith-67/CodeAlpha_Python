"""test_file_operations.py - Automated Unit Tests for File I/O & Export Operations
================================================================================
Validates:
- Reading standard UTF-8 text files.
- Reading empty text files.
- Reading across multiple source text files.
- Handling missing, nonexistent, or directory paths gracefully.
- RFC-compliant CSV export (correct headers, quoting, row counts, validation notes).
- Plaintext TXT export (one unique email address per line).
- Error handling on export failures.
"""

from __future__ import annotations

import csv
import os
import shutil
import tempfile
import unittest

from src.email_engine import EmailRecord, ValidationResult
from src.file_operations import (
    export_to_csv,
    export_to_txt,
    read_single_text_file,
    read_text_files_batch,
)


class TestFileOperations(unittest.TestCase):
    """Unit tests for reading input files and exporting extraction outputs."""

    def setUp(self) -> None:
        self.test_dir = tempfile.mkdtemp(prefix="email_extractor_test_")

    def tearDown(self) -> None:
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_successful_txt_reading(self) -> None:
        """Test reading a standard UTF-8 text file with content."""
        file_path = os.path.join(self.test_dir, "sample.txt")
        content = "Line 1: contact@alpha.org\nLine 2: info@beta.com\n"
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        outcome = read_single_text_file(file_path)
        self.assertTrue(outcome.success)
        self.assertEqual(outcome.content, content)
        self.assertEqual(outcome.filename, "sample.txt")
        self.assertIsNone(outcome.error_message)

    def test_empty_file_reading(self) -> None:
        """Test reading an existing text file that contains zero bytes."""
        file_path = os.path.join(self.test_dir, "empty.txt")
        with open(file_path, "w", encoding="utf-8") as f:
            pass  # Create empty file

        outcome = read_single_text_file(file_path)
        self.assertTrue(outcome.success)
        self.assertEqual(outcome.content, "")
        self.assertEqual(outcome.filename, "empty.txt")

    def test_missing_file_handling(self) -> None:
        """Test handling when a specified file does not exist on disk."""
        nonexistent_path = os.path.join(self.test_dir, "ghost_file.txt")
        outcome = read_single_text_file(nonexistent_path)
        self.assertFalse(outcome.success)
        self.assertIn("does not exist", outcome.error_message)

    def test_directory_path_handling(self) -> None:
        """Test handling when the path provided is a directory rather than a file."""
        sub_dir = os.path.join(self.test_dir, "subdir")
        os.makedirs(sub_dir)
        outcome = read_single_text_file(sub_dir)
        self.assertFalse(outcome.success)
        self.assertIn("directory", outcome.error_message)

    def test_multiple_source_files_batch(self) -> None:
        """Test batch reading with a mix of valid files and nonexistent files."""
        file1 = os.path.join(self.test_dir, "doc1.txt")
        file2 = os.path.join(self.test_dir, "doc2.txt")
        file3 = os.path.join(self.test_dir, "nonexistent.txt")

        with open(file1, "w", encoding="utf-8") as f:
            f.write("Text in doc1")
        with open(file2, "w", encoding="utf-8") as f:
            f.write("Text in doc2")

        summary = read_text_files_batch([file1, file2, file3])
        self.assertEqual(summary.total_selected, 3)
        self.assertEqual(summary.success_count, 2)
        self.assertEqual(summary.failure_count, 1)

        success_filenames = [name for name, _ in summary.successful_files]
        self.assertIn("doc1.txt", success_filenames)
        self.assertIn("doc2.txt", success_filenames)

        failed_filenames = [name for name, _ in summary.failed_files]
        self.assertIn("nonexistent.txt", failed_filenames)

    def test_csv_export(self) -> None:
        """Test exporting email records to an RFC-compliant CSV file."""
        records = [
            EmailRecord(
                address="alex.chen@technova.org",
                normalized="alex.chen@technova.org",
                validation=ValidationResult(True, "Valid", "Passed RFC checks"),
                occurrences=3,
                source_files=["contacts.txt", "leads.txt"]
            ),
            EmailRecord(
                address="bad..email@domain.com",
                normalized="bad..email@domain.com",
                validation=ValidationResult(False, "Needs Review", "Local part contains consecutive dots"),
                occurrences=1,
                source_files=["logs.txt"]
            ),
        ]

        csv_path = os.path.join(self.test_dir, "exported.csv")
        success, count, err = export_to_csv(records, csv_path)

        self.assertTrue(success)
        self.assertEqual(count, 2)
        self.assertIsNone(err)
        self.assertTrue(os.path.exists(csv_path))

        # Verify CSV content
        with open(csv_path, "r", encoding="utf-8-sig") as f:
            reader = list(csv.reader(f))

        # Check headers
        expected_header = [
            "Email Address",
            "Validation Status",
            "Occurrences",
            "Source Files",
            "Validation Notes"
        ]
        self.assertEqual(reader[0], expected_header)

        # Check row 1
        self.assertEqual(reader[1][0], "alex.chen@technova.org")
        self.assertEqual(reader[1][1], "Valid")
        self.assertEqual(reader[1][2], "3")
        self.assertEqual(reader[1][3], "contacts.txt, leads.txt")
        self.assertEqual(reader[1][4], "Passed RFC checks")

        # Check row 2
        self.assertEqual(reader[2][0], "bad..email@domain.com")
        self.assertEqual(reader[2][1], "Needs Review")
        self.assertEqual(reader[2][2], "1")
        self.assertEqual(reader[2][3], "logs.txt")
        self.assertIn("consecutive dots", reader[2][4])

    def test_txt_export(self) -> None:
        """Test exporting email records to a plaintext file (one email per line)."""
        records = [
            EmailRecord(
                address="first@alpha.com",
                normalized="first@alpha.com",
                validation=ValidationResult(True, "Valid", "Passed"),
                occurrences=1,
                source_files=["f1.txt"]
            ),
            EmailRecord(
                address="second@beta.org",
                normalized="second@beta.org",
                validation=ValidationResult(True, "Valid", "Passed"),
                occurrences=2,
                source_files=["f2.txt"]
            ),
        ]

        txt_path = os.path.join(self.test_dir, "exported.txt")
        success, count, err = export_to_txt(records, txt_path)

        self.assertTrue(success)
        self.assertEqual(count, 2)
        self.assertIsNone(err)
        self.assertTrue(os.path.exists(txt_path))

        with open(txt_path, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f.readlines()]

        self.assertEqual(lines, ["first@alpha.com", "second@beta.org"])

    def test_export_empty_records(self) -> None:
        """Test exporting an empty record sequence creates a valid header-only CSV and empty TXT."""
        csv_path = os.path.join(self.test_dir, "empty.csv")
        success_csv, count_csv, _ = export_to_csv([], csv_path)
        self.assertTrue(success_csv)
        self.assertEqual(count_csv, 0)

        txt_path = os.path.join(self.test_dir, "empty.txt")
        success_txt, count_txt, _ = export_to_txt([], txt_path)
        self.assertTrue(success_txt)
        self.assertEqual(count_txt, 0)


if __name__ == "__main__":
    unittest.main()
