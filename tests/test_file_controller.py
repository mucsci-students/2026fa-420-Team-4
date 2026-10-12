import asyncio
from io import BytesIO

from starlette.datastructures import UploadFile

from backend.back_controllers import file_controller
from backend.models.session_store import store
from scheduler.config import CombinedConfig


def test_upload_config_stores_source_filename(monkeypatch):
    monkeypatch.setattr(
        file_controller, "validate_config_dict", lambda data: (True, [])
    )
    monkeypatch.setattr(
        CombinedConfig,
        "model_validate",
        classmethod(lambda cls, data: object()),
    )
    monkeypatch.setattr(store, "raw_config", {})
    monkeypatch.setattr(store, "config_filename", None)
    monkeypatch.setattr(store, "config_object", None)
    monkeypatch.setattr(store, "is_loaded", False)

    response = asyncio.run(
        file_controller.upload_config(
            UploadFile(filename="fall-term.json", file=BytesIO(b"{}"))
        )
    )

    assert response["message"] == "Configuration uploaded and validated successfully"
    assert store.config_filename == "fall-term.json"
