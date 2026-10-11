import asyncio
from io import BytesIO
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from starlette.datastructures import UploadFile

from backend import json_validator
from backend.back_controllers import (
    file_controller,
    generator_controller,
    schedule_export_controller,
)
from backend.main import app, root
from backend.models.session_store import SessionStore, store
from scheduler.config import CombinedConfig


def _valid_config():
    # Returns a valid scheduler config fixture for API input validation.
    return {
        "config": {
            "rooms": [{"name": "R1", "capacity": 30}],
            "labs": [{"name": "L1", "capacity": 30}],
            "courses": [
                {
                    "course_id": "CS101",
                    "credits": 4,
                    "capacity": 30,
                    "room": ["R1"],
                    "lab": ["L1"],
                    "conflicts": [],
                    "faculty": ["F1"],
                }
            ],
            "faculty": [
                {
                    "name": "F1",
                    "maximum_credits": 4,
                    "minimum_credits": 4,
                    "unique_course_limit": 1,
                    "times": {
                        day: ["08:00-20:00"]
                        for day in ("MON", "TUE", "WED", "THU", "FRI")
                    },
                }
            ],
        },
        "time_slot_config": {
            "times": {
                day: [{"start": "08:00", "spacing": 60, "end": "20:00"}]
                for day in ("MON", "TUE", "WED", "THU", "FRI")
            },
            "classes": [
                {
                    "credits": 4,
                    "meetings": [
                        {"day": "MON", "duration": 110, "lab": True},
                        {"day": "WED", "duration": 110, "lab": False},
                    ],
                }
            ],
        },
        "limit": 2,
        "optimizer_flags": [],
    }


def _upload(data, filename="config.json"):
    # Builds an in-memory upload matching FastAPI's UploadFile interface.
    content = data if isinstance(data, bytes) else data.encode("utf-8")
    return UploadFile(filename=filename, file=BytesIO(content))


