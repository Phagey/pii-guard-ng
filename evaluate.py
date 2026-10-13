import csv
import random
import re
import shutil
from collections import Counter
from pathlib import Path

import pii_guard

DATA_FOLDER = Path("eval_data")
SEED = 42
TEXT_FILES = 20
CSV_FILES = 5
ITEMS_PER_TEXT_FILE = 14
ROWS_PER_CSV_FILE = 10

DATA_TYPES = ["Email", "Phone", "NIN", "NIN (checksum failed)", "BVN", "Card", "Possible ID"]

FIRST_NAMES = ["ada", "tunde", "ngozi", "musa", "chiamaka", "bello", "femi", "aisha", "emeka", "kemi"]
LAST_NAMES = ["eze", "bakare", "okafor", "sani", "obi", "adeyemi", "yusuf", "nwosu", "balogun"]
DOMAINS = ["example.com", "example.org", "example.net"]
PHONE_PREFIXES = ["0703", "0705", "0706", "0803", "0806", "0810", "0813", "0816", "0905", "0916"]

TEMPLATES = {
    "Email": ["Please email {v} for details.", "Contact: {v}", "Send the invoice to {v} by Friday."],
    "Phone": ["Customer {n} called from {v}.", "Phone: {v}", "Reach {n} on {v} after 5pm."],
    "NIN": ["NIN: {v}", "National Identification Number {v}", "Staff {n} - NIN {v}"],
    "BVN": ["BVN: {v}", "Bank Verification Number: {v}", "{n} BVN {v}"],
    "Card": ["Paid with card {v}.", "Card on file: {v}", "Refund to card {v} approved."],
    "Possible ID": ["Reference {v} was used for payroll.", "File ref {v}"],
}

FILLER = [
    "The team agreed to update the website.",
    "Budget review moved to next quarter.",
    "Please confirm attendance for Monday.",
]


def digits(rng, count):
    return "".join(rng.choice("0123456789") for _ in range(count))


def add_check_digit(body, is_valid):
    for digit in "0123456789":
        if is_valid(body + digit):
            return body + digit


def make_name(rng):
    return rng.choice(FIRST_NAMES).title() + " " + rng.choice(LAST_NAMES).title()


def make_email(rng):
    return f"{rng.choice(FIRST_NAMES)}.{rng.choice(LAST_NAMES)}{rng.randint(1, 99)}@{rng.choice(DOMAINS)}"


def make_phone(rng):
    prefix = rng.choice(PHONE_PREFIXES)
    middle = digits(rng, 3)
    end = digits(rng, 4)
    style = rng.choice(["plain", "spaced", "dashed", "intl_spaced", "intl_plain"])

    if style == "plain":
        return prefix + middle + end
    elif style == "spaced":
        return f"{prefix} {middle} {end}"
    elif style == "dashed":
        return f"{prefix}-{middle}-{end}"
    elif style == "intl_spaced":
        return f"+234 {prefix[1:]} {middle} {end}"
    else:
        return f"+234{prefix[1:]}{middle}{end}"


def make_nin(rng):
    return add_check_digit(digits(rng, 10), pii_guard.verhoeff_valid)


def make_bad_nin(rng):
    nin = make_nin(rng)
    wrong_digit = rng.choice([d for d in "0123456789" if d != nin[-1]])
    return nin[:-1] + wrong_digit


def make_bvn(rng):
    return "22" + digits(rng, 9)


def make_card_number(rng):
    kind = rng.choice(["visa", "mastercard", "verve"])

    if kind == "visa":
        body = "4" + digits(rng, 14)
    elif kind == "mastercard":
        body = "5" + rng.choice("12345") + digits(rng, 13)
    else:
        body = "5061" + digits(rng, 14)

    return add_check_digit(body, pii_guard.luhn_valid)


def format_card(rng, number):
    style = rng.choice(["plain", "spaced", "dashed"])
    if style == "plain":
        return number
    separator = " " if style == "spaced" else "-"
    return separator.join(number[i:i + 4] for i in range(0, len(number), 4))


def make_possible_id(rng):
    return rng.choice("3456") + digits(rng, 10)


def make_trap(rng):
    choice = rng.randint(1, 7)

    if choice == 1:
        return f"Invoice number {rng.choice('123456789')}{digits(rng, 15)}"
    elif choice == 2:
        card = make_card_number(rng)
        wrong_digit = rng.choice([d for d in "0123456789" if d != card[-1]])
        return f"Typo in record: {card[:-1] + wrong_digit}"
    elif choice == 3:
        return f"Room {rng.randint(100, 999)} is booked from 10am to 12pm."
    elif choice == 4:
        return f"Total paid: NGN {rng.randint(10, 999)},000.00 on 13/10/2026."
    elif choice == 5:
        return f"Tracking code {rng.choice('123456789')}{digits(rng, 19)}"
    elif choice == 6:
        return "Evening shift starts at 6pm."
    else:
        return "Write to support at example dot com."


