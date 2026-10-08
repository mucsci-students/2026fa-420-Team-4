import csv
import json
from dataclasses import dataclass

import pytest

import Schedule_exporter


@dataclass
class Course:
    course_id: str
    room: str


def test_export_schedules_as_json(monkeypatch, tmp_path):
    destination = tmp_path / "schedule.json"
    monkeypatch.setattr(
        Schedule_exporter, "_choose_export_path", lambda: str(destination)
    )

    result = Schedule_exporter.export_schedules([[Course("CS101", "A1")]])

    assert result == destination
    assert json.loads(destination.read_text(encoding="utf-8")) == [
        [{"course_id": "CS101", "room": "A1"}]
    ]


def test_export_schedules_as_csv_keeps_schedule_numbers(monkeypatch, tmp_path):
    destination = tmp_path / "schedule.csv"
    monkeypatch.setattr(
        Schedule_exporter, "_choose_export_path", lambda: str(destination)
    )

    result = Schedule_exporter.export_schedules(
        [[Course("CS101", "A1"), Course("CS102", "A2")], [Course("CS201", "B1")]]
    )

    assert result == destination
    with destination.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    assert rows == [
        {
            "schedule_number": "1",
            "item_number": "1",
            "course_id": "CS101",
            "room": "A1",
        },
        {
            "schedule_number": "1",
            "item_number": "2",
            "course_id": "CS102",
            "room": "A2",
        },
        {
            "schedule_number": "2",
            "item_number": "1",
            "course_id": "CS201",
            "room": "B1",
        },
    ]


def test_export_schedules_returns_none_if_save_dialog_is_cancelled(monkeypatch):
    monkeypatch.setattr(Schedule_exporter, "_choose_export_path", lambda: "")

    assert Schedule_exporter.export_schedules([]) is None


def test_export_schedules_rejects_non_sequence():
    with pytest.raises(TypeError, match="sequence of schedule objects"):
        Schedule_exporter.export_schedules(None)


def test_export_schedules_rejects_unknown_file_extension(monkeypatch, tmp_path):
    destination = tmp_path / "schedule.txt"
    monkeypatch.setattr(
        Schedule_exporter, "_choose_export_path", lambda: str(destination)
    )

    with pytest.raises(ValueError, match=".json or .csv"):
        Schedule_exporter.export_schedules([])
