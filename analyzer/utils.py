import re
from pathlib import Path


def shorten_string(string, max_length=60):
    if len(string) <= max_length:
        extra_space = max_length - len(string)
        appended_spaces = extra_space * " "
        return string + appended_spaces
    part_length = (max_length - 3) // 2
    return string[:part_length] + "..." + string[-part_length:]


def str_to_int(string):
    matches = re.findall(r"\d+", str(string))
    integer = int(matches[0])
    return integer


def is_valid_data(data):
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
    marker = ".git"
    current_path = Path(__file__).resolve()
    for parent in current_path.parents:
        if (parent / marker).exists():
            return parent
    print("ERROR: Failed to find root folder of project")
    exit(1)