def make_text_file(rng, file_name):
    lines = ["Generated test file - FAKE DATA ONLY", ""]
    answers = []

    categories = ["Email", "Phone", "NIN", "NIN (checksum failed)", "BVN", "Card",
                  "Possible ID", "Trap", "Hard case", "Filler"]
    weights = [2, 2, 2, 1, 2, 2, 1, 4, 1, 2]

    for _ in range(ITEMS_PER_TEXT_FILE):
        category = rng.choices(categories, weights)[0]
        name = make_name(rng)

        if category == "Trap":
            lines.append(make_trap(rng))
        elif category == "Filler":
            lines.append(rng.choice(FILLER))
        elif category == "Hard case":
            hard = rng.randint(1, 3)
            if hard == 1:
                value = f"({rng.choice(PHONE_PREFIXES)}) {digits(rng, 3)} {digits(rng, 4)}"
                lines.append(f"Phone: {value}")
                answers.append((file_name, len(lines), "Phone", value))
            elif hard == 2:
                value = f"{rng.choice(PHONE_PREFIXES)}.{digits(rng, 3)}.{digits(rng, 4)}"
                lines.append(f"Alternate line {value}")
                answers.append((file_name, len(lines), "Phone", value))
            else:
                value = make_nin(rng)
                lines.append("NIN:")
                lines.append(value)
                answers.append((file_name, len(lines), "NIN", value))
        else:
            if category == "Email":
                value = make_email(rng)
            elif category == "Phone":
                value = make_phone(rng)
            elif category == "NIN":
                value = make_nin(rng)
            elif category == "NIN (checksum failed)":
                value = make_bad_nin(rng)
            elif category == "BVN":
                value = make_bvn(rng)
            elif category == "Card":
                value = format_card(rng, make_card_number(rng))
            else:
                value = make_possible_id(rng)

            template_type = "NIN" if category == "NIN (checksum failed)" else category
            template = rng.choice(TEMPLATES[template_type])
            lines.append(template.format(v=value, n=name))
            answers.append((file_name, len(lines), category, value))

    (DATA_FOLDER / file_name).write_text("\n".join(lines) + "\n", encoding="utf-8")
    return answers


def make_csv_file(rng, file_name):
    headers = ["full_name", "email", "phone", "nin", "bvn", "card_number", "notes"]
    rows = []
    answers = []

    for row_index in range(ROWS_PER_CSV_FILE):
        line = row_index + 2
        row = {"full_name": make_name(rng)}

        if rng.random() < 0.8:
            row["email"] = make_email(rng)
            answers.append((file_name, line, "Email", row["email"]))
        if rng.random() < 0.8:
            row["phone"] = make_phone(rng)
            answers.append((file_name, line, "Phone", row["phone"]))
        if rng.random() < 0.8:
            if rng.random() < 0.2:
                row["nin"] = make_bad_nin(rng)
                answers.append((file_name, line, "NIN (checksum failed)", row["nin"]))
            else:
                row["nin"] = make_nin(rng)
                answers.append((file_name, line, "NIN", row["nin"]))
        if rng.random() < 0.8:
            row["bvn"] = make_bvn(rng)
            answers.append((file_name, line, "BVN", row["bvn"]))
        if rng.random() < 0.8:
            row["card_number"] = format_card(rng, make_card_number(rng))
            answers.append((file_name, line, "Card", row["card_number"]))

        row["notes"] = rng.choice(["", "TEST DATA ONLY", "room 204", "evening shift"])
        rows.append([row.get(header, "") for header in headers])

    with open(DATA_FOLDER / file_name, "w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(headers)
        writer.writerows(rows)

    return answers


def build_dataset():
    if DATA_FOLDER.exists():
        shutil.rmtree(DATA_FOLDER)
    DATA_FOLDER.mkdir()

    rng = random.Random(SEED)
    answers = []

    for number in range(1, TEXT_FILES + 1):
        answers.extend(make_text_file(rng, f"eval_{number:02d}.txt"))
    for number in range(1, CSV_FILES + 1):
        answers.extend(make_csv_file(rng, f"eval_{number:02d}.csv"))

    return answers


def normalize(data_type, value):
    if data_type == "Email":
        return value.lower()
    return re.sub(r"\D", "", value)


def run_tool():
    findings = []

    for file_path in pii_guard.find_files(DATA_FOLDER):
        text = pii_guard.read_file(file_path)
        emails, phones, ids, cards = pii_guard.analyze_text(text)
        for data_type, value, line in emails + phones + ids + cards:
            findings.append((file_path.name, line, data_type, value))

    return findings


def as_keys(items):
    return Counter((file, line, data_type, normalize(data_type, value))
                   for file, line, data_type, value in items)


def percent(part, whole):
    if whole == 0:
        return "n/a"
    return f"{100 * part / whole:.1f}%"


def main():
    answers = build_dataset()
    findings = run_tool()

    expected = as_keys(answers)
    found = as_keys(findings)

    correct = expected & found
    missed = expected - found
    false_alarms = found - expected

    print(f"Test dataset: {TEXT_FILES + CSV_FILES} files in {DATA_FOLDER} (seed {SEED})")
    print()
    print(f"{'Data type':<24}{'Expected':>9}{'Correct':>9}{'Missed':>8}{'False':>7}{'Precision':>11}{'Recall':>8}")

    for data_type in DATA_TYPES:
        e = sum(n for key, n in expected.items() if key[2] == data_type)
        c = sum(n for key, n in correct.items() if key[2] == data_type)
        m = sum(n for key, n in missed.items() if key[2] == data_type)
        f = sum(n for key, n in false_alarms.items() if key[2] == data_type)
        print(f"{data_type:<24}{e:>9}{c:>9}{m:>8}{f:>7}{percent(c, c + f):>11}{percent(c, c + m):>8}")

    e = sum(expected.values())
    c = sum(correct.values())
    m = sum(missed.values())
    f = sum(false_alarms.values())
    print(f"{'TOTAL':<24}{e:>9}{c:>9}{m:>8}{f:>7}{percent(c, c + f):>11}{percent(c, c + m):>8}")

    print()
    print("Missed items:")
    for (file, line, data_type, value), count in sorted(missed.items()):
        print(f"  {file} line {line}: {data_type} {pii_guard.mask_value(data_type, value)}")

    print()
    print("False alarms:")
    for (file, line, data_type, value), count in sorted(false_alarms.items()):
        print(f"  {file} line {line}: {data_type} {pii_guard.mask_value(data_type, value)}")


if __name__ == "__main__":
    main()