def test_api_root_routes_and_cors_headers():
    # Verifies the application root, all expected API route prefixes, and CORS setup.
    assert root() == {
        "status": "online",
        "message": "Academic Scheduler API active",
    }
    client = TestClient(app)
    assert client.get("/").json()["status"] == "online"
    paths = set(client.get("/openapi.json").json()["paths"])
    assert {
        "/api/config/",
        "/api/config/upload",
        "/api/config/validate",
        "/api/generator/run",
        "/api/schedule/available",
        "/api/schedule/import",
        "/api/schedule/export/json",
        "/api/schedule/export/csv",
    }.issubset(paths)
    response = client.options(
        "/api/config/",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"


def test_session_store_initializes_and_reset_clears_every_field():
    # Verifies session state starts empty and reset clears every stored value.
    state = SessionStore()
    assert state.raw_config == {}
    assert state.config_filename is None
    assert state.config_object is None
    assert state.schedule is None
    assert state.schedule_filename is None
    assert state.is_loaded is False

    state.raw_config = {"config": {}}
    state.config_filename = "config.json"
    state.config_object = object()
    state.schedule = [{"schedule_id": 1}]
    state.schedule_filename = "schedule.json"
    state.is_loaded = True
    state.reset()

    assert state.raw_config == {}
    assert state.config_filename is None
    assert state.config_object is None
    assert state.schedule is None
    assert state.schedule_filename is None
    assert state.is_loaded is False


def test_json_validator_handles_root_diagnostics_and_engine_exceptions(monkeypatch):
    # Verifies root type errors, scheduler diagnostics, and validation exceptions.
    assert json_validator.validate_config_dict([]) == (
        False,
        ["Root structure of JSON payload must be an object/dict."],
    )

    finding = SimpleNamespace(code="E001", path="config.rooms", message="invalid")
    monkeypatch.setattr(
        json_validator,
        "validate_combined_config_data",
        lambda data: SimpleNamespace(is_valid=False, diagnostics=[finding]),
    )
    assert json_validator.validate_config_dict({}) == (
        False,
        ["[E001] config.rooms: invalid"],
    )

    def fail_validation(_data):
        raise RuntimeError("validation unavailable")

    monkeypatch.setattr(
        json_validator, "validate_combined_config_data", fail_validation
    )
    assert json_validator.validate_config_dict({}) == (
        False,
        ["Validation exception: validation unavailable"],
    )


def test_json_validator_reports_unreadable_file(tmp_path, monkeypatch):
    # Verifies an existing file that cannot be opened returns a read diagnostic.
    path = tmp_path / "config.json"
    path.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(json_validator.os.path, "isfile", lambda filename: True)

    def fail_open(*args, **kwargs):
        raise OSError("access denied")

    monkeypatch.setattr("builtins.open", fail_open)
    is_valid, errors = json_validator.validate_config_file(str(path))

    assert is_valid is False
    assert "Could not read file" in errors[0]
    assert "access denied" in errors[0]


def test_config_upload_and_validate_error_paths(monkeypatch):
    # Verifies malformed uploads, invalid configs, and model errors return HTTP 400.
    store.reset()
    with pytest.raises(HTTPException) as exc:
        asyncio.run(file_controller.upload_config(_upload(b"{bad")))
    assert exc.value.status_code == 400
    assert exc.value.detail == "Invalid JSON format"

    monkeypatch.setattr(
        file_controller, "validate_config_dict", lambda data: (False, ["bad config"])
    )
    with pytest.raises(HTTPException) as exc:
        asyncio.run(file_controller.upload_config(_upload("{}")))
    assert exc.value.status_code == 400

    monkeypatch.setattr(
        file_controller, "validate_config_dict", lambda data: (True, [])
    )
    monkeypatch.setattr(
        CombinedConfig,
        "model_validate",
        classmethod(lambda cls, data: (_ for _ in ()).throw(ValueError("model error"))),
    )
    with pytest.raises(HTTPException, match="Configuration error"):
        asyncio.run(file_controller.upload_config(_upload("{}")))

    with pytest.raises(HTTPException, match="Invalid JSON format"):
        asyncio.run(file_controller.validate_config(_upload(b"{bad")))
    monkeypatch.setattr(
        file_controller, "validate_config_dict", lambda data: (False, ["bad config"])
    )
    with pytest.raises(HTTPException) as exc:
        asyncio.run(file_controller.validate_config(_upload("{}")))
    assert exc.value.detail == {"errors": ["bad config"]}


def test_config_upload_and_validate_successfully_store_or_validate(
    monkeypatch,
):
    # Verifies successful upload stores parsed state and validate leaves state untouched.
    payload = _valid_config()
    import json

    content = json.dumps(payload).encode("utf-8")
    monkeypatch.setattr(file_controller, "validate_config_dict", lambda data: (True, []))
    monkeypatch.setattr(
        CombinedConfig,
        "model_validate",
        classmethod(lambda cls, data: object()),
    )
    store.reset()

    response = asyncio.run(
        file_controller.upload_config(_upload(content, "fall.json"))
    )
    assert response["config"] == payload
    assert store.raw_config == payload
    assert store.config_filename == "fall.json"
    assert store.is_loaded is True

    previous_config = store.raw_config
    validated = asyncio.run(file_controller.validate_config(_upload(content)))
    assert validated == {"message": "Configuration validated successfully"}
    assert store.raw_config is previous_config


def test_config_validate_reports_model_validation_errors(monkeypatch):
    # Verifies model validation errors are converted into HTTP 400 responses.
    monkeypatch.setattr(file_controller, "validate_config_dict", lambda data: (True, []))
    monkeypatch.setattr(
        CombinedConfig,
        "model_validate",
        classmethod(
            lambda cls, data: (_ for _ in ()).throw(ValueError("invalid model"))
        ),
    )

    with pytest.raises(HTTPException) as exc:
        asyncio.run(file_controller.validate_config(_upload("{}")))

    assert exc.value.status_code == 400
    assert exc.value.detail == "Configuration error: invalid model"


def test_generator_reports_scheduler_failure(monkeypatch):
    # Verifies scheduler exceptions are converted to an explicit HTTP 500 response.
    store.reset()
    store.config_object = object()
    store.is_loaded = True

    def fail_scheduler(_config):
        raise RuntimeError("engine failed")

    monkeypatch.setattr(generator_controller, "Scheduler", fail_scheduler)

    with pytest.raises(HTTPException) as exc:
        generator_controller.run_generator(limit=None)

    assert exc.value.status_code == 500
    assert "engine failed" in exc.value.detail


def test_schedule_export_reports_encoding_failure_and_supports_unicode_filename(
    monkeypatch,
):
    # Verifies serialization errors become HTTP 500 and Unicode filenames use RFC 5987.
    store.reset()
    store.schedule = [{"schedule_id": 1, "courses": []}]
    store.schedule_filename = "schedules.json"

    def fail_csv(_schedules):
        raise TypeError("bad schedule")

    monkeypatch.setattr(schedule_export_controller.ScheduleExporter, "schedules_to_csv", fail_csv)
    with pytest.raises(HTTPException) as exc:
        schedule_export_controller.export_schedule_csv()
    assert exc.value.status_code == 500
    assert "bad schedule" in exc.value.detail

    monkeypatch.setattr(
        schedule_export_controller.ScheduleExporter,
        "schedules_to_json",
        lambda schedules: "[]",
    )
    store.schedule_filename = "café.json"
    response = schedule_export_controller.export_schedule_json()
    assert "filename*=UTF-8''caf%C3%A9_schedules.json" in response.headers[
        "Content-Disposition"
    ]
