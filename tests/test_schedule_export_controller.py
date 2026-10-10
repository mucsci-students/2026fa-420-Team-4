import pytest
from fastapi import HTTPException

from backend.controllers.schedule_export_controller import export_schedule_csv
from backend.models.session_store import store


def test_export_schedule_csv_returns_generated_csv(monkeypatch):
    monkeypatch.setattr(
        store,
        "schedule",
        [{"schedule_id": 1, "courses": ["CS101, Room A1"]}],
    )

    response = export_schedule_csv()

    assert response.media_type.startswith("text/csv")
    assert response.headers["content-disposition"] == (
        'attachment; filename="schedules.csv"'
    )
    assert b"schedule_number,schedule_id,courses" in response.body
    assert b'"CS101, Room A1"' in response.body


def test_export_schedule_csv_requires_generated_schedules(monkeypatch):
    monkeypatch.setattr(store, "schedule", None)

    with pytest.raises(HTTPException) as exc_info:
        export_schedule_csv()

    assert exc_info.value.status_code == 400
