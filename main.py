"""
main.py - Device Log Summarizer CLI
=====================================
Reads a CSV file of device telemetry data, aggregates per-device statistics,
filters out devices whose average temperature exceeds 80.0 °C, and exports a
clean JSON summary file. A formatted table is printed to the terminal.

Usage:
    python main.py --input device_telemetry.csv --output output/device_summary.json

CSV columns expected:
    device_id   - Unique device identifier (non-empty string)
    status      - One of ACTIVE | WARNING | ERROR (case-insensitive)
    temperature - Numeric float value representing sensor reading in °C
"""

import argparse
import csv
import json
import math
import os
import sys
from collections import defaultdict
from typing import Optional


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

REQUIRED_COLUMNS = {"device_id", "status", "temperature"}
TEMPERATURE_FILTER_THRESHOLD = 80.0  # Devices with avg temp > this are excluded
VALID_STATUSES = {"ACTIVE", "WARNING", "ERROR"}


# ---------------------------------------------------------------------------
# Data helpers
# ---------------------------------------------------------------------------

def normalize_device_id(raw: str) -> Optional[str]:
    """Strip whitespace from device_id; return None if empty after stripping."""
    normalized = raw.strip().upper()
    return normalized if normalized else None


def normalize_status(raw: str) -> Optional[str]:
    """Normalize status to uppercase; return None if not a recognized status."""
    normalized = raw.strip().upper()
    return normalized if normalized in VALID_STATUSES else None


def parse_temperature(raw: str) -> Optional[float]:
    """Parse temperature string to float; return None if invalid, NaN, or Inf."""
    try:
        value = float(raw.strip())
    except (ValueError, TypeError):
        return None

    if math.isnan(value) or math.isinf(value):
        return None

    return value


# ---------------------------------------------------------------------------
# CSV ingestion
# ---------------------------------------------------------------------------

def load_csv(filepath: str) -> list[dict]:
    """Load and validate rows from a CSV file.

    Args:
        filepath: Path to the input CSV file.

    Returns:
        List of raw row dicts from csv.DictReader.

    Raises:
        SystemExit: On missing file or CSV parse errors.
    """
    if not os.path.isfile(filepath):
        print(f"[ERROR] Input file not found: {filepath}", file=sys.stderr)
        sys.exit(2)

    try:
        with open(filepath, newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)

            # Validate required columns
            if reader.fieldnames is None:
                print("[ERROR] CSV file is empty or has no header row.", file=sys.stderr)
                sys.exit(3)

            actual_columns = {col.strip() for col in reader.fieldnames}
            missing = REQUIRED_COLUMNS - actual_columns
            if missing:
                print(
                    f"[ERROR] CSV is missing required columns: {', '.join(sorted(missing))}",
                    file=sys.stderr,
                )
                sys.exit(3)

            rows = list(reader)
    except csv.Error as exc:
        print(f"[ERROR] Malformed CSV data: {exc}", file=sys.stderr)
        sys.exit(3)

    return rows


# ---------------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------------

def aggregate_records(rows: list[dict]) -> dict[str, dict]:
    """Process CSV rows and aggregate per-device statistics.

    Invalid records are skipped with a warning printed to stderr.

    Args:
        rows: Raw row dicts from the CSV reader.

    Returns:
        Dict mapping normalized device_id → aggregation dict with keys:
            valid_count  (int)
            temperatures (list[float])
            error_count  (int)
    """
    aggregation: dict[str, dict] = defaultdict(
        lambda: {"valid_count": 0, "temperatures": [], "error_count": 0}
    )

    for line_num, row in enumerate(rows, start=2):  # start=2 because header is line 1
        # --- device_id ---
        raw_device = row.get("device_id", "") or ""
        device_id = normalize_device_id(raw_device)
        if device_id is None:
            print(
                f"[WARNING] Line {line_num}: Skipping record with empty device_id.",
                file=sys.stderr,
            )
            continue

        # --- status ---
        raw_status = row.get("status", "") or ""
        status = normalize_status(raw_status)
        if status is None:
            print(
                f"[WARNING] Line {line_num}: Device '{device_id}' has invalid status "
                f"'{raw_status.strip()}'. Skipping record.",
                file=sys.stderr,
            )
            continue

        # --- temperature ---
        raw_temp = row.get("temperature", "") or ""
        temperature = parse_temperature(raw_temp)
        if temperature is None:
            print(
                f"[WARNING] Line {line_num}: Device '{device_id}' has invalid temperature "
                f"'{raw_temp.strip()}'. Skipping record.",
                file=sys.stderr,
            )
            continue

        # All fields valid — accumulate
        aggregation[device_id]["valid_count"] += 1
        aggregation[device_id]["temperatures"].append(temperature)
        if status == "ERROR":
            aggregation[device_id]["error_count"] += 1

    return dict(aggregation)


# ---------------------------------------------------------------------------
# Summary building & filtering
# ---------------------------------------------------------------------------

