import pytest
from fastapi import HTTPException

from backend.back_controllers.schedule_export_controller import (
    export_schedule_csv,
    export_schedule_json,
)
from backend.models.session_store import store


def test_export_schedule_csv_returns_generated_csv(monkeypatch):
    monkeypatch.setattr(
        store,
        "schedule",
        [{"schedule_id": 1, "courses": ["CS101, Room A1"]}],
    )
    monkeypatch.setattr(store, "config_filename", "fall-term.json")

    response = export_schedule_csv()

    assert response.media_type.startswith("text/csv")
    assert response.headers["content-disposition"] == (
        'attachment; filename="fall-term_schedules.csv"'
    )
    assert b"schedule_number,schedule_id,courses" in response.body
    assert b'"CS101, Room A1"' in response.body


def test_export_schedule_csv_requires_generated_schedules(monkeypatch):
    monkeypatch.setattr(store, "schedule", None)

    with pytest.raises(HTTPException) as exc_info:
        export_schedule_csv()

    assert exc_info.value.status_code == 400


def test_export_schedule_json_returns_generated_json(monkeypatch):
    """Verify JSON attachment content, media type, and configuration-based filename."""
    monkeypatch.setattr(
        store,
        "schedule",
        [{"schedule_id": 1, "courses": ["CS101, Room A1"]}],
    )
    monkeypatch.setattr(store, "config_filename", "fall-term.json")

    response = export_schedule_json()

    assert response.media_type.startswith("application/json")
    assert response.headers["content-disposition"] == (
        'attachment; filename="fall-term_schedules.json"'
    )
    assert response.body == (
        b'[\n  {\n    "schedule_id": 1,\n'
        b'    "courses": [\n      "CS101, Room A1"\n    ]\n  }\n]\n'
    )


def test_export_schedule_json_requires_generated_schedules(monkeypatch):
    """Verify JSON export rejects a session without schedules with HTTP 400."""
    monkeypatch.setattr(store, "schedule", None)

    with pytest.raises(HTTPException) as exc_info:
        export_schedule_json()

    assert exc_info.value.status_code == 400
