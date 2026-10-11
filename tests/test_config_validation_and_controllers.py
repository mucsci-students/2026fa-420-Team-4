import json

import pytest
from fastapi import HTTPException

from backend.back_controllers import config_controller, generator_controller
from backend.json_validator import validate_config_dict, validate_config_file
from backend.models.session_store import store
from scheduler.config import CombinedConfig


def _valid_config():
    # Returns a compact but valid scheduler config used by multiple tests.
    with open("tests/jsonfiles/new_minimal_config.json", "r", encoding="utf-8") as file:
        return json.load(file)


def test_get_config_returns_empty_state_when_unloaded():
    # Verifies an unloaded session reports an empty config rather than a stale value.
    store.reset()

    result = config_controller.get_config()

    assert result == {"status": "empty", "config": {}}


def test_get_config_returns_loaded_config():
    # Verifies the controller exposes the raw config after a configuration is loaded.
    store.reset()
    payload = {"config": {"rooms": [{"name": "R1", "capacity": 30}]}}
    store.raw_config = payload
    store.is_loaded = True

    result = config_controller.get_config()

    assert result["status"] == "loaded"
    assert result["config"] == payload


def test_validate_config_dict_accepts_valid_payload():
    # Verifies a known-good config is accepted by the validation helper.
    config = _valid_config()

    is_valid, errors = validate_config_dict(config)

    assert is_valid is True
    assert errors == []


def test_validate_config_dict_rejects_invalid_payload():
    # Verifies malformed config payloads are rejected with descriptive diagnostics.
    bad_payload = {"config": {"rooms": "not-a-list"}}

    is_valid, errors = validate_config_dict(bad_payload)

    assert is_valid is False
    assert len(errors) > 0
    assert "[" in errors[0]


def test_validate_config_file_accepts_valid_file_and_rejects_missing_file(tmp_path):
    # Verifies file-based validation succeeds for valid JSON and fails cleanly for missing files.
    config = _valid_config()
    valid_path = tmp_path / "valid_config.json"
    valid_path.write_text(json.dumps(config), encoding="utf-8")

    is_valid, errors = validate_config_file(str(valid_path))

    assert is_valid is True
    assert errors == []

    missing_path = tmp_path / "missing_config.json"
    is_valid, errors = validate_config_file(str(missing_path))

    assert is_valid is False
    assert "File not found" in errors[0]


def test_validate_config_file_rejects_invalid_json(tmp_path):
    # Verifies malformed JSON is reported as a syntax error instead of being silently accepted.
    bad_file = tmp_path / "bad_config.json"
    bad_file.write_text("{not valid json}", encoding="utf-8")

    is_valid, errors = validate_config_file(str(bad_file))

    assert is_valid is False
    assert "Invalid JSON syntax" in errors[0]


def test_run_generator_rejects_unloaded_state():
    # Verifies generation refuses to run when no configuration has been loaded.
    store.reset()

    with pytest.raises(HTTPException) as exc:
        generator_controller.run_generator()

    assert exc.value.status_code == 400
    assert "No configuration loaded" in exc.value.detail


def test_run_generator_returns_zero_schedule_count_when_limit_zero():
    # Verifies a zero limit clears schedules without attempting to generate new ones.
    store.reset()
    store.config_object = CombinedConfig.model_validate(_valid_config())
    store.is_loaded = True

    result = generator_controller.run_generator(limit=0)

    assert result["status"] == "success"
    assert result["count"] == 0
    assert result["schedules"] == []


def test_run_generator_returns_schedules_for_loaded_config():
    # Verifies generation uses the loaded CombinedConfig and produces a schedule list.
    store.reset()
    payload = _valid_config()
    store.config_object = CombinedConfig.model_validate(payload)
    store.is_loaded = True

    result = generator_controller.run_generator(limit=2)

    assert result["status"] == "success"
    assert 0 < result["count"] <= 2
    assert len(result["schedules"]) == result["count"]
    assert result["schedules"][0]["schedule_id"] == 1
    assert "courses" in result["schedules"][0]


def test_get_generator_progress_reports_running_state():
    # Verifies the progress endpoint exposes the latest generation state.
    store.reset()
    store.generation_progess = 3
    store.generation_running = True

    result = generator_controller.get_generator_progress()

    assert result == {"count": 3, "running": True}
