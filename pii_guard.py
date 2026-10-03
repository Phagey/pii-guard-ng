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


def find_emails(text):
    return EMAIL_PATTERN.findall(text)


def find_phones(text):
    return NG_PHONE_PATTERN.findall(text)


def scan_file(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        text = file.read()

    emails = find_emails(text)
    phones = find_phones(text)

    print(f"Scanning: {file_path}")

    print(f"  Emails found: {len(emails)}")
    for email in emails:
        print(f"    - {email}")

    print(f"  Phone numbers found: {len(phones)}")
    for phone in phones:
        print(f"    - {phone}")

    print()


def main():
    files_to_scan = ["samples/sample1.txt", "samples/sample2.txt"]

    for file_path in files_to_scan:
        scan_file(file_path)


if __name__ == "__main__":
    main()