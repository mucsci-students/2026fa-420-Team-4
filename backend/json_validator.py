import json
import os
from typing import Tuple, List, Dict, Any

# Required schema structure and expected types
EXPECTED_SCHEMA = {
    "config": dict,
    "time_slot_config": dict,
    "limit": int,
    "optimizer_flags": list,
}

EXPECTED_CONFIG_KEYS = {
    "rooms": list,
    "labs": list,
    "courses": list,
    "faculty": list,
}

EXPECTED_TIME_SLOT_KEYS = {
    "times": dict,
    "classes": list,
}

EXPECTED_WEEKDAYS = ["MON", "TUE", "WED", "THU", "FRI"]

#Validates the inputted json file matches the expected schema
def validate_config_file(filepath: str) -> Tuple[bool, List[str]]:
    errors: List[str] = []

    #checks if file exists
    if not os.path.isfile(filepath):
        return False, [f"File not found: '{filepath}'"]

    #parse through
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        return False, [f"Invalid JSON syntax in '{filepath}': {str(e)}"]
    except Exception as e:
        return False, [f"Could not read file '{filepath}': {str(e)}"]

    if not isinstance(data, dict):
        return False, ["Root structure of JSON file must be an object/dict."]

    #checks keys
    for key, expected_type in EXPECTED_SCHEMA.items():
        if key not in data:
            errors.append(f"Missing top-level key: '{key}'")
        elif not isinstance(data[key], expected_type):
            errors.append(
                f"Type mismatch for key '{key}': expected {expected_type.__name__}, got {type(data[key]).__name__}"
            )


    if errors:
        return False, errors

    config = data["config"]
    for key, expected_type in EXPECTED_CONFIG_KEYS.items():
        if key not in config:
            errors.append(f"Missing key in 'config': '{key}'")
        elif not isinstance(config[key], expected_type):
            errors.append(
                f"Type mismatch for 'config.{key}': expected {expected_type.__name__}, got {type(config[key]).__name__}"
            )

   #checks inside time slot config
    time_slot_config = data["time_slot_config"]
    for key, expected_type in EXPECTED_TIME_SLOT_KEYS.items():
        if key not in time_slot_config:
            errors.append(f"Missing key in 'time_slot_config': '{key}'")
        elif not isinstance(time_slot_config[key], expected_type):
            errors.append(
                f"Type mismatch for 'time_slot_config.{key}': expected {expected_type.__name__}, got {type(time_slot_config[key]).__name__}"
            )

    if "times" in time_slot_config and isinstance(time_slot_config["times"], dict):
        times = time_slot_config["times"]
        for day in EXPECTED_WEEKDAYS:
            if day not in times:
                errors.append(f"Missing weekday key in 'time_slot_config.times': '{day}'")
            elif not isinstance(times[day], list):
                errors.append(
                    f"Type mismatch for 'time_slot_config.times.{day}': expected list, got {type(times[day]).__name__}"
                )

    is_valid = len(errors) == 0
    return is_valid, errors