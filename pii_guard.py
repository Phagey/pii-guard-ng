import re

EMAIL_PATTERN = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")


def find_emails(text):
    return EMAIL_PATTERN.findall(text)


def main():
    file_path = "samples/sample1.txt"

    with open(file_path, "r", encoding="utf-8") as file:
        text = file.read()

    emails = find_emails(text)

    print(f"Scanning: {file_path}")
    print(f"Emails found: {len(emails)}")
    for email in emails:
        print(f"  - {email}")


if __name__ == "__main__":
    main()