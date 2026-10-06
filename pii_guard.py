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


def line_number(text, position):
    return text.count("\n", 0, position) + 1


def find_emails(text):
    results = []

    for match in EMAIL_PATTERN.finditer(text):
        results.append(("Email", match.group(), line_number(text, match.start())))

    return results


def find_phones(text):
    results = []

    for match in NG_PHONE_PATTERN.finditer(text):
        results.append(("Phone", match.group(), line_number(text, match.start())))

    return results


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
            results.append(("Card", candidate, line_number(text, match.start())))

    return results


def find_ids(text):
    results = []

    for match in ELEVEN_DIGIT_PATTERN.finditer(text):
        number = match.group()
        start = match.start()
        line = line_number(text, start)

        nearby_text = text[max(0, start - 40):start]
        nearby_text = nearby_text.split("\n")[-1]
        nearby_text = nearby_text.split("|")[-1]

        if NIN_KEYWORDS.search(nearby_text):
            if verhoeff_valid(number):
                results.append(("NIN", number, line))
            else:
                results.append(("NIN (checksum failed)", number, line))
        elif BVN_KEYWORDS.search(nearby_text):
            results.append(("BVN", number, line))
        elif NG_PHONE_PATTERN.fullmatch(number):
            continue
        else:
            results.append(("Possible ID", number, line))

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


def mask_email(email):
    name, domain = email.split("@", 1)
    return name[0] + "***@" + domain


def mask_number(value):
    digits = re.sub(r"\D", "", value)
    return "*" * (len(digits) - 4) + digits[-4:]


def mask_value(data_type, value):
    if data_type == "Email":
        return mask_email(value)
    else:
        return mask_number(value)


def get_risk_level(emails, phones, ids, cards):
    has_high_risk_id = any(label != "Possible ID" for label, number, line in ids)

    if cards or has_high_risk_id:
        return "High"
    elif phones or ids:
        return "Medium"
    elif emails:
        return "Low"
    else:
        return "Clean"


def print_findings(title, findings):
    print(f"  {title} found: {len(findings)}")
    for data_type, value, line in findings:
        print(f"    - {data_type}: {mask_value(data_type, value)} (line {line})")


def scan_file(file_path):
    if file_path.suffix.lower() == ".csv":
        text = read_csv_file(file_path)
    else:
        text = read_text_file(file_path)

    emails = find_emails(text)
    ids = find_ids(text)
    cards = find_cards(text)

    id_numbers = [number for label, number, line in ids]
    phones = [
        (data_type, value, line)
        for data_type, value, line in find_phones(text)
        if value not in id_numbers
    ]

    risk = get_risk_level(emails, phones, ids, cards)

    print(f"Scanning: {file_path}")
    print(f"  Risk level: {risk.upper()}")

    print_findings("Emails", emails)
    print_findings("Phone numbers", phones)
    print_findings("ID numbers", ids)
    print_findings("Card numbers", cards)

    print()

    report_rows = []
    for data_type, value, line in emails + phones + ids + cards:
        masked = mask_value(data_type, value)
        report_rows.append([str(file_path), line, data_type, masked, risk])

    return risk, report_rows


def write_report(rows):
    report_folder = Path("reports")
    report_folder.mkdir(exist_ok=True)
    report_path = report_folder / "report.csv"

    with open(report_path, "w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["file", "line", "data_type", "masked_value", "file_risk"])
        writer.writerows(rows)

    return report_path


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

    risk_counts = {"High": 0, "Medium": 0, "Low": 0, "Clean": 0}
    all_rows = []

    for file_path in files:
        risk, report_rows = scan_file(file_path)
        risk_counts[risk] = risk_counts[risk] + 1
        all_rows.extend(report_rows)

    print("Summary")
    print(f"  Files scanned: {len(files)}")
    print(f"  Items found: {len(all_rows)}")
    print("  Files by risk level:")
    for level, count in risk_counts.items():
        print(f"    {level}: {count}")

    report_path = write_report(all_rows)
    print()
    print(f"Report saved to: {report_path}")


if __name__ == "__main__":
    main()