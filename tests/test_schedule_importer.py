"""Tests for importing exported schedule JSON."""

import json
import sys
from types import ModuleType, SimpleNamespace

import pytest

from backend import Schedule_importer


def test_import_schedules_returns_exported_schedule_array(monkeypatch, tmp_path):
    """Verify imports preserve structured assignments and legacy CSV assignments."""
    schedules = [
        [{
            "course": "CS101",
            "faculty": "F1",
            "room": "A1",
            "times": [{"day": "MON", "start": "09:00", "duration": 90}],
        }],
        {
            "schedule_id": 2,
            "courses": [
                "CS201,F2,R2,,TUE 10:00-11:30",
            ],
        },
    ]
    path = tmp_path / "schedules.json"
    path.write_text(json.dumps(schedules), encoding="utf-8")
    monkeypatch.setattr(Schedule_importer, "_choose_import_path", lambda: str(path))

    assert Schedule_importer.import_schedules() == schedules


@pytest.mark.parametrize(
    "filename, contents",
    [
        ("schedules.csv", '[{"course_id": "CS101"}]'),
        ("schedules.json", "{invalid json"),
        ("schedules.json", '{"schedule_id": 1}'),
        ("schedules.json", '[{"schedule_id": 1}, "not a schedule"]'),
        ("schedules.json", '[{"schedule_id": 1, "courses": ["CS101"]}]'),
        (
            "schedules.json",
            '[{"schedule_id": 1, "courses": [{"course": "CS101", '
            '"times": [{"day": "MON", "start": "25:00", "duration": 0}]}]}]',
        ),
    ],
)
def test_import_schedules_rejects_invalid_files(
    monkeypatch, tmp_path, filename, contents
):
    """Verify unsupported files, malformed JSON, and invalid schedules are rejected."""
    path = tmp_path / filename
    path.write_text(contents, encoding="utf-8")
    monkeypatch.setattr(Schedule_importer, "_choose_import_path", lambda: str(path))

    assert Schedule_importer.import_schedules() == Schedule_importer.INVALID_FILE_MESSAGE


def test_import_schedules_reports_cancelled_selection(monkeypatch):
    monkeypatch.setattr(Schedule_importer, "_choose_import_path", lambda: "")

    assert Schedule_importer.import_schedules() == (
        "Import cancelled: no file was selected."
    )


@pytest.mark.parametrize(
    "value, expected",
    [
        (0, True),
        (1439, True),
        (-1, False),
        (1440, False),
        (True, False),
        (1.5, False),
        ("00:00", True),
        ("23:59", True),
        ("24:00", False),
        ("12:60", False),
        ("9:00", True),
        (None, False),
    ],
)
def test_valid_start_accepts_only_minutes_or_valid_clock_strings(value, expected):
    assert Schedule_importer._valid_start(value) is expected


@pytest.mark.parametrize(
    "meeting, expected",
    [
        ({"day": "MON", "start": "09:00", "duration": 60}, True),
        ({"day": 0, "start_time": 0, "duration": 1}, True),
        ({"day": 7, "start": 1439, "duration": 30}, True),
        (None, False),
        ({"day": "", "start": "09:00", "duration": 60}, False),
        ({"day": 8, "start": 0, "duration": 60}, False),
        ({"day": True, "start": 0, "duration": 60}, False),
        ({"day": "MON", "start": 0, "duration": True}, False),
        ({"day": "MON", "start": 0, "duration": 0}, False),
        ({"day": "MON", "duration": 60}, False),
    ],
)
def test_valid_meeting_checks_day_start_and_duration(meeting, expected):
    assert Schedule_importer._valid_meeting(meeting) is expected


