"""
sanitizer.py - Sensor Data Sanitization Module
================================================
Provides the clean_sensor_readings() function which sanitizes a list of raw
sensor values according to the following rules:
  - Convert convertible values to float.
  - Exclude None, NaN, and infinite values.
  - Exclude values that cannot be converted to float.
  - Exclude negative values.
  - Clip values above 500.0 to 500.0.
  - Handle empty lists and entirely invalid lists gracefully.
"""

import math
from typing import Any


def clean_sensor_readings(values: list[Any]) -> list[float]:
    """Sanitize a list of raw sensor readings and return valid floats.

    Processing steps applied in order for each element:
      1. Skip None values.
      2. Attempt conversion to float; skip on failure.
      3. Skip NaN and infinite (±∞) values.
      4. Skip negative values (< 0.0).
      5. Clip values strictly above 500.0 down to 500.0.

    Args:
        values: A list of arbitrary values (int, float, str, None, etc.).

    Returns:
        A list of cleaned float values. May be empty if all inputs were invalid.
    """
    if not values:
        return []

    cleaned: list[float] = []

    for raw in values:
        # Step 1: Exclude None
        if raw is None:
            continue

        # Step 2: Attempt float conversion
        try:
            value = float(raw)
        except (ValueError, TypeError):
            continue

        # Step 3: Exclude NaN and infinite values
        if math.isnan(value) or math.isinf(value):
            continue

        # Step 4: Exclude negative values
        if value < 0.0:
            continue

        # Step 5: Clip values above 500.0
        if value > 500.0:
            value = 500.0

        cleaned.append(value)

    return cleaned

