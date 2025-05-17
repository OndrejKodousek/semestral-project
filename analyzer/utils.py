"""
@file utils.py
@brief Utility functions for string manipulation, data validation, and project management.

This module contains helper functions used throughout the project for tasks like
string formatting, data validation, and project path management.
"""

import re
from pathlib import Path


def shorten_string(string, max_length=60):
    """
    @brief Shortens a string to a specified maximum length.

    If the string is shorter than the maximum length, it will be padded with spaces.
    If longer, it will be truncated with ellipsis in the middle.

    @param string The input string to be shortened.
    @param max_length Maximum length of the output string (default: 60).
    @return The shortened or padded string.
    """
    if len(string) <= max_length:
        extra_space = max_length - len(string)
        appended_spaces = extra_space * " "
        return string + appended_spaces
    part_length = (max_length - 3) // 2
    return string[:part_length] + "..." + string[-part_length:]


def str_to_int(string):
    """
    @brief Extracts the first integer from a string.

    @param string The input string to extract an integer from.
    @return The first integer found in the string.
    """
    matches = re.findall(r"\d+", str(string))
    integer = int(matches[0])
    return integer


def is_valid_data(data):
    """
    @brief Validates stock data structure.

    Ensures that the data dictionary contains all required keys and that values are valid.
    Checks for presence of required keys, validates that stock and ticker fields are not empty,
    and verifies that prediction values are between -1.0 and 1.0 and confidence values are
    between 0.0 and 1.0.

    @param data The data dictionary to validate.
    @return True if the data is valid, False otherwise.
    """
    try:
        required_keys = [
            "stock",
            "ticker",
            "summary",
            "prediction_1_day",
            "prediction_2_day",
            "prediction_3_day",
            "prediction_4_day",
            "prediction_5_day",
            "prediction_6_day",
            "prediction_7_day",
            "confidence_1_day",
            "confidence_2_day",
            "confidence_3_day",
            "confidence_4_day",
            "confidence_5_day",
            "confidence_6_day",
            "confidence_7_day",
        ]

        for key in required_keys:
            if key not in data:
                return False

        invalid_strings = {
            "",
            "none",
            "unknown",
            "null",
            "n/a",
            "error",
            "not available",
        }
        if str(data["stock"]).strip().lower() in invalid_strings:
            return False
        if str(data["ticker"]).strip().lower() in invalid_strings:
            return False

        for i in range(1, 8):
            prediction_key = f"prediction_{i}_day"
            try:
                prediction_value = float(data[prediction_key])
            except (ValueError, TypeError):
                return False

            if not (-1.0 <= prediction_value <= 1.0):
                return False

            confidence_key = f"confidence_{i}_day"
            try:
                confidence_value = float(data[confidence_key])
            except (ValueError, TypeError):
                return False

            if not (0.00 <= confidence_value <= 1.00):
                return False

        return True

    except Exception as e:
        print(f"Validation error: {e}")
        return False


def get_project_root():
    """
    @brief Finds the root directory of the project.

    Searches for a .git directory in parent directories to identify the project root.

    @return Path to the project root directory.
    @throws SystemExit if the root directory cannot be found.
    """
    marker = ".git"
    current_path = Path(__file__).resolve()
    for parent in current_path.parents:
        if (parent / marker).exists():
            return parent
    print("ERROR: Failed to find root folder of project")
    exit(1)
