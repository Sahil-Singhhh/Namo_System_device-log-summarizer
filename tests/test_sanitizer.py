"""
tests/test_sanitizer.py - Automated tests for sanitizer.py
============================================================
Covers: normal input, empty input, invalid input, negative values,
        clipping, non-finite values, and mixed/edge cases.
"""

import math
import sys
import os
import unittest

# Ensure the project root is on the path so we can import sanitizer
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sanitizer import clean_sensor_readings


class TestCleanSensorReadingsNormalInput(unittest.TestCase):
    """Tests for valid, ordinary sensor readings."""

    def test_integer_values_converted_to_float(self):
        """Integer values should be converted to float correctly."""
        result = clean_sensor_readings([10, 20, 30])
        self.assertEqual(result, [10.0, 20.0, 30.0])
        for val in result:
            self.assertIsInstance(val, float)

    def test_float_values_pass_through(self):
        """Plain float values within range should be returned unchanged."""
        result = clean_sensor_readings([0.0, 1.5, 250.0, 499.9])
        self.assertEqual(result, [0.0, 1.5, 250.0, 499.9])

    def test_string_numeric_values_converted(self):
        """String representations of numbers should be converted to float."""
        result = clean_sensor_readings(["10.5", "200", "0"])
        self.assertEqual(result, [10.5, 200.0, 0.0])

    def test_zero_is_valid(self):
        """Zero is a valid, non-negative reading and must be included."""
        result = clean_sensor_readings([0])
        self.assertEqual(result, [0.0])

    def test_exactly_500_is_preserved(self):
        """A value of exactly 500.0 should not be clipped — it equals the cap."""
        result = clean_sensor_readings([500.0])
        self.assertEqual(result, [500.0])

    def test_mixed_int_float_string(self):
        """A realistic mix of int, float, and string numbers should all convert."""
        result = clean_sensor_readings([100, 200.5, "300"])
        self.assertEqual(result, [100.0, 200.5, 300.0])


class TestCleanSensorReadingsEmptyInput(unittest.TestCase):
    """Tests for empty or all-invalid input scenarios."""

    def test_empty_list_returns_empty(self):
        """An empty input list must return an empty list."""
        result = clean_sensor_readings([])
        self.assertEqual(result, [])

    def test_all_none_returns_empty(self):
        """A list of all None values must return an empty list."""
        result = clean_sensor_readings([None, None, None])
        self.assertEqual(result, [])

    def test_all_invalid_strings_returns_empty(self):
        """A list of non-numeric strings must return an empty list."""
        result = clean_sensor_readings(["abc", "xyz", "---"])
        self.assertEqual(result, [])

    def test_entirely_invalid_mixed_returns_empty(self):
        """Mixed invalid values (None, bad strings, dicts) must return an empty list."""
        result = clean_sensor_readings([None, "bad", {}, [], object()])
        self.assertEqual(result, [])


class TestCleanSensorReadingsInvalidInput(unittest.TestCase):
    """Tests that non-convertible values are excluded."""

    def test_non_numeric_string_excluded(self):
        """Non-numeric strings must be excluded while valid values pass through."""
        result = clean_sensor_readings([10, "not_a_number", 20])
        self.assertEqual(result, [10.0, 20.0])

    def test_none_excluded(self):
        """None must be excluded from the output."""
        result = clean_sensor_readings([None, 50.0, None])
        self.assertEqual(result, [50.0])

    def test_dict_excluded(self):
        """A dict value cannot be converted and must be excluded."""
        result = clean_sensor_readings([{"value": 10}, 15.0])
        self.assertEqual(result, [15.0])

    def test_list_value_excluded(self):
        """A nested list value must be excluded."""
        result = clean_sensor_readings([[1, 2, 3], 25.0])
        self.assertEqual(result, [25.0])

    def test_boolean_true_converted_to_1(self):
        """bool is a subclass of int: True → 1.0, which is valid."""
        result = clean_sensor_readings([True])
        self.assertEqual(result, [1.0])

    def test_boolean_false_converted_to_0(self):
        """bool is a subclass of int: False → 0.0, which is valid."""
        result = clean_sensor_readings([False])
        self.assertEqual(result, [0.0])


