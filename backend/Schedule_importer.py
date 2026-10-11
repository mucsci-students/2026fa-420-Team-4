"""Import generated schedules from a JSON file selected by the user."""

import csv
import io
import json
from pathlib import Path
from typing import Any


INVALID_FILE_MESSAGE = (
    "Invalid schedule data. Select a JSON export containing an array of "
    "schedules with course assignments and meeting data."
)


def _valid_start(value: Any) -> bool:
    """Accept minutes since midnight or an hour:minute string within one day."""
    if isinstance(value, int) and not isinstance(value, bool):
        return 0 <= value < 24 * 60
    if isinstance(value, str):
        parts = value.split(":")
        return (
            len(parts) == 2
            and parts[0].isdigit()
            and parts[1].isdigit()
            and 0 <= int(parts[0]) < 24
            and 0 <= int(parts[1]) < 60
        )
    return False


def _valid_meeting(meeting: Any) -> bool:
    """Check that a meeting has a day, valid start, and positive minute duration."""
    if not isinstance(meeting, dict):
        return False
    day = meeting.get("day")
    valid_day = (
        isinstance(day, str) and bool(day.strip())
    ) or (
        isinstance(day, int)
        and not isinstance(day, bool)
        and 0 <= day <= 7
    )
    duration = meeting.get("duration")
    valid_duration = (
        isinstance(duration, int)
        and not isinstance(duration, bool)
        and duration > 0
    )
    return (
        valid_day
        and _valid_start(meeting.get("start", meeting.get("start_time")))
        and valid_duration
    )


def _valid_legacy_assignment(assignment: Any) -> bool:
    """Accept one five-field CSV row with nonempty course and meeting fields."""
    if not isinstance(assignment, str):
        return False
    try:
        rows = list(csv.reader(io.StringIO(assignment)))
    except csv.Error:
        return False
    return (
        len(rows) == 1
        and len(rows[0]) == 5
        and bool(rows[0][0].strip())
        and bool(rows[0][4].strip())
    )


def _valid_assignment(assignment: Any) -> bool:
    """Validate a legacy CSV assignment or a course object with meeting data."""
    if _valid_legacy_assignment(assignment):
        return True
    if not isinstance(assignment, dict):
        return False

    course = (
        assignment.get("course")
        or assignment.get("course_str")
        or assignment.get("course_id")
        or assignment.get("section")
    )
    if not isinstance(course, str) or not course.strip():
        return False

    meetings = assignment.get("times", assignment.get("meetings"))
    if not isinstance(meetings, list) or not meetings:
        return False
    return all(_valid_meeting(meeting) for meeting in meetings)


def _valid_schedule(schedule: Any) -> bool:
    """Validate an assignment list or an identified schedule containing one."""
    if isinstance(schedule, list):
        return all(_valid_assignment(assignment) for assignment in schedule)
    if not isinstance(schedule, dict):
        return False

    schedule_id = schedule.get("schedule_id")
    if schedule_id is None or (
        isinstance(schedule_id, bool)
        or not isinstance(schedule_id, (str, int))
        or (isinstance(schedule_id, str) and not schedule_id.strip())
    ):
        return False

    assignments = schedule.get("courses", schedule.get("assignments"))
    return isinstance(assignments, list) and all(
        _valid_assignment(assignment) for assignment in assignments
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


def load_schedules(content: bytes, filename: str) -> list[object]:
    """Parse and validate an application schedule export before it is loaded."""
    if Path(filename).suffix.lower() != ".json":
        raise ValueError("Unsupported schedule file. Select a .json schedule export.")

    try:
        data = json.loads(content.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("Malformed schedule JSON. Select a valid JSON file.") from error

    if not isinstance(data, list) or not all(_valid_schedule(s) for s in data):
        raise ValueError(INVALID_FILE_MESSAGE)

    return data


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
    try:
        return load_schedules(path.read_bytes(), path.name)
    except (OSError, ValueError):
        return INVALID_FILE_MESSAGE
