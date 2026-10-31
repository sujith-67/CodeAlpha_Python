"""test_email_engine.py - Automated Unit Tests for Email Extraction & Validation
==============================================================================
Validates:
- Extraction of standard, uppercase, multiple, and duplicate email candidates.
- Stripping of surrounding sentence punctuation.
- Case-insensitive deduplication and first-occurrence casing preservation.
- Occurrence frequency and multi-source tracking.
- Statistics calculations (total matches, unique, duplicates, valid, needs review).
- Comprehensive syntax validation edge cases.
"""

from __future__ import annotations

import unittest
from src.email_engine import (
    EmailExtractionEngine,
    ExtractionStats,
    clean_extracted_token,
    extract_candidates_from_text,
    validate_email_syntax,
)


class TestEmailExtraction(unittest.TestCase):
    """Tests for extracting email candidates from text strings."""

    def setUp(self) -> None:
        self.engine = EmailExtractionEngine()

    def test_ordinary_email(self) -> None:
        """Test extraction of a simple, standard email address."""
        text = "Please reach out to support@example.com for assistance."
        candidates = extract_candidates_from_text(text)
        self.assertIn("support@example.com", candidates)
        self.assertEqual(len(candidates), 1)

    def test_uppercase_email(self) -> None:
        """Test extraction of uppercase email addresses."""
        text = "Send queries to ADMIN@COMPANY.ORG right away."
        candidates = extract_candidates_from_text(text)
        self.assertIn("ADMIN@COMPANY.ORG", candidates)

    def test_multiple_addresses_in_one_file(self) -> None:
        """Test extraction of multiple distinct email addresses in arbitrary text."""
        text = (
            "Primary: contact@site.com\n"
            "Billing: billing@site.com\n"
            "Tech support: support@cloud.net"
        )
        candidates = extract_candidates_from_text(text)
        self.assertEqual(len(candidates), 3)
        self.assertIn("contact@site.com", candidates)
        self.assertIn("billing@site.com", candidates)
        self.assertIn("support@cloud.net", candidates)

    def test_duplicate_addresses_same_case(self) -> None:
        """Test handling of identical duplicate email addresses."""
        text = "Email sales@shop.com or write to sales@shop.com again."
        self.engine.process_text(text, "file1.txt")
        records = self.engine.get_records()

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].address, "sales@shop.com")
        self.assertEqual(records[0].occurrences, 2)
        self.assertEqual(records[0].source_files, ["file1.txt"])

        stats = self.engine.get_statistics()
        self.assertEqual(stats.total_matches, 2)
        self.assertEqual(stats.unique_emails, 1)
        self.assertEqual(stats.duplicates_removed, 1)

    def test_different_letter_case_duplicates(self) -> None:
        """Test case-insensitive deduplication and preservation of first-seen casing."""
        text = "First seen: HelpDesk@Service.com and later helpdesk@service.com or HELPDESK@SERVICE.COM"
        self.engine.process_text(text, "file1.txt")
        records = self.engine.get_records()

        self.assertEqual(len(records), 1)
        # Should preserve original casing of first occurrence
        self.assertEqual(records[0].address, "HelpDesk@Service.com")
        self.assertEqual(records[0].occurrences, 3)

        stats = self.engine.get_statistics()
        self.assertEqual(stats.total_matches, 3)
        self.assertEqual(stats.unique_emails, 1)
        self.assertEqual(stats.duplicates_removed, 2)

    def test_surrounding_punctuation_stripping(self) -> None:
        """Verify trailing dots, commas, quotes, brackets, angle brackets are cleaned."""
        test_cases = [
            ("<user@example.com>", "user@example.com"),
            ("(user@example.com)", "user@example.com"),
            ("[user@example.com]", "user@example.com"),
            ("\"user@example.com\"", "user@example.com"),
            ("'user@example.com'", "user@example.com"),
            ("user@example.com.", "user@example.com"),
            ("user@example.com,", "user@example.com"),
            ("user@example.com;", "user@example.com"),
            ("user@example.com:", "user@example.com"),
            ("user@example.com!", "user@example.com"),
            ("user@example.com?", "user@example.com"),
            ("<mailto:user@example.com>", "user@example.com"),
        ]

        for raw_input, expected in test_cases:
            cleaned = clean_extracted_token(raw_input)
            self.assertEqual(
                cleaned,
                expected,
                f"Failed cleaning '{raw_input}': got '{cleaned}', expected '{expected}'"
            )

    def test_empty_input(self) -> None:
        """Test extraction with empty string input."""
        candidates = extract_candidates_from_text("")
        self.assertEqual(candidates, [])

        self.engine.process_text("", "empty.txt")
        self.assertEqual(self.engine.get_records(), [])
        stats = self.engine.get_statistics()
        self.assertEqual(stats.total_matches, 0)
        self.assertEqual(stats.unique_emails, 0)

    def test_text_without_email_addresses(self) -> None:
        """Test extraction from plain prose containing no email addresses."""
        text = "The quick brown fox jumps over the lazy dog 1234567890."
        candidates = extract_candidates_from_text(text)
        self.assertEqual(candidates, [])

    def test_malformed_candidates_extracted_for_review(self) -> None:
        """Ensure candidates with syntax defects are captured for review, not silently dropped."""
        text = "Flag this: user@-invalid.com and test..double@domain.org"
        candidates = extract_candidates_from_text(text)
        self.assertIn("user@-invalid.com", candidates)
        self.assertIn("test..double@domain.org", candidates)

        self.engine.process_text(text, "flags.txt")
        stats = self.engine.get_statistics()
        self.assertEqual(stats.needs_review, 2)
        self.assertEqual(stats.valid_emails, 0)

    def test_multi_file_source_tracking(self) -> None:
        """Test occurrence and source file tracking across distinct source documents."""
        sources = [
            ("file_a.txt", "common@domain.com and alpha@domain.com"),
            ("file_b.txt", "common@domain.com and beta@domain.com"),
            ("file_c.txt", "COMMON@DOMAIN.COM"),
        ]
        stats = self.engine.process_sources(sources)

        self.assertEqual(stats.total_matches, 5)
        self.assertEqual(stats.unique_emails, 3)
        self.assertEqual(stats.duplicates_removed, 2)

        records_by_norm = {r.normalized: r for r in self.engine.get_records()}
        common_rec = records_by_norm["common@domain.com"]
        self.assertEqual(common_rec.occurrences, 3)
        self.assertEqual(common_rec.source_files, ["file_a.txt", "file_b.txt", "file_c.txt"])


