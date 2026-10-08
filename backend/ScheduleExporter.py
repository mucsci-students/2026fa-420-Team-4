"""Export generated schedules as JSON or CSV."""

import csv
import json
from collections.abc import Mapping, Sequence
from dataclasses import asdict, is_dataclass
from pathlib import Path


def _choose_export_path() -> str:
    """Open a save dialog and return the selected destination, if any."""
    import tkinter as tk
    from tkinter import filedialog

    window = tk.Tk()
    # Keep the save dialog visible without showing an extra empty Tk window.
    window.withdraw()
    try:
        return filedialog.asksaveasfilename(
            title="Export schedules",
            defaultextension=".json",
            filetypes=(("JSON files", "*.json"), ("CSV files", "*.csv")),
        )
    finally:
        window.destroy()


def _to_serializable(value):
    """Convert scheduler model values and nested collections to plain data."""
    # Walk nested schedule data so JSON and CSV receive only basic Python values.
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Mapping):
        return {str(key): _to_serializable(item) for key, item in value.items()}
    if is_dataclass(value) and not isinstance(value, type):
        return _to_serializable(asdict(value))
    if isinstance(value, (list, tuple)):
        return [_to_serializable(item) for item in value]

    for method_name in ("model_dump", "to_dict"):
        converter = getattr(value, method_name, None)
        if callable(converter):
            return _to_serializable(converter())

    attributes = getattr(value, "__dict__", None)
    if attributes is not None:
        public_attributes = {
            key: item for key, item in attributes.items() if not key.startswith("_")
        }
        return _to_serializable(public_attributes)

    raise TypeError(
        f"Schedule value of type {type(value).__name__} cannot be converted"
    )


def _csv_rows(schedules):
    """Create one CSV record per schedule entry and retain its schedule number."""
    rows = []
    for schedule_number, schedule in enumerate(schedules, start=1):
        if isinstance(schedule, list):
            # CSV has no nested-list structure, so write each schedule item as a row.
            if not schedule:
                rows.append({"schedule_number": schedule_number})
            for item_number, item in enumerate(schedule, start=1):
                item_data = item if isinstance(item, dict) else {"value": item}
                rows.append(
                    {
                        "schedule_number": schedule_number,
                        "item_number": item_number,
                        **item_data,
                    }
                )
        else:
            rows.append({"schedule_number": schedule_number, **schedule})
    return rows


def _csv_value(value):
    """Encode dictionaries and lists as JSON for a CSV cell; return other values unchanged."""
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return value


def export_schedules(schedules: Sequence[object]) -> Path | None:
    """Export an array of schedule objects after the user chooses a destination.

    The destination extension selects JSON or CSV. Returning ``None`` means the
    user cancelled the save dialog.
    """
    if isinstance(schedules, (str, bytes)) or not isinstance(schedules, Sequence):
        raise TypeError("schedules must be a sequence of schedule objects")

    schedule_data = [_to_serializable(schedule) for schedule in schedules]
    selected_path = _choose_export_path()
    if not selected_path:
        return None

    path = Path(selected_path)
    file_format = path.suffix.lower()
    if file_format == ".json":
        # JSON keeps each generated schedule together in the outer array.
        path.write_text(
            json.dumps(schedule_data, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    elif file_format == ".csv":
        rows = _csv_rows(schedule_data)
        # Use the union of all row keys so schedules with different fields fit.
        fieldnames = list(dict.fromkeys(key for row in rows for key in row))
        with path.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=fieldnames)
            if fieldnames:
                writer.writeheader()
                writer.writerows(
                    {key: _csv_value(value) for key, value in row.items()}
                    for row in rows
                )
    else:
        raise ValueError("Choose a destination ending in .json or .csv")

    return path