def test_valid_legacy_assignment_checks_csv_shape_and_handles_parser_error(monkeypatch):
    assert Schedule_importer._valid_legacy_assignment(
        "CS101,F1,R1,,MON 09:00-10:00"
    )
    assert not Schedule_importer._valid_legacy_assignment(1)
    assert not Schedule_importer._valid_legacy_assignment("CS101,F1,R1")
    assert not Schedule_importer._valid_legacy_assignment(",F1,R1,,MON")

    def fail_csv_reader(_stream):
        raise Schedule_importer.csv.Error("parse failure")

    monkeypatch.setattr(Schedule_importer.csv, "reader", fail_csv_reader)
    assert not Schedule_importer._valid_legacy_assignment("CS101,F1,R1,,MON")


def test_valid_assignment_accepts_supported_course_identifiers_and_meeting_keys():
    meeting = {"day": "MON", "start": "09:00", "duration": 60}
    assert Schedule_importer._valid_assignment(
        {"course": "CS101", "times": [meeting]}
    )
    assert Schedule_importer._valid_assignment(
        {"course_str": "CS102", "meetings": [meeting]}
    )
    assert Schedule_importer._valid_assignment(
        {"course_id": "CS103", "times": [meeting]}
    )
    assert Schedule_importer._valid_assignment(
        {"section": "CS104", "times": [meeting]}
    )
    assert not Schedule_importer._valid_assignment(None)
    assert not Schedule_importer._valid_assignment({"course": "", "times": [meeting]})
    assert not Schedule_importer._valid_assignment(
        {"course": "CS105", "times": []}
    )
    assert not Schedule_importer._valid_assignment(
        {"course": "CS106", "times": [meeting, {"day": "BAD"}]}
    )


def test_valid_schedule_checks_ids_and_supports_legacy_assignment_arrays():
    valid_course = {
        "course_id": "CS101",
        "times": [{"day": "MON", "start": "09:00", "duration": 60}],
    }
    assert Schedule_importer._valid_schedule([])
    assert Schedule_importer._valid_schedule([valid_course])
    assert Schedule_importer._valid_schedule(
        {"schedule_id": 1, "courses": [valid_course]}
    )
    assert Schedule_importer._valid_schedule(
        {"schedule_id": "fall", "assignments": [valid_course]}
    )
    for bad_id in (None, True, 1.5, "", "   "):
        assert not Schedule_importer._valid_schedule(
            {"schedule_id": bad_id, "courses": []}
        )
    assert not Schedule_importer._valid_schedule("not a schedule")


def test_load_schedules_reports_unsupported_and_malformed_data():
    with pytest.raises(ValueError, match="Unsupported schedule file"):
        Schedule_importer.load_schedules(b"[]", "schedules.csv")
    with pytest.raises(ValueError, match="Malformed schedule JSON"):
        Schedule_importer.load_schedules(b"{broken", "schedules.json")
    with pytest.raises(ValueError, match="Malformed schedule JSON"):
        Schedule_importer.load_schedules(b"\xff", "schedules.json")
    with pytest.raises(ValueError, match="Invalid schedule data"):
        Schedule_importer.load_schedules(b"{}", "schedules.json")


def test_choose_import_path_configures_dialog_and_destroys_window(monkeypatch):
    window = SimpleNamespace(withdraw=lambda: None, destroyed=False)

    def destroy():
        window.destroyed = True

    window.destroy = destroy
    dialog_arguments = {}
    tkinter_module = ModuleType("tkinter")
    tkinter_module.Tk = lambda: window
    tkinter_module.filedialog = SimpleNamespace(
        askopenfilename=lambda **kwargs: dialog_arguments.update(kwargs) or "picked.json"
    )
    monkeypatch.setitem(sys.modules, "tkinter", tkinter_module)

    result = Schedule_importer._choose_import_path()

    assert result == "picked.json"
    assert dialog_arguments["title"] == "Import schedules"
    assert window.destroyed is True


def test_import_schedules_handles_unreadable_selected_file(monkeypatch, tmp_path):
    missing = tmp_path / "missing.json"
    monkeypatch.setattr(Schedule_importer, "_choose_import_path", lambda: str(missing))

    assert Schedule_importer.import_schedules() == Schedule_importer.INVALID_FILE_MESSAGE
