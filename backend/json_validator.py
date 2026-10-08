# backend/json_validator.py
import json
import os
from typing import Tuple, List, Dict, Any
from scheduler import validate_combined_config_data


def validate_config_dict(data: Any) -> Tuple[bool, List[str]]:
    """Validates an in-memory dictionary using the scheduler's validation engine."""
    errors: List[str] = []

    if not isinstance(data, dict):
        return False, ["Root structure of JSON payload must be an object/dict."]

    try:
        v_results = validate_combined_config_data(data)
        if not v_results.is_valid:
            for finding in v_results.diagnostics:
                errors.append(f"[{finding.code}] {finding.path}: {finding.message}")
            return False, errors
        return True, []
    except Exception as e:
        return False, [f"Validation exception: {str(e)}"]


def validate_config_file(filepath: str) -> Tuple[bool, List[str]]:
    """Validates a JSON file on disk by path."""
    if not os.path.isfile(filepath):
        return False, [f"File not found: '{filepath}'"]

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        return False, [f"Invalid JSON syntax in '{filepath}': {str(e)}"]
    except Exception as e:
        return False, [f"Could not read file '{filepath}': {str(e)}"]

    return validate_config_dict(data)