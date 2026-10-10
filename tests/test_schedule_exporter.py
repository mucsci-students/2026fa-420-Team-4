import csv
import io

import pytest

from backend import ScheduleExporter


def test_schedules_to_csv_serializes_generated_schedule_rows():
    schedules = [
        {
            "schedule_id": 1,
            "courses": ["CS101, Room A1, Monday 09:00"],
        },
        {
            "schedule_id": 2,
            "courses": ["CS201, Room B2, Tuesday 10:00"],
        },
    ]

    rows = list(csv.DictReader(io.StringIO(ScheduleExporter.schedules_to_csv(schedules))))

    assert rows == [
        {
            "schedule_number": "1",
            "schedule_id": "1",
            "courses": '["CS101, Room A1, Monday 09:00"]',
        },
        {
            "schedule_number": "2",
            "schedule_id": "2",
            "courses": '["CS201, Room B2, Tuesday 10:00"]',
        },
    ]


@pytest.mark.parametrize("prefix", ["=", "+", "-", "@", "\t", "\r"])
def test_schedules_to_csv_escapes_formula_like_strings(prefix):
    value = prefix + "SUM(1,2)"
    rows = list(csv.DictReader(io.StringIO(
        ScheduleExporter.schedules_to_csv([[{"name": value}]])
    )))

    assert rows[0]["name"] == "'" + value


def test_schedules_to_csv_preserves_other_values_and_nested_json():
    schedule = {
        "name": "CS101",
        "empty": "",
        "number": -42,
        "decimal": -1.5,
        "enabled": True,
        "missing": None,
        "courses": ["=CS101"],
        "details": {"room": "@A1"},
    }
    rows = list(csv.DictReader(io.StringIO(
        ScheduleExporter.schedules_to_csv([schedule])
    )))

    assert rows == [{
        "schedule_number": "1",
        "name": "CS101",
        "empty": "",
        "number": "-42",
        "decimal": "-1.5",
        "enabled": "True",
        "missing": "",
        "courses": '["=CS101"]',
        "details": '{"room": "@A1"}',
    }]
