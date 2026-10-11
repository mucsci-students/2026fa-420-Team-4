import asyncio
import json
from io import BytesIO

import pytest
from fastapi import HTTPException
from starlette.datastructures import UploadFile

from backend.back_controllers import generator_controller, schedule_export_controller
from backend.models.session_store import store


def test_import_schedule_file_replaces_available_schedules(monkeypatch):
    schedules = [{
        "schedule_id": 1,
        "courses": [{
            "course": "CS101",
            "faculty": "F1",
            "room": "R1",
            "lab": "L1",
            "times": [{"day": 1, "start": 540, "duration": 90}],
        }],
    }]
    monkeypatch.setattr(store, "schedule", [])
    monkeypatch.setattr(store, "schedule_filename", None)
    file = UploadFile(
        filename="fall-term_schedules.json",
        file=BytesIO(json.dumps(schedules).encode("utf-8")),
    )

    response = asyncio.run(schedule_export_controller.import_schedule_file(file))

    assert response == {"count": 1, "schedules": schedules}
    assert store.schedule == schedules
    assert store.schedule_filename == "fall-term_schedules.json"


def test_import_schedule_file_rejects_invalid_json_without_replacing_schedules(
    monkeypatch,
):
    existing_schedules = [{"schedule_id": 3, "courses": []}]
    monkeypatch.setattr(store, "schedule", existing_schedules)
    file = UploadFile(filename="invalid.json", file=BytesIO(b"{"))

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(schedule_export_controller.import_schedule_file(file))

    assert exc_info.value.status_code == 400
    assert "Malformed schedule JSON" in exc_info.value.detail
    assert store.schedule == existing_schedules


def test_import_schedule_file_rejects_unsupported_data_without_replacing_schedules(
    monkeypatch,
):
    existing_schedules = [{"schedule_id": 3, "courses": []}]
    monkeypatch.setattr(store, "schedule", existing_schedules)
    file = UploadFile(
        filename="unsupported.json",
        file=BytesIO(b'[{"schedule_id": 4, "courses": ["not a schedule"]}]'),
    )

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(schedule_export_controller.import_schedule_file(file))

    assert exc_info.value.status_code == 400
    assert "Invalid schedule data" in exc_info.value.detail
    assert store.schedule == existing_schedules


def test_import_schedule_file_reports_unsupported_extension(monkeypatch):
    existing_schedules = [{"schedule_id": 3, "courses": []}]
    monkeypatch.setattr(store, "schedule", existing_schedules)
    file = UploadFile(
        filename="schedules.csv",
        file=BytesIO(b"CS101,F1,R1,,MON 09:00-10:00"),
    )

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(schedule_export_controller.import_schedule_file(file))

    assert exc_info.value.status_code == 400
    assert "Unsupported schedule file" in exc_info.value.detail
    assert store.schedule == existing_schedules


def test_get_and_clear_available_schedules(monkeypatch):
    monkeypatch.setattr(store, "schedule", [{"schedule_id": 1}])
    monkeypatch.setattr(store, "schedule_filename", "schedules.json")

    assert schedule_export_controller.get_available_schedules() == {
        "count": 1,
        "schedules": [{"schedule_id": 1}],
    }
    assert schedule_export_controller.clear_available_schedules() == {
        "count": 0,
        "schedules": [],
    }
    assert store.schedule == []
    assert store.schedule_filename is None


def test_generator_stores_structured_course_assignments(monkeypatch):
    class FakeCourse:
        def model_dump(self, *, mode, by_alias):
            assert mode == "json"
            assert by_alias is True
            return {
                "course": "CS101.01",
                "faculty": "F1",
                "room": "R1",
                "lab": "L1",
                "times": [
                    {"day": 1, "start": 540, "duration": 90},
                ],
            }

    class FakeScheduler:
        def __init__(self, config):
            pass

        def get_models(self):
            yield [FakeCourse()]

    monkeypatch.setattr(store, "is_loaded", True)
    monkeypatch.setattr(store, "config_object", object())
    monkeypatch.setattr(generator_controller, "Scheduler", FakeScheduler)

    response = generator_controller.run_generator(limit=None)

    assert response["count"] == 1
    assert response["schedules"][0]["courses"][0]["course"] == "CS101.01"
    assert store.schedule[0]["courses"][0]["times"][0]["start"] == 540
