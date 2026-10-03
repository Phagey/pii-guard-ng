# pii-guard-ng

A lightweight, offline tool that detects sensitive personal data in files,
including Nigerian National Identification Numbers (NIN), Bank Verification
Numbers (BVN) and Nigerian phone numbers.

Built as part of the CyberFox Society Cybersecurity Research & Development
Internship (Privacy & Data Security track).

## The Problem

Organizations often store files such as spreadsheets, exports and documents
that contain personal information without realizing it. If these files are
shared or leaked, it causes a privacy breach. Existing detection tools are
often paid, cloud-based or require programming knowledge, and most do not
recognize Nigerian data types out of the box. See
[docs/research.md](docs/research.md) for a comparison of existing tools.

## Current Features

| Data type | Example format | How it is detected |
|---|---|---|
| Email address | name@example.com | Pattern match |
| Nigerian phone number | 0803 000 0001, +234 805 000 0002 | Pattern match with network prefix rules |
| NIN | 11 digits after "NIN" or "National Identification" | Pattern match + context words |
| BVN | 11 digits after "BVN" or "Bank Verification" | Pattern match + context words |
| Possible ID | Unlabelled 11-digit numbers | Flagged for review |

Key design choices:

- **Context-aware detection:** NIN and BVN are both 11 digits, so the tool
  reads the words on the same line to tell them apart.
- **Trap resistance:** numbers inside longer numbers, and words like
  "evening" (which contains "nin"), are not mistaken for sensitive data.
- **Fully offline:** uses only Python's standard library. No data leaves
  your computer.

## Requirements

- Python 3 (tested on Python 3.14)
- No additional packages required

## How to Run (Windows)

```powershell
git clone https://github.com/Phagey/pii-guard-ng.git
cd pii-guard-ng
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python pii_guard.py
```

## Test Data

All files in the `samples` folder contain **fake data only**. Email
addresses use the reserved `example.com`, `example.org` and `example.net`
domains, and phone and ID numbers are made-up patterned values. No real
personal information is used anywhere in this project.

## Roadmap

- [x] Email detection
- [x] Nigerian phone number detection
- [x] Context-aware NIN and BVN detection
- [ ] Bank card detection with Luhn checksum validation
- [ ] NIN validation with Verhoeff checksum
- [ ] Scan a whole folder, including CSV files
- [ ] Mask sensitive values in output
- [ ] Risk level per file (Low / Medium / High)
- [ ] Save results to a report file

## License

MIT License. See [LICENSE](LICENSE).