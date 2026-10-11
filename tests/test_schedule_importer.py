"""Tests for importing exported schedule JSON."""

import json

import pytest

from backend import Schedule_importer


def test_import_schedules_returns_exported_schedule_array(monkeypatch, tmp_path):
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
    path = tmp_path / filename
    path.write_text(contents, encoding="utf-8")
    monkeypatch.setattr(Schedule_importer, "_choose_import_path", lambda: str(path))

    assert Schedule_importer.import_schedules() == Schedule_importer.INVALID_FILE_MESSAGE


def test_import_schedules_reports_cancelled_selection(monkeypatch):
    monkeypatch.setattr(Schedule_importer, "_choose_import_path", lambda: "")

    assert Schedule_importer.import_schedules() == (
        "Import cancelled: no file was selected."
    )
