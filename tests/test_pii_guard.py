import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import pii_guard


def values(findings):
    return [value for data_type, value, line in findings]


def labels(findings):
    return [data_type for data_type, value, line in findings]


class TestLuhn(unittest.TestCase):
    def test_valid_test_cards_pass(self):
        for number in ["4111111111111111", "5500000000000004", "4012888888881881"]:
            self.assertTrue(pii_guard.luhn_valid(number), number)

    def test_typo_fails(self):
        self.assertFalse(pii_guard.luhn_valid("4111111111111112"))

    def test_random_number_fails(self):
        self.assertFalse(pii_guard.luhn_valid("1234567812345678"))


class TestVerhoeff(unittest.TestCase):
    def test_valid_nins_pass(self):
        for number in ["12345678904", "70000000004", "08000000002"]:
            self.assertTrue(pii_guard.verhoeff_valid(number), number)

    def test_wrong_check_digit_fails(self):
        self.assertFalse(pii_guard.verhoeff_valid("12345678901"))

    def test_swapped_digits_fail(self):
        self.assertFalse(pii_guard.verhoeff_valid("21345678904"))


class TestEmails(unittest.TestCase):
    def test_finds_email(self):
        found = pii_guard.find_emails("Contact: ada.eze@example.com today")
        self.assertEqual(values(found), ["ada.eze@example.com"])

    def test_ignores_written_out_email(self):
        self.assertEqual(pii_guard.find_emails("support at example dot com"), [])


class TestPhones(unittest.TestCase):
    def test_finds_all_formats(self):
        text = "0803 000 0001, +234 805 000 0002, 09010000003"
        found = pii_guard.find_phones(text)
        self.assertEqual(values(found), ["0803 000 0001", "+234 805 000 0002", "09010000003"])

    def test_ignores_longer_number(self):
        self.assertEqual(pii_guard.find_phones("Order 2340801000000456"), [])

    def test_ignores_short_number(self):
        self.assertEqual(pii_guard.find_phones("Ref 0803000"), [])

    def test_finds_bracket_and_dot_formats(self):
        text = "(0803) 123 4567 and 0805.123.4567"
        found = pii_guard.find_phones(text)
        self.assertEqual(values(found), ["(0803) 123 4567", "0805.123.4567"])

    def test_ignores_dates_and_amounts(self):
        self.assertEqual(pii_guard.find_phones("Paid NGN 150,000.00 on 13.10.2026"), [])


class TestIds(unittest.TestCase):
    def test_nin_and_bvn_labels(self):
        found = pii_guard.find_ids("NIN: 12345678904\nBVN: 22000000001")
        self.assertEqual(labels(found), ["NIN", "BVN"])

    def test_failed_checksum_is_flagged(self):
        found = pii_guard.find_ids("NIN: 12345678901")
        self.assertEqual(labels(found), ["NIN (checksum failed)"])

    def test_evening_is_not_a_nin_label(self):
        found = pii_guard.find_ids("Evening shift code: 33300000007")
        self.assertEqual(labels(found), ["Possible ID"])

    def test_unlabelled_phone_is_not_an_id(self):
        self.assertEqual(pii_guard.find_ids("Phone: 08100000004"), [])

    def test_label_on_line_above(self):
        found = pii_guard.find_ids("NIN:\n12345678904")
        self.assertEqual(labels(found), ["NIN"])

    def test_line_above_with_numbers_is_not_a_label(self):
        found = pii_guard.find_ids("NIN: 12345678904\n55500000009")
        self.assertEqual(labels(found), ["NIN", "Possible ID"])

    def test_line_numbers(self):
        found = pii_guard.find_ids("Title\n\nNIN: 12345678904")
        self.assertEqual(found[0][2], 3)


class TestCards(unittest.TestCase):
    def test_finds_cards_in_different_formats(self):
        text = "4111 1111 1111 1111 and 5500-0000-0000-0004 and 5061 0000 0000 0000 007"
        self.assertEqual(len(pii_guard.find_cards(text)), 3)

    def test_rejects_luhn_failure(self):
        self.assertEqual(pii_guard.find_cards("4111 1111 1111 1112"), [])

    def test_phone_is_not_a_card(self):
        self.assertEqual(pii_guard.find_cards("+234 805 000 0002"), [])


class TestMasking(unittest.TestCase):
    def test_mask_email(self):
        self.assertEqual(pii_guard.mask_email("tunde.bakare@example.com"), "t***@example.com")

    def test_mask_number_keeps_last_four(self):
        self.assertEqual(pii_guard.mask_number("12345678904"), "*******8904")

    def test_mask_number_ignores_spaces(self):
        self.assertEqual(pii_guard.mask_number("4111 1111 1111 1111"), "************1111")


class TestRiskLevels(unittest.TestCase):
    def test_high(self):
        ids = [("NIN", "12345678904", 1)]
        self.assertEqual(pii_guard.get_risk_level([], [], ids, []), "High")

    def test_medium(self):
        ids = [("Possible ID", "55500000009", 1)]
        self.assertEqual(pii_guard.get_risk_level([], [], ids, []), "Medium")

    def test_low(self):
        emails = [("Email", "a@example.com", 1)]
        self.assertEqual(pii_guard.get_risk_level(emails, [], [], []), "Low")

    def test_clean(self):
        self.assertEqual(pii_guard.get_risk_level([], [], [], []), "Clean")


class TestFiles(unittest.TestCase):
    def test_csv_values_get_column_labels(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "people.csv"
            path.write_text("name,nin,bvn\nAda,12345678904,22000000001\n", encoding="utf-8")
            text = pii_guard.read_csv_file(path)
        self.assertEqual(labels(pii_guard.find_ids(text)), ["NIN", "BVN"])

    def test_find_files_skips_hidden_folders_and_other_types(self):
        with tempfile.TemporaryDirectory() as folder:
            (Path(folder) / "a.txt").write_text("x", encoding="utf-8")
            (Path(folder) / "b.csv").write_text("x", encoding="utf-8")
            (Path(folder) / "c.pdf").write_text("x", encoding="utf-8")
            (Path(folder) / ".hidden").mkdir()
            (Path(folder) / ".hidden" / "d.txt").write_text("x", encoding="utf-8")
            names = [path.name for path in pii_guard.find_files(folder)]
        self.assertEqual(names, ["a.txt", "b.csv"])


class TestCommandLine(unittest.TestCase):
    def test_scanner_runs_on_samples(self):
        result = subprocess.run(
            [sys.executable, "pii_guard.py", "samples"],
            capture_output=True,
            text=True,
        )
        self.assertIn("Files scanned: 6", result.stdout)
        self.assertIn("Items found: 32", result.stdout)


if __name__ == "__main__":
    unittest.main()