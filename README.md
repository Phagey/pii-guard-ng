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
| Nigerian phone number | 0803 000 0001, +234 805 000 0002, (0803) 000 0001, 0803.000.0001 | Pattern match with network prefix rules |
| NIN | 11 digits labelled "NIN" or "National Identification" | Context words + Verhoeff checksum |
| BVN | 11 digits labelled "BVN" or "Bank Verification" | Context words |
| Bank card number | 13 to 19 digits, including Verve-style 19-digit cards | Pattern match + Luhn checksum |
| Possible ID | Unlabelled 11-digit numbers | Flagged for review |

Key design choices:

- **Context-aware detection:** NIN and BVN are both 11 digits, so the tool
  reads the label on the same line, the column name in CSV files, or a
  label-only line directly above the number.
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

## Testing and Evaluation

### Automated tests

35 automated tests cover every detector, both checksums, masking, risk
levels, CSV handling, folder scanning, line numbers, and an end-to-end test
that runs the scanner from the command line.

```powershell
python -m unittest discover -s tests -v
```

### Accuracy

`evaluate.py` generates a reproducible fake dataset (25 files, 409 sensitive
items, seed 42) containing normal cases, traps that must not be flagged,
and deliberately hard cases, then compares the tool's findings against the
known answers.

```powershell
python evaluate.py
```

| Version | Precision | Recall | Missed | False alarms |
|---|---|---|---|---|
| First version | 98.8% | 97.6% | 10 | 5 |
| After fixes | 100% | 100% | 0 | 0 |

All 10 misses in the first version came from two formats: phone numbers
written with brackets or dots, and NIN labels on the line above the
number. Both were fixed. Note that 100% applies to this generated dataset
only; real files contain formats not represented here, so real-world
accuracy is expected to be lower.

### Performance

`benchmark.py` measures scanning speed on 2,500 small files and on single
files of 0.25 to 2 MB.

```powershell
python benchmark.py
```

Benchmarking revealed that scan time grew quadratically with file size
(each doubling of size took about four times longer), because line numbers
were recalculated from the start of the file for every finding. Line
positions are now indexed once per file and looked up with binary search.

| File size | Before | After | Speed-up |
|---|---|---|---|
| 0.25 MB | 1.21 s | 0.10 s | 12x |
| 0.5 MB | 2.72 s | 0.15 s | 18x |
| 1.0 MB | 10.57 s | 0.31 s | 34x |
| 2.0 MB | 39.91 s | 0.78 s | 51x |

Measured on a Windows laptop. The number of items found was identical
before and after the fix.

## Project Structure

```
pii-guard-ng/
├── pii_guard.py        Main scanner
├── evaluate.py         Accuracy evaluation on a generated dataset
├── benchmark.py        Performance benchmark
├── samples/            Hand-written test files (fake data only)
├── tests/              Automated tests
├── docs/
│   ├── research.md     Review of existing tools
│   └── design.md       Design and decisions
├── reports/            Scan reports (created when run, not uploaded)
├── README.md
└── LICENSE
```

## Test Data

All test data in this project is **fake**:

- Email addresses use the reserved `example.com`, `example.org` and
  `example.net` domains.
- Phone and ID numbers are made-up values. NINs are generated to pass the
  Verhoeff checksum, plus deliberate failures.
- Card numbers are publicly documented payment test numbers or generated
  numbers that pass the Luhn check.
- Test files include "trap" cases (look-alike numbers and words such as
  "evening") to test for false alarms.

No real personal information is used anywhere in this project.

## Roadmap

Weeks 1 and 2 (done):

- [x] Email, Nigerian phone, NIN and BVN detection
- [x] Bank card detection with Luhn checksum validation
- [x] NIN validation with Verhoeff checksum
- [x] Folder scanning, including CSV files
- [x] Masked output, risk levels and masked CSV report with line numbers

Week 3 (done):

- [x] 35 automated tests, including an end-to-end test
- [x] Accuracy evaluation on a 409-item generated dataset
- [x] Support for bracket and dot phone formats, and labels on the line above
- [x] Performance benchmark and fix for slow scanning of large files

Possible future work:

- [ ] Support Word, Excel and PDF files
- [ ] Test on real-world-style documents with more varied formats
- [ ] Add more Nigerian identifiers (for example TIN, passport numbers)

## License

MIT License. See [LICENSE](LICENSE).