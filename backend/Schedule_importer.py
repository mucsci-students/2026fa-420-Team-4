"""Import generated schedules from a JSON file selected by the user."""

import json
from pathlib import Path


INVALID_FILE_MESSAGE = (
    "Invalid file. Select a valid JSON schedule export containing an array "
    "of schedule objects."
)


def _choose_import_path() -> str:
    """Open a file dialog and return the selected source, if any."""
    import tkinter as tk
    from tkinter import filedialog

    window = tk.Tk()
    window.withdraw()
    try:
        return filedialog.askopenfilename(
            title="Import schedules",
            filetypes=(("JSON files", "*.json"),),
        )
    finally:
        window.destroy()


def import_schedules() -> list[object] | str:
    """Return schedules from a selected JSON export, or an error message.

    The file must have a ``.json`` extension and contain an outer JSON array
    with each schedule represented by an object or array, as produced by
    :func:`backend.ScheduleExporter.export_schedules`.
    """
    selected_path = _choose_import_path()
    if not selected_path:
        return "Import cancelled: no file was selected."

    path = Path(selected_path)
    if path.suffix.lower() != ".json":
        return INVALID_FILE_MESSAGE

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return INVALID_FILE_MESSAGE

    if not isinstance(data, list) or not all(
        isinstance(schedule, (dict, list)) for schedule in data
    ):
        return INVALID_FILE_MESSAGE

    return data
