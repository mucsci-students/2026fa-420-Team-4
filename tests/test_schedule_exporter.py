import csv
import io

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
