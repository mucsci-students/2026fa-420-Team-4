import json

import pytest

import limit_commands
import optimizer_commands


def _write_config(tmp_path, data):
    path = tmp_path / "config.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def test_validate_limit_accepts_positive_integer():
    # Verifies positive integer limits, including the lower valid boundary, are accepted.
    assert limit_commands.validate_limit("1") == 1
    assert limit_commands.validate_limit(25) == 25


@pytest.mark.parametrize(
    "value, message",
    [
        ("not-a-number", "integer"),
        (None, "integer"),
        ("0", "positive integer"),
        ("-1", "positive integer"),
    ],
)
def test_validate_limit_rejects_invalid_values(value, message):
    # Verifies non-integers and limits below the supported minimum raise ValueError.
    with pytest.raises(ValueError, match=message):
        limit_commands.validate_limit(value)


def test_limit_add_update_remove_and_list_persist_config(tmp_path, monkeypatch, capsys):
    # Verifies the complete limit workflow updates JSON and reports the active value.
    path = _write_config(tmp_path, {})
    responses = iter(["0", "4"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(responses))

    limit_commands.limit_add(None, str(path))
    assert json.loads(path.read_text(encoding="utf-8"))["limit"] == 4
    assert "Invalid input" in capsys.readouterr().out

    monkeypatch.setattr("builtins.input", lambda prompt="": "7")
    limit_commands.limit_update(None, str(path))
    assert json.loads(path.read_text(encoding="utf-8"))["limit"] == 7

    limit_commands.limit_list(None, str(path))
    assert "Current limit: 7" in capsys.readouterr().out

    limit_commands.limit_remove(None, str(path))
    assert "limit" not in json.loads(path.read_text(encoding="utf-8"))


def test_limit_commands_handle_defaults_existing_values_and_empty_filename(
    tmp_path, monkeypatch, capsys
):
    # Verifies default behavior, already-configured state, and missing filenames.
    path = _write_config(tmp_path, {})
    monkeypatch.setattr("builtins.input", lambda prompt="": "")

    limit_commands.limit_add(None, str(path))
    assert json.loads(path.read_text(encoding="utf-8"))["limit"] == limit_commands.DEFAULT_LIMIT

    limit_commands.limit_add(None, str(path))
    assert "already configured" in capsys.readouterr().out

    limit_commands.limit_update(None, str(path))
    assert json.loads(path.read_text(encoding="utf-8"))["limit"] == limit_commands.DEFAULT_LIMIT

    limit_commands.limit_remove(None, str(path))
    limit_commands.limit_remove(None, str(path))
    assert "Already using the default" in capsys.readouterr().out

    limit_commands.limit_list(None, None)
    assert "No configuration file selected" in capsys.readouterr().out


@pytest.mark.parametrize(
    "handler, command, expected",
    [
        (limit_commands.limit_handler, "", "Usage: limit"),
        (limit_commands.limit_handler, "unknown config.json", "Invalid command"),
        (optimizer_commands.optimizer_handler, "", "Usage: optimizer"),
        (optimizer_commands.optimizer_handler, "unknown config.json", "Invalid command"),
    ],
)
def test_command_handlers_report_usage_for_invalid_commands(
    handler, command, expected, capsys
):
    # Verifies both command dispatchers report usage for incomplete or unknown commands.
    handler(None, command)
    assert expected in capsys.readouterr().out


def test_limit_handler_dispatches_supported_command(tmp_path, capsys):
    # Verifies handler dispatch reaches the corresponding limit operation.
    path = _write_config(tmp_path, {"limit": 6})

    limit_commands.limit_handler(None, f"list {path}")

    assert "Current limit: 6" in capsys.readouterr().out


def test_limit_commands_cover_defaults_missing_filenames_and_file_errors(
    tmp_path, monkeypatch, capsys
):
    # Verifies default limit behavior and handled file errors for every limit operation.
    default_path = _write_config(tmp_path, {})
    monkeypatch.setattr("builtins.input", lambda prompt="": "")
    limit_commands.limit_list(None, str(default_path))
    limit_commands.limit_update(None, str(default_path))
    assert json.loads(default_path.read_text(encoding="utf-8"))["limit"] == 10
    assert "Omitted (Defaults to 10)" in capsys.readouterr().out

    for operation in ("add", "list", "update", "remove"):
        getattr(limit_commands, f"limit_{operation}")(None, None)

    bad_path = _write_config(tmp_path, {"bad": True})
    bad_path.write_text("{bad json", encoding="utf-8")
    for operation in ("add", "list", "update", "remove"):
        getattr(limit_commands, f"limit_{operation}")(None, str(bad_path))

    output = capsys.readouterr().out
    assert output.count("No configuration file selected") == 4
    assert "Add limit failed" in output
    assert "List limit failed" in output
    assert "Update limit failed" in output
    assert "Remove limit failed" in output


def test_limit_handler_dispatches_every_supported_operation(monkeypatch, capsys):
    # Verifies handler dispatch for each supported operation and its invalid-command path.
    dispatched = []
    for operation in ("add", "list", "update", "remove"):
        monkeypatch.setattr(
            limit_commands,
            f"limit_{operation}",
            lambda shell, filename, op=operation: dispatched.append((op, filename)),
        )

    for operation in ("add", "list", "update", "remove"):
        limit_commands.limit_handler(None, f"{operation} config.json")
    limit_commands.limit_handler(None, "")
    assert "Usage: limit" in capsys.readouterr().out

    limit_commands.limit_handler(None, "unknown config.json")
    assert "Invalid command" in capsys.readouterr().out
    assert dispatched == [
        (operation, "config.json") for operation in ("add", "list", "update", "remove")
    ]


def test_validate_flags_list_rejects_bad_shapes_and_unknown_flags():
    # Verifies optimizer flag input must be a list containing only supported values.
    with pytest.raises(ValueError, match="array/list"):
        optimizer_commands.validate_flags_list("same_room")
    with pytest.raises(ValueError, match="Unknown flag"):
        optimizer_commands.validate_flags_list(["not_a_flag"])
    assert optimizer_commands.validate_flags_list(
        ["same_room", "same_room", "pack_rooms"]
    ) == ["same_room", "pack_rooms"]


def test_optimizer_add_update_remove_and_list_persist_flags(
    tmp_path, monkeypatch, capsys
):
    # Verifies valid optimizer flag changes persist and list output reflects the state.
    path = _write_config(tmp_path, {"optimizer_flags": []})
    monkeypatch.setattr("builtins.input", lambda prompt="": "same_room, pack_rooms")

    optimizer_commands.optimizer_add(None, str(path))
    assert json.loads(path.read_text(encoding="utf-8"))["optimizer_flags"] == [
        "same_room",
        "pack_rooms",
    ]

    optimizer_commands.optimizer_list(None, str(path))
    output = capsys.readouterr().out
    assert "same_room" in output
    assert "pack_rooms" in output
    assert "(active)" in output

    monkeypatch.setattr("builtins.input", lambda prompt="": "faculty_course")
    optimizer_commands.optimizer_update(None, str(path))
    assert json.loads(path.read_text(encoding="utf-8"))["optimizer_flags"] == [
        "faculty_course"
    ]

    monkeypatch.setattr("builtins.input", lambda prompt="": "1")
    optimizer_commands.optimizer_remove(None, str(path))
    assert json.loads(path.read_text(encoding="utf-8"))["optimizer_flags"] == []


def test_optimizer_add_reprompts_for_invalid_input(tmp_path, monkeypatch, capsys):
    # Verifies unknown and already-active flags are rejected before accepting valid input.
    path = _write_config(tmp_path, {"optimizer_flags": ["same_room"]})
    responses = iter(["unknown_flag", "same_room", "pack_rooms"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(responses))

    optimizer_commands.optimizer_add(None, str(path))

    output = capsys.readouterr().out
    assert "Invalid input" in output
    assert json.loads(path.read_text(encoding="utf-8"))["optimizer_flags"] == [
        "same_room",
        "pack_rooms",
    ]


def test_optimizer_update_keeps_current_value_on_empty_input(tmp_path, monkeypatch):
    # Verifies pressing Enter retains the currently configured optimizer flags.
    path = _write_config(tmp_path, {"optimizer_flags": ["same_lab"]})
    monkeypatch.setattr("builtins.input", lambda prompt="": "")

    optimizer_commands.optimizer_update(None, str(path))

    assert json.loads(path.read_text(encoding="utf-8"))["optimizer_flags"] == [
        "same_lab"
    ]


def test_optimizer_remove_accepts_flag_names_and_rejects_invalid_selection(
    tmp_path, monkeypatch, capsys
):
    # Verifies invalid selectors are rejected and names can remove multiple active flags.
    path = _write_config(
        tmp_path, {"optimizer_flags": ["same_room", "pack_rooms", "same_lab"]}
    )
    responses = iter(["0", "missing_flag", "same_room, 3"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(responses))

    optimizer_commands.optimizer_remove(None, str(path))

    output = capsys.readouterr().out
    assert "Invalid input" in output
    assert json.loads(path.read_text(encoding="utf-8"))["optimizer_flags"] == [
        "pack_rooms"
    ]


def test_optimizer_no_flag_state_and_missing_filename(tmp_path, capsys):
    # Verifies empty optimizer state is reported and missing files are handled.
    path = _write_config(tmp_path, {"optimizer_flags": []})

    optimizer_commands.optimizer_list(None, str(path))
    optimizer_commands.optimizer_remove(None, str(path))
    optimizer_commands.optimizer_add(None, None)

    output = capsys.readouterr().out
    assert "No optimizer flags configured" in output
    assert "No optimizer flags currently configured to remove" in output
    assert "No configuration file selected" in output


def test_optimizer_handler_dispatches_supported_command(tmp_path, capsys):
    # Verifies handler dispatch reaches the requested optimizer operation.
    path = _write_config(tmp_path, {"optimizer_flags": ["same_room"]})

    optimizer_commands.optimizer_handler(None, f"list {path}")

    assert "same_room" in capsys.readouterr().out


def test_optimizer_commands_cover_all_active_empty_and_file_error_paths(
    tmp_path, monkeypatch, capsys
):
    # Verifies all-active flags, blank-input retry, and handled file failures.
    all_active_path = _write_config(
        tmp_path, {"optimizer_flags": list(optimizer_commands.VALID_OPTIMIZER_FLAGS)}
    )
    optimizer_commands.optimizer_add(None, str(all_active_path))
    assert "All valid optimizer flags are already active" in capsys.readouterr().out

    path = _write_config(tmp_path, {"optimizer_flags": []})
    responses = iter(["", "same_room"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(responses))
    optimizer_commands.optimizer_add(None, str(path))
    assert "Invalid input" in capsys.readouterr().out

    for operation in ("list", "update", "remove"):
        getattr(optimizer_commands, f"optimizer_{operation}")(None, None)

    bad_path = tmp_path / "bad_optimizer.json"
    bad_path.write_text("{bad json", encoding="utf-8")
    for operation in ("add", "list", "update", "remove"):
        getattr(optimizer_commands, f"optimizer_{operation}")(None, str(bad_path))

    output = capsys.readouterr().out
    assert output.count("No configuration file selected") == 3
    assert "Add failed" in output
    assert "List failed" in output
    assert "Update failed" in output
    assert "Remove failed" in output


def test_optimizer_update_can_clear_flags_and_remove_retries_empty_selection(
    tmp_path, monkeypatch, capsys
):
    # Verifies update parsing can yield an empty list and remove rejects blank selection.
    path = _write_config(tmp_path, {"optimizer_flags": ["same_room"]})
    original_prompt = optimizer_commands._prompt_input

    def clear_flags_for_prompt(prompt_text, validator_func, default=None):
        if prompt_text.startswith("Optimizer flags"):
            return validator_func("")
        return original_prompt(prompt_text, validator_func, default)

    monkeypatch.setattr(
        optimizer_commands, "_prompt_input", clear_flags_for_prompt
    )
    optimizer_commands.optimizer_update(None, str(path))
    assert json.loads(path.read_text(encoding="utf-8"))["optimizer_flags"] == []

    responses = iter(["", "same_room"])
    monkeypatch.setattr(optimizer_commands, "_prompt_input", original_prompt)
    monkeypatch.setattr("builtins.input", lambda prompt="": next(responses))
    path.write_text(json.dumps({"optimizer_flags": ["same_room"]}), encoding="utf-8")
    optimizer_commands.optimizer_remove(None, str(path))
    assert "Invalid input" in capsys.readouterr().out
    assert json.loads(path.read_text(encoding="utf-8"))["optimizer_flags"] == []


def test_optimizer_handler_dispatches_every_supported_operation(monkeypatch, capsys):
    # Verifies all optimizer handler branches and invalid-command reporting.
    dispatched = []
    for operation in ("add", "list", "update", "remove"):
        monkeypatch.setattr(
            optimizer_commands,
            f"optimizer_{operation}",
            lambda shell, filename, op=operation: dispatched.append((op, filename)),
        )

    for operation in ("add", "list", "update", "remove"):
        optimizer_commands.optimizer_handler(None, f"{operation} config.json")
    optimizer_commands.optimizer_handler(None, "")
    assert "Usage: optimizer" in capsys.readouterr().out

    optimizer_commands.optimizer_handler(None, "unknown config.json")
    assert "Invalid command" in capsys.readouterr().out
    assert dispatched == [
        (operation, "config.json") for operation in ("add", "list", "update", "remove")
    ]
