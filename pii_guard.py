import csv
import re
import sys
from pathlib import Path

EMAIL_PATTERN = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")

NG_PHONE_PATTERN = re.compile(
    r"(?<!\d)"
    r"(?:\+234[ -]?|234[ -]?|0)"
    r"[789][01]\d"
    r"[ -]?\d{3}"
    r"[ -]?\d{4}"
    r"(?!\d)"
)

ELEVEN_DIGIT_PATTERN = re.compile(r"(?<!\d)\d{11}(?!\d)")

NIN_KEYWORDS = re.compile(r"\b(nin|national identification)\b", re.IGNORECASE)
BVN_KEYWORDS = re.compile(r"\b(bvn|bank verification)\b", re.IGNORECASE)

SUPPORTED_EXTENSIONS = {".txt", ".csv"}

CARD_PATTERN = re.compile(r"(?<!\d)(?:\d[ -]?){12,18}\d(?!\d)")

VERHOEFF_MULTIPLY = [
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
    [1, 2, 3, 4, 0, 6, 7, 8, 9, 5],
    [2, 3, 4, 0, 1, 7, 8, 9, 5, 6],
    [3, 4, 0, 1, 2, 8, 9, 5, 6, 7],
    [4, 0, 1, 2, 3, 9, 5, 6, 7, 8],
    [5, 9, 8, 7, 6, 0, 4, 3, 2, 1],
    [6, 5, 9, 8, 7, 1, 0, 4, 3, 2],
    [7, 6, 5, 9, 8, 2, 1, 0, 4, 3],
    [8, 7, 6, 5, 9, 3, 2, 1, 0, 4],
    [9, 8, 7, 6, 5, 4, 3, 2, 1, 0],
]

VERHOEFF_PERMUTE = [
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
    [1, 5, 7, 6, 2, 8, 3, 0, 9, 4],
    [5, 8, 0, 3, 7, 9, 6, 1, 4, 2],
    [8, 9, 1, 6, 0, 4, 3, 5, 2, 7],
    [9, 4, 5, 3, 1, 2, 7, 6, 8, 0],
    [4, 2, 8, 6, 5, 7, 3, 9, 0, 1],
    [2, 7, 9, 3, 8, 0, 6, 4, 1, 5],
    [7, 0, 4, 6, 9, 1, 3, 2, 5, 8],
]


def find_emails(text):
    return EMAIL_PATTERN.findall(text)


def find_phones(text):
    return NG_PHONE_PATTERN.findall(text)


def luhn_valid(number):
    total = 0

    for position, digit in enumerate(number[::-1]):
        n = int(digit)
        if position % 2 == 1:
            n = n * 2
            if n > 9:
                n = n - 9
        total = total + n

    return total % 10 == 0


def verhoeff_valid(number):
    check = 0

    for position, digit in enumerate(number[::-1]):
        row = VERHOEFF_PERMUTE[position % 8]
        check = VERHOEFF_MULTIPLY[check][row[int(digit)]]

    return check == 0


def find_cards(text):
    results = []

    for match in CARD_PATTERN.finditer(text):
        candidate = match.group()

        if NG_PHONE_PATTERN.fullmatch(candidate):
            continue

        digits_only = re.sub(r"[ -]", "", candidate)

        if luhn_valid(digits_only):
            results.append(candidate)

    return results


def find_ids(text):
    results = []

    for match in ELEVEN_DIGIT_PATTERN.finditer(text):
        number = match.group()
        start = match.start()

        nearby_text = text[max(0, start - 40):start]
        nearby_text = nearby_text.split("\n")[-1]
        nearby_text = nearby_text.split("|")[-1]

        if NIN_KEYWORDS.search(nearby_text):
            if verhoeff_valid(number):
                results.append(("NIN", number))
            else:
                results.append(("NIN (checksum failed)", number))
        elif BVN_KEYWORDS.search(nearby_text):
            results.append(("BVN", number))
        elif NG_PHONE_PATTERN.fullmatch(number):
            continue
        else:
            results.append(("Possible ID", number))

    return results


def read_text_file(file_path):
    with open(file_path, "r", encoding="utf-8", errors="replace") as file:
        return file.read()


def read_csv_file(file_path):
    with open(file_path, "r", encoding="utf-8-sig", errors="replace", newline="") as file:
        rows = list(csv.reader(file))

    if not rows:
        return ""

    headers = [header.replace("_", " ") for header in rows[0]]
    lines = [", ".join(rows[0])]

    for row in rows[1:]:
        cells = [f"{header}: {value}" for header, value in zip(headers, row)]
        lines.append(" | ".join(cells))

    return "\n".join(lines)


def find_files(folder):
    found = []

    for path in sorted(Path(folder).rglob("*")):
        relative_parts = path.relative_to(folder).parts
        if any(part.startswith(".") for part in relative_parts):
            continue
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS:
            found.append(path)

    return found


def scan_file(file_path):
    if file_path.suffix.lower() == ".csv":
        text = read_csv_file(file_path)
    else:
        text = read_text_file(file_path)

    emails = find_emails(text)
    ids = find_ids(text)
    cards = find_cards(text)

    id_numbers = [number for label, number in ids]
    phones = [phone for phone in find_phones(text) if phone not in id_numbers]

    print(f"Scanning: {file_path}")

    print(f"  Emails found: {len(emails)}")
    for email in emails:
        print(f"    - {email}")

    print(f"  Phone numbers found: {len(phones)}")
    for phone in phones:
        print(f"    - {phone}")

    print(f"  ID numbers found: {len(ids)}")
    for label, number in ids:
        print(f"    - {label}: {number}")

    print(f"  Card numbers found: {len(cards)}")
    for card in cards:
        print(f"    - {card}")

    print()


def main():
    if len(sys.argv) > 1:
        folder = sys.argv[1]
    else:
        folder = "samples"

    if not Path(folder).is_dir():
        print(f"Folder not found: {folder}")
        return

    files = find_files(folder)

    if not files:
        print(f"No .txt or .csv files found in: {folder}")
        return

    print(f"Found {len(files)} file(s) to scan in: {folder}")
    print()

    for file_path in files:
        scan_file(file_path)


if __name__ == "__main__":
    main()