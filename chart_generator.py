"""
chart_generator.py - Average Temperature Bar Chart Generator
=============================================================
Reads the JSON summary produced by main.py and generates a bar chart
comparing average temperatures across devices.

Usage:
    python chart_generator.py --input output/device_summary.json --output output/average_temperature.png

AI-Assisted Generation Note:
    Initial chart code was generated via AI prompt (see PROMPT_LOG.md).
    The output was reviewed for layout issues and corrected manually.
"""

import argparse
import json
import math
import os
import sys

# Graceful import of matplotlib
try:
    import matplotlib
    matplotlib.use("Agg")  # Non-interactive backend — safe for CLI usage
    import matplotlib.pyplot as plt
    import matplotlib.ticker as ticker
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_summary(filepath: str) -> list[dict]:
    """Load and validate the device summary JSON file.

    Args:
        filepath: Path to the JSON summary file.

    Returns:
        List of device summary dicts.

    Raises:
        SystemExit: On missing file, malformed JSON, or missing fields.
    """
    if not os.path.isfile(filepath):
        print(f"[ERROR] JSON file not found: {filepath}", file=sys.stderr)
        sys.exit(2)

    try:
        with open(filepath, encoding="utf-8") as fh:
            data = json.load(fh)
    except json.JSONDecodeError as exc:
        print(f"[ERROR] Malformed JSON: {exc}", file=sys.stderr)
        sys.exit(3)

    if not isinstance(data, list):
        print("[ERROR] JSON root must be a list of device records.", file=sys.stderr)
        sys.exit(3)

    return data


def extract_chart_data(data: list[dict]) -> tuple[list[str], list[float]]:
    """Extract device IDs and average temperatures from the summary list.

    Invalid or non-finite temperature values are skipped with a warning.

    Args:
        data: List of device summary dicts.

    Returns:
        Tuple of (device_ids, avg_temperatures) lists with matched indices.

    Raises:
        SystemExit: If the resulting device list is empty.
    """
    device_ids: list[str] = []
    avg_temps: list[float] = []

    for record in data:
        # Validate required fields
        if "device_id" not in record or "average_temperature" not in record:
            print(
                f"[WARNING] Record missing required fields, skipping: {record}",
                file=sys.stderr,
            )
            continue

        device_id = str(record["device_id"]).strip()
        if not device_id:
            print("[WARNING] Record has empty device_id, skipping.", file=sys.stderr)
            continue

        try:
            avg_temp = float(record["average_temperature"])
        except (ValueError, TypeError):
            print(
                f"[WARNING] Device '{device_id}' has non-numeric average_temperature. Skipping.",
                file=sys.stderr,
            )
            continue

        if math.isnan(avg_temp) or math.isinf(avg_temp):
            print(
                f"[WARNING] Device '{device_id}' has non-finite average_temperature. Skipping.",
                file=sys.stderr,
            )
            continue

        device_ids.append(device_id)
        avg_temps.append(avg_temp)

    if not device_ids:
        print("[ERROR] No valid device records to chart. Exiting.", file=sys.stderr)
        sys.exit(4)

    return device_ids, avg_temps


# ---------------------------------------------------------------------------
# Chart generation
# ---------------------------------------------------------------------------

def generate_chart(
    device_ids: list[str],
    avg_temps: list[float],
    output_path: str,
) -> None:
    """Generate and save a bar chart of average temperature by device.

    Features:
    - Meaningful title and axis labels.
    - Bar value annotations above each bar.
    - Rotated x-axis labels to prevent overlap.
    - Tight layout to prevent clipped titles.
    - A horizontal reference line at the 80 °C filter threshold.

    Args:
        device_ids: List of device ID strings (x-axis).
        avg_temps: List of average temperatures matching device_ids (y-axis).
        output_path: Destination path for the PNG file.
    """
    fig, ax = plt.subplots(figsize=(max(8, len(device_ids) * 1.4), 6))

    x_positions = range(len(device_ids))
    bar_color = "#4C72B0"
    bars = ax.bar(x_positions, avg_temps, color=bar_color, width=0.6, zorder=3)

    # --- Value labels above each bar ---
    for bar, temp in zip(bars, avg_temps):
        ax.text(
            bar.get_x() + bar.get_width() / 2.0,
            bar.get_height() + 0.5,
            f"{temp:.1f}",
            ha="center",
            va="bottom",
            fontsize=9,
            fontweight="bold",
            color="#222222",
        )

    # --- Reference line at 80 °C threshold ---
    ax.axhline(y=80.0, color="#D94040", linestyle="--", linewidth=1.2, zorder=2,
               label="Filter threshold (80.0 °C)")
    ax.legend(fontsize=9, loc="upper right")

    # --- Axes configuration ---
    ax.set_xticks(list(x_positions))
    ax.set_xticklabels(device_ids, rotation=30, ha="right", fontsize=10)
    ax.set_xlabel("Device ID", fontsize=12, labelpad=8)
    ax.set_ylabel("Average Temperature (°C)", fontsize=12, labelpad=8)
    ax.set_title(
        "Average Temperature by Device\n(Devices with avg > 80 °C excluded)",
        fontsize=13,
        fontweight="bold",
        pad=12,
    )

    # --- Grid for readability ---
    ax.yaxis.set_minor_locator(ticker.AutoMinorLocator())
    ax.grid(axis="y", which="major", linestyle="--", alpha=0.5, zorder=0)
    ax.set_ylim(0, max(avg_temps) * 1.18 + 5)

    # --- Save ---
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    plt.tight_layout()

    try:
        plt.savefig(output_path, dpi=150, bbox_inches="tight")
        print(f"[INFO] Chart saved to: {output_path}", file=sys.stderr)
    except (OSError, IOError) as exc:
        print(f"[ERROR] Failed to save chart: {exc}", file=sys.stderr)
        sys.exit(5)
    finally:
        plt.close(fig)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def build_arg_parser() -> argparse.ArgumentParser:
    """Construct and return the argument parser."""
    parser = argparse.ArgumentParser(
        prog="chart_generator.py",
        description=(
            "Chart Generator — reads a device summary JSON file and produces "
            "a bar chart of average temperature by device."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python chart_generator.py --input output/device_summary.json "
            "--output output/average_temperature.png\n"
        ),
    )
    parser.add_argument(
        "--input",
        default="output/device_summary.json",
        metavar="FILE",
        help="Path to the JSON summary file (default: output/device_summary.json).",
    )
    parser.add_argument(
        "--output",
        default="output/average_temperature.png",
        metavar="FILE",
        help="Destination path for the PNG chart (default: output/average_temperature.png).",
    )
    return parser


def main() -> None:
    """Main CLI entry point."""
    parser = build_arg_parser()
    args = parser.parse_args()

    if not MATPLOTLIB_AVAILABLE:
        print(
            "[ERROR] matplotlib is not installed. Run: pip install matplotlib",
            file=sys.stderr,
        )
        sys.exit(1)

    data = load_summary(args.input)

    if not data:
        print("[ERROR] JSON file contains an empty device list. No chart generated.", file=sys.stderr)
        sys.exit(4)

    device_ids, avg_temps = extract_chart_data(data)
    generate_chart(device_ids, avg_temps, args.output)


if __name__ == "__main__":
    main()

