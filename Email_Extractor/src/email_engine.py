"""email_engine.py - Core Email Extraction & Syntax Validation Engine
===================================================================
Provides robust, RFC-guided email candidate extraction from raw text,
case-insensitive deduplication, occurrence frequency tracking, source file
provenance attribution, and thorough local syntax validation.

IMPORTANT:
    This engine validates email address syntax strictly through local rule-based
    analysis. It does NOT perform DNS MX queries or verify mailbox existence,
    activity, or deliverability.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple


# RFC 5321 / 5322 constraints
MAX_TOTAL_EMAIL_LENGTH = 254
MAX_LOCAL_PART_LENGTH = 64
MAX_DOMAIN_LENGTH = 255
MAX_DOMAIN_LABEL_LENGTH = 63

# Characters allowed in local-part per standard specification (unquoted)
# a-z, A-Z, 0-9, and specific printable ASCII punctuation
LOCAL_PART_ALLOWED_CHARS = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!#$%&'*+-/=?^_`{|}~.")

# Characters commonly surrounding email addresses in unstructured text
SURROUNDING_PUNCTUATION = ".,:;!?\"'()[]{}<>` \t\r\n"

# Candidate extraction pattern:
# Extracts tokens containing '@' surrounded by potential email characters.
# Candidates are subsequently cleaned of surrounding sentence punctuation and
# evaluated by validate_email_syntax().
CANDIDATE_REGEX = re.compile(
    r"[a-zA-Z0-9!#$%&'*+/=?^_`{|}~.-]+@[a-zA-Z0-9.-]+"
)


@dataclass(frozen=True)
class ValidationResult:
    """Represents the syntax validation outcome for an email candidate."""
    is_valid: bool
    status: str          # "Valid" or "Needs Review"
    reason: str          # Descriptive explanation of the validation outcome


@dataclass
class EmailRecord:
    """Represents a unique email address with provenance and validation metadata."""
    address: str                             # Original casing from first occurrence
    normalized: str                          # Lowercase identifier for deduplication
    validation: ValidationResult             # Syntax validation outcome
    occurrences: int = 1                     # Total times observed across all sources
    source_files: List[str] = field(default_factory=list)  # Files containing this email

    def add_occurrence(self, source_file: str) -> None:
        """Increment count and record the source file if not already present."""
        self.occurrences += 1
        if source_file and source_file not in self.source_files:
            self.source_files.append(source_file)


@dataclass
class ExtractionStats:
    """Live summary statistics for an extraction run."""
    total_matches: int = 0         # All extracted email occurrences (including duplicates)
    unique_emails: int = 0         # Number of distinct email addresses (case-insensitive)
    duplicates_removed: int = 0    # Total Matches - Unique Emails
    valid_emails: int = 0          # Addresses passing syntax checks
    needs_review: int = 0          # Addresses failing syntax checks


def validate_email_syntax(candidate: str) -> ValidationResult:
    """Validate email address syntax against RFC-guided structural rules.

    Checks:
        1. Non-empty candidate string.
        2. Maximum total length (254 chars).
        3. Exactly one '@' symbol.
        4. Non-empty local-part and domain.
        5. Maximum local-part length (64 chars).
        6. Maximum domain length (255 chars).
        7. No leading or trailing dots in local-part or domain.
        8. No consecutive dots ('..') in local-part or domain.
        9. Local-part contains only allowed RFC characters.
        10. Domain contains at least two labels (domain name + TLD).
        11. Domain labels do not exceed 63 characters each.
        12. Domain labels consist of alphanumeric characters and hyphens.
        13. Domain labels do not start or end with a hyphen.
        14. Top-level domain (TLD) is at least 2 alphabetic characters (or valid punycode).

    Returns:
        ValidationResult with is_valid, status ('Valid' / 'Needs Review'), and reason.
    """
    if not candidate or not isinstance(candidate, str):
        return ValidationResult(
            is_valid=False,
            status="Needs Review",
            reason="Empty or non-string email candidate"
        )

    # Clean candidate of whitespace
    email = candidate.strip()

    # Rule 1: Total length limit
    if len(email) > MAX_TOTAL_EMAIL_LENGTH:
        return ValidationResult(
            is_valid=False,
            status="Needs Review",
            reason=f"Address exceeds maximum RFC length of {MAX_TOTAL_EMAIL_LENGTH} characters ({len(email)} chars)"
        )

    # Rule 2: Exactly one '@' symbol
    at_count = email.count("@")
    if at_count == 0:
        return ValidationResult(
            is_valid=False,
            status="Needs Review",
            reason="Missing '@' separator symbol"
        )
    if at_count > 1:
        return ValidationResult(
            is_valid=False,
            status="Needs Review",
            reason=f"Contains multiple '@' symbols ({at_count} found)"
        )

    local_part, domain = email.split("@", 1)

    # Rule 3: Non-empty parts
    if not local_part:
        return ValidationResult(
            is_valid=False,
            status="Needs Review",
            reason="Local part (before '@') cannot be empty"
        )
    if not domain:
        return ValidationResult(
            is_valid=False,
            status="Needs Review",
            reason="Domain part (after '@') cannot be empty"
        )

    # Rule 4: Local-part length limit
    if len(local_part) > MAX_LOCAL_PART_LENGTH:
        return ValidationResult(
            is_valid=False,
            status="Needs Review",
            reason=f"Local part exceeds maximum RFC length of {MAX_LOCAL_PART_LENGTH} characters ({len(local_part)} chars)"
        )

    # Rule 5: Domain length limit
    if len(domain) > MAX_DOMAIN_LENGTH:
        return ValidationResult(
            is_valid=False,
            status="Needs Review",
            reason=f"Domain exceeds maximum RFC length of {MAX_DOMAIN_LENGTH} characters ({len(domain)} chars)"
        )

    # Rule 6: Consecutive dots
    if ".." in local_part:
        return ValidationResult(
            is_valid=False,
            status="Needs Review",
            reason="Local part contains consecutive dots ('..')"
        )
    if ".." in domain:
        return ValidationResult(
            is_valid=False,
            status="Needs Review",
            reason="Domain contains consecutive dots ('..')"
        )

    # Rule 7: Leading / trailing dots
    if local_part.startswith(".") or local_part.endswith("."):
        return ValidationResult(
            is_valid=False,
            status="Needs Review",
            reason="Local part cannot start or end with a dot"
        )
    if domain.startswith(".") or domain.endswith("."):
        return ValidationResult(
            is_valid=False,
            status="Needs Review",
            reason="Domain cannot start or end with a dot"
        )

    # Rule 8: Allowed characters in local part
    invalid_local_chars = set(local_part) - LOCAL_PART_ALLOWED_CHARS
    if invalid_local_chars:
        sample_chars = "".join(sorted(invalid_local_chars)[:3])
        return ValidationResult(
            is_valid=False,
            status="Needs Review",
            reason=f"Local part contains invalid characters: '{sample_chars}'"
        )

    # Rule 9: Domain structure and labels
    labels = domain.split(".")
    if len(labels) < 2:
        return ValidationResult(
            is_valid=False,
            status="Needs Review",
            reason="Domain must contain at least a domain name and top-level domain (e.g., example.com)"
        )

    for idx, label in enumerate(labels):
        if not label:
            return ValidationResult(
                is_valid=False,
                status="Needs Review",
                reason="Domain contains an empty label between dots"
            )
        if len(label) > MAX_DOMAIN_LABEL_LENGTH:
            return ValidationResult(
                is_valid=False,
                status="Needs Review",
                reason=f"Domain label '{label[:10]}...' exceeds maximum of {MAX_DOMAIN_LABEL_LENGTH} characters"
            )
        if label.startswith("-") or label.endswith("-"):
            return ValidationResult(
                is_valid=False,
                status="Needs Review",
                reason=f"Domain label '{label}' cannot start or end with a hyphen"
            )
        # Check label characters: alphanumeric and hyphen only
        for ch in label:
            if not (ch.isalnum() or ch == "-"):
                return ValidationResult(
                    is_valid=False,
                    status="Needs Review",
                    reason=f"Domain label '{label}' contains invalid character '{ch}'"
                )

    # Rule 10: Top-level domain (TLD) requirements
    tld = labels[-1]
    if len(tld) < 2:
        return ValidationResult(
            is_valid=False,
            status="Needs Review",
            reason=f"Top-level domain '.{tld}' is too short (must be at least 2 characters)"
        )

    # TLD must be either all alphabetic letters or valid IDN punycode (e.g., xn--...)
    if not (tld.isalpha() or (tld.startswith("xn--") and tld[4:].isalnum())):
        return ValidationResult(
            is_valid=False,
            status="Needs Review",
            reason=f"Top-level domain '.{tld}' must consist of alphabetic characters"
        )

    # All syntax criteria satisfied
    return ValidationResult(
        is_valid=True,
        status="Valid",
        reason="Passed RFC-guided syntax structure checks"
    )


def clean_extracted_token(raw_token: str) -> Optional[str]:
    """Strip extraneous leading and trailing punctuation from an extracted token.

    Handles tokens enclosed in quotes, angle brackets, parentheses, or trailing
    sentence punctuation (periods, commas, colons, semicolons, exclamation marks).
    Also strips any 'mailto:' prefix if present.
    """
    if not raw_token:
        return None

    cleaned = raw_token.strip(SURROUNDING_PUNCTUATION)

    # Strip mailto: scheme if present
    if cleaned.lower().startswith("mailto:"):
        cleaned = cleaned[7:].strip(SURROUNDING_PUNCTUATION)

    # If the candidate still has surrounding angle brackets, quotes, or parens
    while cleaned and cleaned[0] in "<(\"'" and cleaned[-1] in ">)\"'":
        cleaned = cleaned[1:-1].strip(SURROUNDING_PUNCTUATION)
        if cleaned.lower().startswith("mailto:"):
            cleaned = cleaned[7:].strip(SURROUNDING_PUNCTUATION)

    # Strip again to remove any newly exposed outer punctuation
    cleaned = cleaned.strip(SURROUNDING_PUNCTUATION)

    # Must retain '@' to remain an email candidate
    if "@" not in cleaned:
        return None

    return cleaned if cleaned else None


def extract_candidates_from_text(text: str) -> List[str]:
    """Extract raw candidate email strings from an arbitrary text document.

    Surrounding sentence punctuation (e.g., periods, commas, angle brackets)
    is stripped while preserving the candidate's inner characters.
    """
    if not text:
        return []

    raw_matches = CANDIDATE_REGEX.findall(text)
    candidates: List[str] = []

    for match in raw_matches:
        cleaned = clean_extracted_token(match)
        if cleaned:
            candidates.append(cleaned)

    return candidates


class EmailExtractionEngine:
    """Coordinates email candidate extraction, deduplication, occurrence frequency,

    provenance tracking, and syntax validation across one or multiple documents.
    """

    def __init__(self) -> None:
        # Key: normalized email (lowercase), Value: EmailRecord
        self._records: Dict[str, EmailRecord] = {}
        self._total_matches: int = 0

    def reset(self) -> None:
        """Clear all stored extraction records and counters."""
        self._records.clear()
        self._total_matches = 0

    def process_text(self, text: str, source_filename: str = "input.txt") -> int:
        """Extract and index email addresses from a single text source.

        Args:
            text: The raw text content to parse.
            source_filename: Display name of the source file.

        Returns:
            The number of email candidate occurrences extracted from this source.
        """
        candidates = extract_candidates_from_text(text)
        self._total_matches += len(candidates)

        for candidate in candidates:
            norm_key = candidate.lower()
            if norm_key in self._records:
                self._records[norm_key].add_occurrence(source_filename)
            else:
                validation = validate_email_syntax(candidate)
                record = EmailRecord(
                    address=candidate,
                    normalized=norm_key,
                    validation=validation,
                    occurrences=1,
                    source_files=[source_filename] if source_filename else []
                )
                self._records[norm_key] = record

        return len(candidates)

    def process_sources(self, sources: List[Tuple[str, str]]) -> ExtractionStats:
        """Process a collection of sources: List of (source_filename, text_content).

        Replaces previous records with fresh extraction results.

        Returns:
            Computed ExtractionStats summary.
        """
        self.reset()
        for source_filename, content in sources:
            self.process_text(content, source_filename)
        return self.get_statistics()

    def get_records(self) -> List[EmailRecord]:
        """Return all unique email records in order of discovery."""
        return list(self._records.values())

    def get_statistics(self) -> ExtractionStats:
        """Calculate and return live summary statistics."""
        records = list(self._records.values())
        unique_count = len(records)
        total_matches = self._total_matches
        duplicates_removed = max(0, total_matches - unique_count)

        valid_count = sum(1 for r in records if r.validation.is_valid)
        needs_review_count = unique_count - valid_count

        return ExtractionStats(
            total_matches=total_matches,
            unique_emails=unique_count,
            duplicates_removed=duplicates_removed,
            valid_emails=valid_count,
            needs_review=needs_review_count
        )
