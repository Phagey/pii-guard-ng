# Research: Existing Sensitive Data Detection Tools

This document reviews existing tools for detecting sensitive personal data,
checks how well they cover Nigerian data types (NIN, BVN, +234 phone numbers),
and identifies the gap that pii-guard-ng aims to address.

Research conducted: October 2026.

---

## 1. Microsoft Presidio

- **What it is:** An open-source Python toolkit, originally developed by
  Microsoft, for detecting and anonymizing personally identifiable
  information (PII) in text.
- **How it works:** Combines pattern matching (regular expressions), context
  words, checksum validation and natural language processing (spaCy named
  entity recognition).
- **Cost and setup:** Free. Requires Python, installing the Presidio packages
  and downloading a spaCy language model. It is a developer toolkit that must
  be integrated into code, not a ready-to-run scanner.
- **Nigerian coverage:** Partial. Release 2.2.362 (March 2026) added a
  Nigerian NIN recognizer (NG_NIN) with Verhoeff checksum validation, and a
  Nigerian vehicle registration recognizer. No BVN recognizer is listed.
  Nigerian phone detection requires configuring the phone recognizer in code.
- **Limitations:** Requires programming knowledge to use; heavier setup
  because of the NLP model; no BVN support; Nigerian phone detection is not
  available out of the box.
- **Sources:**
  - https://github.com/data-privacy-stack/presidio/blob/main/docs/supported_entities.md
  - https://github.com/data-privacy-stack/presidio/blob/main/CHANGELOG.md

## 2. Amazon Macie

- **What it is:** A fully managed AWS cloud service that discovers sensitive
  data stored in Amazon S3.
- **How it works:** Uses machine learning and pattern matching through
  "managed data identifiers". Each identifier lists the countries it is
  designed for. Users can also write custom regex-based identifiers.
- **Cost and setup:** Paid, usage-based AWS pricing. Requires an AWS account
  and the data to be stored in Amazon S3.
- **Nigerian coverage:** No Nigeria-specific managed identifiers were found
  in the documentation reviewed. Country-specific identifiers focus on regions
  such as the US, UK, EU countries, India and parts of Latin America. Nigerian
  formats would require custom identifiers.
- **Limitations:** Only scans data in Amazon S3; ongoing cost; sensitive data
  must be stored in the cloud; Nigerian IDs require manual configuration.
- **Sources:**
  - https://docs.aws.amazon.com/macie/latest/user/mdis-reference-quick.html
  - https://docs.aws.amazon.com/macie/latest/user/mdis-reference-pii.html

## 3. Google Cloud Sensitive Data Protection (formerly Cloud DLP)

- **What it is:** A Google Cloud service for inspecting, classifying and
  de-identifying sensitive data in text, images and cloud storage.
- **How it works:** Uses built-in "infoType detectors" (for example email
  address, phone number, credit card number and country-specific ID numbers),
  plus custom infoTypes defined with regular expressions or word lists.
- **Cost and setup:** Paid, usage-based. Requires a Google Cloud project,
  enabling the API and writing code or configuration to run scans.
- **Nigerian coverage:** No Nigeria-specific infoType was identified in the
  reference reviewed. Nigerian formats would require custom infoTypes.
- **Limitations:** Cloud-based, so data must be sent to Google for
  inspection; ongoing cost; technical setup required.
- **Sources:**
  - https://cloud.google.com/dlp/docs/infotypes-reference
  - https://cloud.google.com/sensitive-data-protection/docs/concepts-infotypes

## 4. Gitleaks

- **What it is:** An open-source command-line tool that scans Git
  repositories and files for leaked secrets such as API keys, passwords and
  access tokens.
- **How it works:** Uses a set of regular-expression rules, with optional
  entropy (randomness) checks, to spot secret-like strings.
- **Cost and setup:** Free and open source; runs locally as a single program.
- **Nigerian coverage:** Not applicable. It is designed for credentials and
  secrets, not personal data such as NIN, BVN or phone numbers.
- **Limitations:** Different purpose: it does not detect personal
  information. It is included here because it shows the value of a simple,
  free, offline scanning tool.
- **Sources:**
  - https://github.com/gitleaks/gitleaks

---

## Comparison Summary

| Tool | Free | Runs offline | No coding needed | Nigerian NIN | Nigerian BVN | Nigerian phone |
|---|---|---|---|---|---|---|
| Microsoft Presidio | Yes | Yes | No | Yes (since 2026) | No | Needs configuration |
| Amazon Macie | No | No | Partly | Custom only | Custom only | Custom only |
| Google Cloud SDP | No | No | No | Custom only | Custom only | Custom only |
| Gitleaks | Yes | Yes | Yes | No (not its purpose) | No | No |
| **pii-guard-ng** | **Yes** | **Yes** | **Yes** | **Yes** | **Yes** | **Yes** |

---

## Gap and Opportunity

The major cloud tools (Amazon Macie and Google Cloud Sensitive Data
Protection) are powerful but paid, cloud-based and not built for Nigerian
data types, so a small Nigerian organization would need to upload sensitive
files to a cloud provider and write custom rules. Microsoft Presidio is free
and has recently added Nigerian NIN support, but it is a developer toolkit
with a heavier setup, and it does not cover BVN or Nigerian phone numbers out
of the box.

pii-guard-ng addresses this gap with a lightweight, free tool that runs fully
offline, needs no cloud account or machine-learning model, and detects
Nigerian NIN, BVN and phone numbers together with common data types such as
email addresses. It uses context words on the same line to tell NIN and BVN
apart, since both are 11-digit numbers.

## Ideas Adopted From This Research

- **Context keywords:** Presidio and Macie both use nearby keywords to
  improve accuracy. This supports pii-guard-ng's approach of reading the label
  before an 11-digit number.
- **Checksum validation:** Presidio validates NINs with the Verhoeff checksum.
  pii-guard-ng will add Verhoeff validation for NINs and Luhn validation for
  bank card numbers in Week 2 to reduce false positives.