class TestCleanSensorReadingsNegativeValues(unittest.TestCase):
    """Tests that negative values are excluded."""

    def test_negative_float_excluded(self):
        """Negative float values must be excluded."""
        result = clean_sensor_readings([-1.0, 10.0])
        self.assertEqual(result, [10.0])

    def test_negative_integer_excluded(self):
        """Negative integer values must be excluded."""
        result = clean_sensor_readings([-100, 50])
        self.assertEqual(result, [50.0])

    def test_negative_string_excluded(self):
        """Negative values expressed as strings must also be excluded."""
        result = clean_sensor_readings(["-5.0", "25.0"])
        self.assertEqual(result, [25.0])

    def test_all_negative_returns_empty(self):
        """A list of only negative values must return an empty list."""
        result = clean_sensor_readings([-10, -20, -0.001])
        self.assertEqual(result, [])


class TestCleanSensorReadingsClipping(unittest.TestCase):
    """Tests that values above 500.0 are clipped to 500.0."""

    def test_value_above_500_clipped(self):
        """Values strictly greater than 500.0 must be clipped to 500.0."""
        result = clean_sensor_readings([600.0])
        self.assertEqual(result, [500.0])

    def test_value_just_above_500_clipped(self):
        """A value of 500.0001 must be clipped to exactly 500.0."""
        result = clean_sensor_readings([500.0001])
        self.assertEqual(result, [500.0])

    def test_value_exactly_500_not_clipped(self):
        """A value of exactly 500.0 must NOT be clipped."""
        result = clean_sensor_readings([500.0])
        self.assertEqual(result, [500.0])

    def test_multiple_values_clipped(self):
        """Multiple values above 500.0 should all clip to 500.0."""
        result = clean_sensor_readings([1000, 750, 501])
        self.assertEqual(result, [500.0, 500.0, 500.0])

    def test_clipping_preserves_lower_values(self):
        """Clipping large values should not affect values within range."""
        result = clean_sensor_readings([100.0, 1000.0, 200.0])
        self.assertEqual(result, [100.0, 500.0, 200.0])


class TestCleanSensorReadingsNonFiniteValues(unittest.TestCase):
    """Tests that NaN and infinite values are excluded."""

    def test_nan_excluded(self):
        """float('nan') must be excluded."""
        result = clean_sensor_readings([float("nan"), 42.0])
        self.assertEqual(result, [42.0])

    def test_positive_infinity_excluded(self):
        """float('inf') must be excluded."""
        result = clean_sensor_readings([float("inf"), 10.0])
        self.assertEqual(result, [10.0])

    def test_negative_infinity_excluded(self):
        """float('-inf') must be excluded (negative AND infinite)."""
        result = clean_sensor_readings([float("-inf"), 10.0])
        self.assertEqual(result, [10.0])

    def test_math_nan_excluded(self):
        """math.nan must be excluded."""
        result = clean_sensor_readings([math.nan, 5.0])
        self.assertEqual(result, [5.0])

    def test_math_inf_excluded(self):
        """math.inf must be excluded."""
        result = clean_sensor_readings([math.inf, 5.0])
        self.assertEqual(result, [5.0])

    def test_string_nan_excluded(self):
        """The string 'nan' converts to float('nan') and must be excluded."""
        result = clean_sensor_readings(["nan", 20.0])
        self.assertEqual(result, [20.0])

    def test_string_inf_excluded(self):
        """The string 'inf' converts to float('inf') and must be excluded."""
        result = clean_sensor_readings(["inf", 20.0])
        self.assertEqual(result, [20.0])

    def test_all_nan_returns_empty(self):
        """A list of only NaN values must return an empty list."""
        result = clean_sensor_readings([float("nan"), float("nan")])
        self.assertEqual(result, [])


class TestCleanSensorReadingsReturnType(unittest.TestCase):
    """Tests that the return type is always a list of floats."""

    def test_return_type_is_list(self):
        """Return value must always be a list."""
        result = clean_sensor_readings([1, 2, 3])
        self.assertIsInstance(result, list)

    def test_elements_are_floats(self):
        """All elements in the returned list must be floats."""
        result = clean_sensor_readings([1, 2, 3])
        for item in result:
            self.assertIsInstance(item, float)

    def test_empty_return_is_list(self):
        """Empty result must be a list, not None or another type."""
        result = clean_sensor_readings([])
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)

