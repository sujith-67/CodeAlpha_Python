"""file_operations.py - File I/O, Reading, and Export Handlers
============================================================
Handles robust reading of single or multiple text files across common encodings,
captures and segregates file-level read errors, and provides formatted CSV and TXT
export facilities for extracted email records.
"""

from __future__ import annotations

import csv
import os
from dataclasses import dataclass
from typing import List, Optional, Sequence, Tuple

from src.email_engine import EmailRecord


# Candidate encodings to try sequentially when opening text files
SUPPORTED_ENCODINGS: Sequence[str] = ("utf-8", "utf-8-sig", "cp1252", "latin-1")


@dataclass
class FileReadOutcome:
    """Outcome of attempting to read an individual text file."""
    filepath: str
    filename: str
    content: str
    success: bool
    error_message: Optional[str] = None


@dataclass
class BatchLoadSummary:
    """Aggregate summary of reading multiple text files."""
    successful_files: List[Tuple[str, str]]   # List of (filename, text_content)
    failed_files: List[Tuple[str, str]]        # List of (filename, error_message)

    @property
    def total_selected(self) -> int:
        return len(self.successful_files) + len(self.failed_files)

    @property
    def success_count(self) -> int:
        return len(self.successful_files)

    @property
    def failure_count(self) -> int:
        return len(self.failed_files)


def read_single_text_file(filepath: str) -> FileReadOutcome:
    """Read an individual text file, testing multiple fallback encodings.

    Args:
        filepath: Absolute or relative path to the text file.

    Returns:
        FileReadOutcome containing the loaded content or failure details.
    """
    filename = os.path.basename(filepath)

    if not os.path.exists(filepath):
        return FileReadOutcome(
            filepath=filepath,
            filename=filename,
            content="",
            success=False,
            error_message="File does not exist"
        )

    if os.path.isdir(filepath):
        return FileReadOutcome(
            filepath=filepath,
            filename=filename,
            content="",
            success=False,
            error_message="Target path is a directory, not a file"
        )

    last_error: Optional[Exception] = None

    for encoding in SUPPORTED_ENCODINGS:
        try:
            with open(filepath, "r", encoding=encoding, errors="strict") as fh:
                content = fh.read()
            return FileReadOutcome(
                filepath=filepath,
                filename=filename,
                content=content,
                success=True,
                error_message=None
            )
        except UnicodeDecodeError as ude:
            last_error = ude
            continue
        except PermissionError:
            return FileReadOutcome(
                filepath=filepath,
                filename=filename,
                content="",
                success=False,
                error_message="Permission denied reading file"
            )
        except OSError as oe:
            return FileReadOutcome(
                filepath=filepath,
                filename=filename,
                content="",
                success=False,
                error_message=f"I/O Error: {oe.strerror or str(oe)}"
            )

    # If all strict encodings failed, attempt utf-8 with replacement
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as fh:
            content = fh.read()
        return FileReadOutcome(
            filepath=filepath,
            filename=filename,
            content=content,
            success=True,
            error_message=None
        )
    except Exception as exc:
        return FileReadOutcome(
            filepath=filepath,
            filename=filename,
            content="",
            success=False,
            error_message=f"Failed to decode text: {exc}"
        )


def read_text_files_batch(filepaths: Sequence[str]) -> BatchLoadSummary:
    """Read a collection of text files, isolating individual failures.

    Args:
        filepaths: Sequence of filepaths to read.

    Returns:
        BatchLoadSummary with successfully loaded files and failed files segregated.
    """
    successful_files: List[Tuple[str, str]] = []
    failed_files: List[Tuple[str, str]] = []

    for path in filepaths:
        outcome = read_single_text_file(path)
        if outcome.success:
            successful_files.append((outcome.filename, outcome.content))
        else:
            failed_files.append((outcome.filename, outcome.error_message or "Unknown error"))

    return BatchLoadSummary(
        successful_files=successful_files,
        failed_files=failed_files
    )


def export_to_csv(records: Sequence[EmailRecord], destination_path: str) -> Tuple[bool, int, Optional[str]]:
    """Export email records to an RFC-compliant CSV file.

    Columns:
        1. Email Address
        2. Validation Status
        3. Occurrences
        4. Source Files
        5. Validation Notes

    Args:
        records: Sequence of EmailRecord items to export.
        destination_path: File system path for the destination CSV file.

    Returns:
        Tuple of (success: bool, records_exported_count: int, error_message: Optional[str])
    """
    if not destination_path:
        return False, 0, "No destination path provided"

    try:
        # Ensure parent directory exists
        parent_dir = os.path.dirname(os.path.abspath(destination_path))
        if parent_dir and not os.path.exists(parent_dir):
            os.makedirs(parent_dir, exist_ok=True)

        with open(destination_path, "w", newline="", encoding="utf-8-sig") as fh:
            writer = csv.writer(fh, quoting=csv.QUOTE_MINIMAL)
            # Header
            writer.writerow([
                "Email Address",
                "Validation Status",
                "Occurrences",
                "Source Files",
                "Validation Notes"
            ])

            for record in records:
                source_str = ", ".join(record.source_files) if record.source_files else "Unknown"
                writer.writerow([
                    record.address,
                    record.validation.status,
                    record.occurrences,
                    source_str,
                    record.validation.reason
                ])

        return True, len(records), None

    except PermissionError:
        return False, 0, "Permission denied writing to the destination CSV file"
    except OSError as oe:
        return False, 0, f"Failed to save CSV file: {oe.strerror or str(oe)}"
    except Exception as exc:
        return False, 0, f"Unexpected error during CSV export: {exc}"


def export_to_txt(records: Sequence[EmailRecord], destination_path: str) -> Tuple[bool, int, Optional[str]]:
    """Export unique email addresses to a plain text file, one address per line.

    Args:
        records: Sequence of EmailRecord items to export.
        destination_path: File system path for the destination TXT file.

    Returns:
        Tuple of (success: bool, addresses_exported_count: int, error_message: Optional[str])
    """
    if not destination_path:
        return False, 0, "No destination path provided"

    try:
        # Ensure parent directory exists
        parent_dir = os.path.dirname(os.path.abspath(destination_path))
        if parent_dir and not os.path.exists(parent_dir):
            os.makedirs(parent_dir, exist_ok=True)

        with open(destination_path, "w", encoding="utf-8") as fh:
            for record in records:
                fh.write(record.address + "\n")

        return True, len(records), None

    except PermissionError:
        return False, 0, "Permission denied writing to the destination TXT file"
    except OSError as oe:
        return False, 0, f"Failed to save TXT file: {oe.strerror or str(oe)}"
    except Exception as exc:
        return False, 0, f"Unexpected error during TXT export: {exc}"
