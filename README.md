# Device Log Summarizer CLI

A Python command-line tool for **sensor data sanitization**, **device telemetry aggregation**, **JSON export**, and **temperature visualization**. Built as part of a Software Engineering Intern Technical Assessment.

---

## Table of Contents

- [Project Overview](#project-overview)
- [Features](#features)
- [Directory Structure](#directory-structure)
- [Installation](#installation)
- [Commands](#commands)
  - [Run the CLI](#run-the-cli)
  - [Run Tests](#run-tests)
  - [Generate the Chart](#generate-the-chart)
- [Input CSV Format](#input-csv-format)
- [Output JSON Format](#output-json-format)
- [Sanitization Rules](#sanitization-rules)
- [Aggregation and Filtering Logic](#aggregation-and-filtering-logic)
- [Error Handling](#error-handling)
- [Example Terminal Output](#example-terminal-output)
- [Generated Sample Artifacts](#generated-sample-artifacts)
- [Assumptions and Limitations](#assumptions-and-limitations)

---

## Project Overview

The **Device Log Summarizer CLI** reads raw device telemetry from a CSV file, cleans and validates the data, aggregates per-device statistics, filters out hot devices (average temperature > 80 °C), exports a structured JSON summary, and generates a bar chart of average temperatures.

The project is organized into three focused modules:

| Module | Purpose |
|---|---|
| `sanitizer.py` | Sensor data sanitization library |
| `main.py` | CSV ingestion, aggregation, filtering, JSON export, terminal table |
| `chart_generator.py` | Bar chart generation from JSON summary |

---

## Features

- **Sensor Data Sanitization** — converts, validates, clips, and filters raw readings
- **CSV Ingestion** — uses Python's built-in `csv` module, no third-party parsing
- **Argument Parsing** — `argparse`-based CLI with `--help` support
- **Required-Column Validation** — exits with a clear error if columns are missing
- **Robust Error Handling** — missing files, malformed CSV, invalid fields, empty datasets
- **Record Normalization** — device IDs and statuses are normalized to uppercase
- **Invalid Record Skipping** — warnings printed per skipped record; program continues
- **Per-Device Aggregation** — valid count, average temperature, error status count
- **Temperature Threshold Filtering** — devices with avg > 80.0 °C excluded; avg = 80.0 preserved
- **JSON Export** — clean, indented JSON; NaN/Infinity explicitly blocked
- **Terminal Summary Table** — formatted, human-readable table
- **Bar Chart Generation** — matplotlib chart with value labels, reference line, tight layout
- **36 Automated Unit Tests** — covering all sanitizer branches
- **Reproducible Output** — sorted by device_id for deterministic results

---

## Directory Structure

```
device-log-summarizer/
├── main.py                      # Section 2: CSV processing, aggregation, JSON export
├── sanitizer.py                 # Section 1: Sensor data sanitization module
├── chart_generator.py           # Section 3: Bar chart generation
├── device_telemetry.csv         # Synthetic sample CSV dataset (see Assumptions)
├── output/
│   ├── device_summary.json      # Generated JSON summary (committed sample output)
│   └── average_temperature.png  # Generated bar chart PNG (committed sample output)
├── tests/
│   └── test_sanitizer.py        # 36 unit tests for sanitizer.py
├── PROMPT_LOG.md                # AI collaboration documentation
├── README.md                    # This file
├── requirements.txt             # Python dependencies
└── .gitignore                   # Excludes venvs, caches, secrets
```

---

## Installation

### Prerequisites

- Python 3.8 or later
- pip

### Steps

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/device-log-summarizer-cli.git
cd device-log-summarizer-cli

# (Optional) Create and activate a virtual environment
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

> **Note:** `sanitizer.py` and `main.py` use only the Python standard library.  
> `chart_generator.py` requires **matplotlib** (listed in `requirements.txt`).

---

## Commands

### Run the CLI

Process the sample CSV and export a JSON summary:

```bash
python main.py --input device_telemetry.csv --output output/device_summary.json
```

View CLI help:

```bash
python main.py --help
```

### Run Tests

Run all 36 unit tests with verbose output:

```bash
python -m unittest discover -s tests -v
```

Expected result: `Ran 36 tests in ~0.00s — OK`

### Generate the Chart

Generate the average-temperature bar chart from the JSON summary:

```bash
python chart_generator.py --input output/device_summary.json --output output/average_temperature.png
```

View chart generator help:

```bash
python chart_generator.py --help
```

Custom paths are supported:

```bash
python chart_generator.py --input path/to/summary.json --output path/to/chart.png
```

---

## Input CSV Format

The input CSV must contain a header row with **exactly** these three columns (additional columns are ignored):

| Column | Type | Description |
|---|---|---|
| `device_id` | string | Unique device identifier. Must be non-empty after stripping whitespace. |
| `status` | string | Device status. Must be one of `ACTIVE`, `WARNING`, `ERROR` (case-insensitive). |
| `temperature` | float | Sensor temperature reading in °C. Must be a parseable, finite number. |

**Example:**

```csv
device_id,status,temperature
DEV001,ACTIVE,72.5
DEV002,ERROR,60.1
DEV003,WARNING,88.0
```

Records that fail any field validation are **skipped** with a warning; processing continues with remaining records.

---

## Output JSON Format

The output is a JSON array of device summary objects, sorted by `device_id`:

```json
[
  {
    "device_id": "DEV001",
    "valid_record_count": 3,
    "average_temperature": 71.8333,
    "error_count": 0
  },
  {
    "device_id": "DEV006",
    "valid_record_count": 2,
    "average_temperature": 80.0,
    "error_count": 1
  }
]
```

| Field | Type | Description |
|---|---|---|
| `device_id` | string | Normalized (uppercase) device identifier |
| `valid_record_count` | integer | Number of valid records included in aggregation |
| `average_temperature` | float | Average of valid temperature readings (rounded to 4 decimal places) |
| `error_count` | integer | Count of records with status `ERROR` |

NaN and Infinity values are explicitly blocked from the JSON output.

---

## Sanitization Rules

Implemented in `sanitizer.clean_sensor_readings(values)`:

| Rule | Behavior |
|---|---|
| `None` | Excluded |
| Non-convertible types | Excluded (strings like `"abc"`, dicts, lists) |
| NaN (`float('nan')`, `"nan"`) | Excluded |
| Infinite values (`float('inf')`, `"-inf"`, `"inf"`) | Excluded |
| Negative values (`< 0.0`) | Excluded |
| Values `> 500.0` | Clipped to `500.0` |
| Values `<= 500.0` and `>= 0.0` | Converted to `float` and returned |
| Empty input list | Returns `[]` |
| All-invalid input | Returns `[]` |

---

## Aggregation and Filtering Logic

1. **Load CSV** — read with `csv.DictReader`, validate header columns.
2. **Normalize** — strip whitespace from all fields; uppercase `device_id` and `status`.
3. **Validate per record:**
   - `device_id` must be non-empty after stripping.
   - `status` must be one of `ACTIVE`, `WARNING`, `ERROR` after normalization.
   - `temperature` must be parseable as a finite float.
   - Invalid records are skipped with a `[WARNING]` message.
4. **Aggregate per device:**
   - Count valid records.
   - Accumulate temperature values.
   - Count `ERROR` status records.
5. **Compute averages** — arithmetic mean of all valid temperatures per device.
6. **Apply filter:**
   - Devices with average temperature **strictly greater than 80.0 °C** → excluded (`[INFO]` message).
   - Devices with average temperature **exactly equal to 80.0 °C** → **preserved**.
7. **Sort** results by `device_id` for reproducible output.
8. **Export** JSON and print terminal table.

---

## Error Handling

| Scenario | Behavior | Exit Code |
|---|---|---|
| Input CSV file not found | `[ERROR]` message to stderr | `2` |
| CSV missing required columns | `[ERROR]` message listing missing columns | `3` |
| Malformed CSV (parse error) | `[ERROR]` message with exception detail | `3` |
| Empty CSV (header only) | `[WARNING]`, exports `[]` JSON | `0` |
| No valid records after processing | `[WARNING]`, exports `[]` JSON | `0` |
| Invalid `device_id` (empty) | `[WARNING]` per record, skipped | — |
| Invalid `status` | `[WARNING]` per record, skipped | — |
| Invalid or missing `temperature` | `[WARNING]` per record, skipped | — |
| Non-finite average temperature | `[WARNING]`, device excluded | — |
| Device filtered by temperature threshold | `[INFO]` per device excluded | — |
| JSON write failure | `[ERROR]` message | `4` |
| Chart: JSON not found | `[ERROR]` message | `2` |
| Chart: Malformed JSON | `[ERROR]` message | `3` |
| Chart: Empty device list | `[ERROR]` message | `4` |
| Chart: matplotlib not installed | `[ERROR]` message with install command | `1` |
| Chart: save failure | `[ERROR]` message | `5` |

---

## Example Terminal Output

```
[WARNING] Line 17: Device 'DEV001' has invalid temperature 'invalid_temp'. Skipping record.
[WARNING] Line 18: Device 'DEV002' has invalid temperature ''. Skipping record.
[WARNING] Line 19: Skipping record with empty device_id.
[INFO] Device 'DEV003' excluded: avg temperature 87.83 C > 80.0 C threshold.
[INFO] JSON summary written to: output/device_summary.json

----------------------------------------------------
  DEVICE TELEMETRY SUMMARY
----------------------------------------------------
Device ID  Valid Records   Avg Temp (C)  Error Count
----------------------------------------------------
DEV001                 3        71.8333            0
DEV002                 3        58.0000            1
DEV004                 3        80.0000            0
DEV005                 3        71.5000            1
DEV006                 2        80.0000            1
----------------------------------------------------

  Total devices (after filter): 5
  Temperature filter threshold: avg > 80.0 C -> excluded
----------------------------------------------------
```

---

## Generated Sample Artifacts

The `output/` directory contains pre-generated artifacts from the sample dataset:

- **`output/device_summary.json`** — JSON summary of 5 devices (DEV003 excluded)
- **`output/average_temperature.png`** — Bar chart of average temperatures

These artifacts are committed to the repository so an evaluator can inspect them immediately without running the pipeline.

---

## Assumptions and Limitations

1. **Synthetic CSV dataset** — `device_telemetry.csv` is a synthetic dataset generated for this assessment. It intentionally includes:
   - Devices with `ACTIVE`, `WARNING`, and `ERROR` statuses.
   - `DEV003` with average temperature **87.83 °C** → filtered out (avg > 80.0).
   - `DEV004` and `DEV006` with average temperature **exactly 80.0 °C** → preserved.
   - One record with an invalid temperature string (`"invalid_temp"`).
   - One record with an empty temperature field.
   - One record with an empty `device_id`.
   - Records with mixed-case statuses (`active`, `Active`, ` error `) to test normalization.

2. **Temperature units** — assumed to be degrees Celsius. No unit conversion is performed.

3. **Duplicate device IDs** — records for the same `device_id` are aggregated together, which is the intended behavior.

4. **CSV encoding** — UTF-8 encoding is assumed. Files with other encodings may need conversion.

5. **Filter boundary** — the threshold of 80.0 °C uses strict inequality (`> 80.0`). Exactly 80.0 is preserved, per specification.

6. **Floating-point precision** — average temperatures are rounded to 4 decimal places in JSON output. Internal computation uses full float precision.

7. **matplotlib cache warning** — on some Windows systems, matplotlib may print a warning about a non-writable config directory. This does not affect functionality.

8. **Python version** — tested on Python 3.14.2. Compatible with Python 3.8+.

