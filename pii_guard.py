import re

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

CARD_PATTERN = re.compile(r"(?<!\d)(?:\d[ -]?){12,18}\d(?!\d)")


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

        if NIN_KEYWORDS.search(nearby_text):
            results.append(("NIN", number))
        elif BVN_KEYWORDS.search(nearby_text):
            results.append(("BVN", number))
        elif NG_PHONE_PATTERN.fullmatch(number):
            continue
        else:
            results.append(("Possible ID", number))

    return results


def scan_file(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        text = file.read()

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
    files_to_scan = [
        "samples/sample1.txt",
        "samples/sample2.txt",
        "samples/sample3.txt",
        "samples/sample4.txt",
    ]

    for file_path in files_to_scan:
        scan_file(file_path)


if __name__ == "__main__":
    main()