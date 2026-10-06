# pii-guard-ng

A lightweight, offline data loss prevention (DLP) tool that scans files for
sensitive personal data, including Nigerian National Identification Numbers
(NIN), Bank Verification Numbers (BVN) and Nigerian phone numbers.

Built as part of the CyberFox Society Cybersecurity Research & Development
Internship (Privacy & Data Security track).

## The Problem

Organizations often store files such as spreadsheets, exports and documents
that contain personal information without realizing it. If these files are
shared or leaked, it causes a privacy breach. Existing detection tools are
often paid, cloud-based or require programming knowledge, and most do not
recognize Nigerian data types out of the box. See
[docs/research.md](docs/research.md) for a comparison of existing tools.

## Features

| Data type | Example | How it is detected and validated |
|---|---|---|
| Email address | name@example.com | Pattern match |
| Nigerian phone number | 0803 000 0001, +234 805 000 0002 | Pattern match with network prefix rules |
| NIN | 11 digits after "NIN" or "National Identification" | Context words + Verhoeff checksum |
| BVN | 11 digits after "BVN" or "Bank Verification" | Context words |
| Bank card number | 13 to 19 digits, including Verve-style 19-digit cards | Pattern match + Luhn checksum |
| Possible ID | Unlabelled 11-digit numbers | Flagged for review |

Key design choices:

- **Context-aware detection:** NIN and BVN are both 11 digits, so the tool
  reads the label on the same line (or the column name in CSV files).
- **Checksum validation:** the Luhn check filters out random numbers that
  look like cards, and the Verhoeff check flags mistyped NINs.
- **Masked output:** sensitive values are never shown or saved in full
  (for example `*******8904`).
- **Risk levels:** each file is rated High, Medium, Low or Clean.
- **Fully offline:** uses only Python's standard library. No data leaves
  your computer.

See [docs/design.md](docs/design.md) for full design details.

## Requirements

- Python 3.8 or newer (tested on Python 3.14)
- No additional packages required

## How to Run (Windows)

Set up once:

```powershell
git clone https://github.com/Phagey/pii-guard-ng.git
cd pii-guard-ng
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Scan the included sample files:

```powershell
python pii_guard.py
```

Scan any folder of your own (all .txt and .csv files inside, including
sub-folders):

```powershell
python pii_guard.py "C:\path\to\your\folder"
```

## Example Output

```
Scanning: samples\sample3.txt
  Risk level: HIGH
  Emails found: 0
  Phone numbers found: 1
    - Phone: *******0004 (line 6)
  ID numbers found: 8
    - NIN: *******8904 (line 4)
    - BVN: *******0001 (line 5)
    - NIN: *******0004 (line 9)
    - BVN: *******0003 (line 10)
    - NIN: *******0002 (line 11)
    - NIN (checksum failed): *******8901 (line 12)
    - Possible ID: *******0009 (line 14)
    - Possible ID: *******0007 (line 15)
  Card numbers found: 0
```

At the end of each scan, a summary shows how many files fall into each
risk level, and a masked report is saved to `reports/report.csv` with the
columns `file, line, data_type, masked_value, file_risk`. The `reports`
folder is excluded from Git so scan results are never uploaded.

## Risk Levels

| Level | Rule |
|---|---|
| High | Any NIN, BVN or valid card number |
| Medium | Phone numbers or Possible IDs |
| Low | Email addresses only |
| Clean | Nothing found |

## Project Structure

```
pii-guard-ng/
├── pii_guard.py        Main scanner
├── samples/            Test files (fake data only)
├── docs/
│   ├── research.md     Review of existing tools
│   └── design.md       Design and decisions
├── reports/            Scan reports (created when run, not uploaded)
├── README.md
└── LICENSE
```

## Test Data

All files in the `samples` folder contain **fake data only**:

- Email addresses use the reserved `example.com`, `example.org` and
  `example.net` domains.
- Phone and ID numbers are made-up patterned values. NINs were generated to
  pass the Verhoeff checksum, plus one deliberate failure.
- Card numbers are publicly documented payment test numbers, plus one
  made-up Verve-style number.
- Each file includes "trap" cases (look-alike numbers and words such as
  "evening") to test for false positives.

No real personal information is used anywhere in this project.

## Roadmap

Week 1 and 2 (done):

- [x] Email detection
- [x] Nigerian phone number detection
- [x] Context-aware NIN and BVN detection
- [x] Bank card detection with Luhn checksum validation
- [x] NIN validation with Verhoeff checksum
- [x] Scan a whole folder, including CSV files
- [x] Mask sensitive values in all output
- [x] Risk level per file and scan summary
- [x] Masked CSV report with line numbers

Week 3 (planned):

- [ ] Automated tests for every detector and validator
- [ ] Measure accuracy (false positives and missed items) on a larger test set
- [ ] Performance check on larger folders

## License

MIT License. See [LICENSE](LICENSE).