class TestEmailValidation(unittest.TestCase):
    """Tests for rule-based local email syntax validation."""

    def test_valid_email_syntax(self) -> None:
        """Test legitimate email address syntaxes."""
        valid_samples = [
            "alex.chen@technova.org",
            "support+billing@cloudpeak.io",
            "first_last@company.co.uk",
            "user.name123@sub.domain.com",
            "customer-service@portal.net",
        ]
        for address in valid_samples:
            result = validate_email_syntax(address)
            self.assertTrue(result.is_valid, f"Expected '{address}' to be valid. Reason: {result.reason}")
            self.assertEqual(result.status, "Valid")

    def test_missing_at_symbol(self) -> None:
        """Test candidate with no '@' symbol."""
        result = validate_email_syntax("notanemail.com")
        self.assertFalse(result.is_valid)
        self.assertEqual(result.status, "Needs Review")
        self.assertIn("Missing '@'", result.reason)

    def test_multiple_at_symbols(self) -> None:
        """Test candidate with multiple '@' symbols."""
        result = validate_email_syntax("user@@domain.com")
        self.assertFalse(result.is_valid)
        self.assertEqual(result.status, "Needs Review")
        self.assertIn("multiple '@'", result.reason)

    def test_empty_local_part(self) -> None:
        """Test candidate with missing local part."""
        result = validate_email_syntax("@example.com")
        self.assertFalse(result.is_valid)
        self.assertEqual(result.status, "Needs Review")
        self.assertIn("Local part", result.reason)

    def test_empty_domain(self) -> None:
        """Test candidate with missing domain."""
        result = validate_email_syntax("user@")
        self.assertFalse(result.is_valid)
        self.assertEqual(result.status, "Needs Review")
        self.assertIn("Domain part", result.reason)

    def test_consecutive_dots(self) -> None:
        """Test candidate with consecutive dots in local part or domain."""
        res_local = validate_email_syntax("user..name@example.com")
        self.assertFalse(res_local.is_valid)
        self.assertIn("consecutive dots", res_local.reason.lower())

        res_domain = validate_email_syntax("user@example..com")
        self.assertFalse(res_domain.is_valid)
        self.assertIn("consecutive dots", res_domain.reason.lower())

    def test_leading_trailing_dots(self) -> None:
        """Test candidate with leading or trailing dots."""
        res1 = validate_email_syntax(".user@example.com")
        self.assertFalse(res1.is_valid)
        self.assertIn("cannot start or end with a dot", res1.reason)

        res2 = validate_email_syntax("user.@example.com")
        self.assertFalse(res2.is_valid)
        self.assertIn("cannot start or end with a dot", res2.reason)

    def test_invalid_domain_labels(self) -> None:
        """Test domain labels starting/ending with hyphen or containing illegal characters."""
        res_hyphen_start = validate_email_syntax("user@-domain.com")
        self.assertFalse(res_hyphen_start.is_valid)
        self.assertIn("hyphen", res_hyphen_start.reason)

        res_hyphen_end = validate_email_syntax("user@domain-.com")
        self.assertFalse(res_hyphen_end.is_valid)
        self.assertIn("hyphen", res_hyphen_end.reason)

        res_no_tld = validate_email_syntax("user@localhost")
        self.assertFalse(res_no_tld.is_valid)
        self.assertIn("at least a domain name and top-level domain", res_no_tld.reason)

    def test_invalid_top_level_domains(self) -> None:
        """Test invalid TLDs (too short or containing digits)."""
        res_short = validate_email_syntax("user@domain.c")
        self.assertFalse(res_short.is_valid)
        self.assertIn("too short", res_short.reason)

        res_numeric = validate_email_syntax("user@domain.123")
        self.assertFalse(res_numeric.is_valid)
        self.assertIn("alphabetic characters", res_numeric.reason)

    def test_excessive_address_length(self) -> None:
        """Test RFC maximum length constraint violations."""
        long_local = "a" * 65 + "@example.com"
        res_local = validate_email_syntax(long_local)
        self.assertFalse(res_local.is_valid)
        self.assertIn("Local part exceeds", res_local.reason)

        long_domain = "user@" + ("a" * 60 + ".") * 4 + "com"
        if len(long_domain) > 254:
            res_total = validate_email_syntax(long_domain)
            self.assertFalse(res_total.is_valid)
            self.assertIn("exceeds maximum", res_total.reason)


if __name__ == "__main__":
    unittest.main()