def build_summary(aggregation: dict[str, dict]) -> list[dict]:
    """Convert raw aggregation into final summary records and apply temperature filter.

    Devices with average temperature strictly greater than TEMPERATURE_FILTER_THRESHOLD
    are excluded. Devices with average exactly equal to the threshold are preserved.

    Args:
        aggregation: Output of aggregate_records().

    Returns:
        Sorted list of device summary dicts ready for JSON export.
    """
    summary = []

    for device_id, data in aggregation.items():
        temps = data["temperatures"]
        if not temps:
            continue

        avg_temp = sum(temps) / len(temps)

        # Safety guard — should never occur after parse_temperature(), but be explicit
        if math.isnan(avg_temp) or math.isinf(avg_temp):
            print(
                f"[WARNING] Device '{device_id}' produced a non-finite average temperature. "
                "Excluding from output.",
                file=sys.stderr,
            )
            continue

        # Filter: exclude devices whose avg temp is STRICTLY greater than threshold
        if avg_temp > TEMPERATURE_FILTER_THRESHOLD:
            print(
                f"[INFO] Device '{device_id}' excluded: avg temperature "
                f"{avg_temp:.2f} °C > {TEMPERATURE_FILTER_THRESHOLD} °C threshold.",
                file=sys.stderr,
            )
            continue

        summary.append(
            {
                "device_id": device_id,
                "valid_record_count": data["valid_count"],
                "average_temperature": round(avg_temp, 4),
                "error_count": data["error_count"],
            }
        )

    # Sort by device_id for deterministic, reproducible output
    summary.sort(key=lambda r: r["device_id"])
    return summary


# ---------------------------------------------------------------------------
# JSON export
# ---------------------------------------------------------------------------

def export_json(summary: list[dict], output_path: str) -> None:
    """Write summary list to a JSON file, creating parent directories as needed.

    Args:
        summary: List of device summary dicts.
        output_path: Destination file path.

    Raises:
        SystemExit: On file I/O errors.
    """
    try:
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as fh:
            json.dump(summary, fh, indent=2, allow_nan=False)
        print(f"[INFO] JSON summary written to: {output_path}", file=sys.stderr)
    except (OSError, IOError) as exc:
        print(f"[ERROR] Failed to write JSON output: {exc}", file=sys.stderr)
        sys.exit(4)
    except ValueError as exc:
        # allow_nan=False raises ValueError if NaN/Inf slip through
        print(f"[ERROR] JSON serialization error: {exc}", file=sys.stderr)
        sys.exit(4)


# ---------------------------------------------------------------------------
# Terminal table
# ---------------------------------------------------------------------------

def print_summary_table(summary: list[dict]) -> None:
    """Print a formatted table of device summary statistics to stdout.

    Args:
        summary: List of device summary dicts.
    """
    if not summary:
        print("\nNo devices passed the temperature filter. Nothing to display.\n")
        return

    col_widths = {
        "device_id": max(len("Device ID"), max(len(r["device_id"]) for r in summary)),
        "valid_record_count": max(len("Valid Records"), 13),
        "average_temperature": max(len("Avg Temp (C)"), 13),
        "error_count": max(len("Error Count"), 11),
    }

    header = (
        f"{'Device ID':<{col_widths['device_id']}}  "
        f"{'Valid Records':>{col_widths['valid_record_count']}}  "
        f"{'Avg Temp (C)':>{col_widths['average_temperature']}}  "
        f"{'Error Count':>{col_widths['error_count']}}"
    )
    separator = "-" * len(header)

    print("\n" + separator)
    print("  DEVICE TELEMETRY SUMMARY")
    print(separator)
    print(header)
    print(separator)

    for record in summary:
        print(
            f"{record['device_id']:<{col_widths['device_id']}}  "
            f"{record['valid_record_count']:>{col_widths['valid_record_count']}}  "
            f"{record['average_temperature']:>{col_widths['average_temperature']}.4f}  "
            f"{record['error_count']:>{col_widths['error_count']}}"
        )

    print(separator + "\n")
    print(f"  Total devices (after filter): {len(summary)}")
    print(f"  Temperature filter threshold: avg > {TEMPERATURE_FILTER_THRESHOLD} C -> excluded")
    print(separator + "\n")


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def build_arg_parser() -> argparse.ArgumentParser:
    """Construct and return the argument parser."""
    parser = argparse.ArgumentParser(
        prog="main.py",
        description=(
            "Device Log Summarizer CLI — reads device telemetry CSV data, "
            "aggregates per-device statistics, filters high-temperature devices, "
            "and exports a JSON summary."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python main.py --input device_telemetry.csv --output output/device_summary.json\n"
        ),
    )
    parser.add_argument(
        "--input",
        required=True,
        metavar="FILE",
        help="Path to the input CSV file containing device telemetry data.",
    )
    parser.add_argument(
        "--output",
        required=True,
        metavar="FILE",
        help="Path for the output JSON summary file.",
    )
    return parser


def main() -> None:
    """Main CLI entry point."""
    parser = build_arg_parser()
    args = parser.parse_args()

    # 1. Load CSV
    rows = load_csv(args.input)

    if not rows:
        print("[WARNING] CSV file contains no data rows.", file=sys.stderr)
        export_json([], args.output)
        print_summary_table([])
        sys.exit(0)

    # 2. Aggregate
    aggregation = aggregate_records(rows)

    if not aggregation:
        print("[WARNING] No valid records found after processing.", file=sys.stderr)
        export_json([], args.output)
        print_summary_table([])
        sys.exit(0)

    # 3. Build summary (apply temperature filter)
    summary = build_summary(aggregation)

    # 4. Export JSON
    export_json(summary, args.output)

    # 5. Print terminal table
    print_summary_table(summary)


if __name__ == "__main__":
    main()
