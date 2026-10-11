import json

import pytest

import lab_commands
import room_commands


RESOURCE_COMMANDS = [
    (room_commands, "rooms", "room"),
    (lab_commands, "labs", "lab"),
]


def _write_config(tmp_path, section, entries):
    path = tmp_path / f"{section}.json"
    path.write_text(json.dumps({"config": {section: entries}}), encoding="utf-8")
    return path


@pytest.mark.parametrize("module, section, label", RESOURCE_COMMANDS)
def test_resource_add_reprompts_for_duplicates_and_invalid_values(
    module, section, label, tmp_path, monkeypatch, capsys
):
    # Verifies resource creation retries invalid entries before persisting valid values.
    path = _write_config(
        tmp_path,
        section,
        [{"name": f"Existing {label}", "capacity": 5, "features": [], "times": None}],
    )
    responses = iter(
        [
            f"existing {label}",
            f"New {label}",
            "0",
            "15",
            "projector, projector",
            "projector, whiteboard",
            "n",
        ]
    )
    monkeypatch.setattr("builtins.input", lambda prompt="": next(responses))

    getattr(module, f"{label}_add")(None, str(path))

    saved = json.loads(path.read_text(encoding="utf-8"))["config"][section]
    assert saved[-1]["name"] == f"New {label}"
    assert saved[-1]["capacity"] == 15
    assert saved[-1]["features"] == ["projector", "whiteboard"]
    assert "Invalid input" in capsys.readouterr().out


@pytest.mark.parametrize("module, section, label", RESOURCE_COMMANDS)
def test_resource_list_displays_restricted_and_missing_optional_values(
    module, section, label, tmp_path, capsys
):
    # Verifies resource listing handles restricted availability and absent fields.
    path = _write_config(
        tmp_path,
        section,
        [
            {
                "name": f"Restricted {label}",
                "capacity": 20,
                "features": ["projector"],
                "times": {"MON": [{"start": "08:00", "end": "12:00"}]},
            },
            {},
        ],
    )

    getattr(module, f"{label}_list")(None, str(path))

    output = capsys.readouterr().out
    assert f"Restricted {label}" in output
    assert "Restricted [MON]" in output
    assert "N/A" in output
    assert "None" in output


@pytest.mark.parametrize("module, section, label", RESOURCE_COMMANDS)
def test_resource_remove_reprompts_and_persists_case_insensitive_match(
    module, section, label, tmp_path, monkeypatch, capsys
):
    # Verifies an unknown name is rejected before a case-insensitive match is removed.
    path = _write_config(
        tmp_path,
        section,
        [
            {"name": f"First {label}", "capacity": 20, "features": [], "times": None},
            {"name": f"Second {label}", "capacity": 15, "features": [], "times": None},
        ],
    )
    responses = iter(["missing", f"first {label}"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(responses))

    getattr(module, f"{label}_remove")(None, str(path))

    remaining = json.loads(path.read_text(encoding="utf-8"))["config"][section]
    assert [item["name"] for item in remaining] == [f"Second {label}"]
    assert "Invalid input" in capsys.readouterr().out


@pytest.mark.parametrize("module, section, label", RESOURCE_COMMANDS)
def test_resource_update_changes_fields_and_replaces_restricted_hours(
    module, section, label, tmp_path, monkeypatch
):
    # Verifies updates validate fields and can replace unrestricted availability with windows.
    path = _write_config(
        tmp_path,
        section,
        [{"name": f"Old {label}", "capacity": 10, "features": ["old"], "times": None}],
    )
    responses = iter(
        [
            f"Old {label}",
            f"New {label}",
            "bad",
            "25",
            "new feature",
            "y",
            "y",
            "08:00-12:00",
            "",
            "",
            "",
            "",
        ]
    )
    monkeypatch.setattr("builtins.input", lambda prompt="": next(responses))

    getattr(module, f"{label}_update")(None, str(path))

    updated = json.loads(path.read_text(encoding="utf-8"))["config"][section][0]
    assert updated["name"] == f"New {label}"
    assert updated["capacity"] == 25
    assert updated["features"] == ["new feature"]
    assert updated["times"] == {"MON": [{"start": "08:00", "end": "12:00"}]}


@pytest.mark.parametrize("module, section, label", RESOURCE_COMMANDS)
def test_resource_commands_report_empty_states_and_missing_filename(
    module, section, label, tmp_path, capsys
):
    # Verifies list, remove, and update report empty states and add handles no filename.
    path = _write_config(tmp_path, section, [])

    getattr(module, f"{label}_list")(None, str(path))
    getattr(module, f"{label}_remove")(None, str(path))
    getattr(module, f"{label}_update")(None, str(path))
    getattr(module, f"{label}_add")(None, None)

    output = capsys.readouterr().out
    assert f"No {section[:-1]}s found" in output
    assert f"No {section[:-1]}s available to remove" in output
    assert f"No {section[:-1]}s available to update" in output
    assert "No configuration file selected" in output


@pytest.mark.parametrize("module, section, label", RESOURCE_COMMANDS)
def test_resource_handlers_dispatch_each_operation(
    module, section, label, monkeypatch, capsys
):
    # Verifies supported handler commands dispatch and invalid invocations show usage.
    dispatched = []
    for command in ("add", "list", "remove", "update"):
        monkeypatch.setattr(
            module,
            f"{label}_{command}",
            lambda shell, filename, op=command: dispatched.append((op, filename)),
        )

    handler = getattr(module, f"{label}_handler")
    handler(None, "ADD config.json")
    handler(None, "list config.json")
    handler(None, "remove config.json")
    handler(None, "update config.json")
    handler(None, "")
    assert "Usage:" in capsys.readouterr().out

    handler(None, "unknown config.json")
    assert "Invalid command" in capsys.readouterr().out
    assert dispatched == [(command, "config.json") for command in ("add", "list", "remove", "update")]


def test_room_remove_last_room_reports_schema_warning(tmp_path, monkeypatch, capsys):
    # Verifies removing the only room reports that the resulting config has no rooms.
    path = _write_config(
        tmp_path,
        "rooms",
        [{"name": "Only room", "capacity": 10, "features": [], "times": None}],
    )
    monkeypatch.setattr("builtins.input", lambda prompt="": "Only room")

    room_commands.room_remove(None, str(path))

    assert "Schema requires 'rooms' to be non-empty" in capsys.readouterr().out
    assert json.loads(path.read_text(encoding="utf-8"))["config"]["rooms"] == []


def test_resource_add_handles_missing_filename_and_bad_json(tmp_path, capsys):
    # Verifies lab and room additions handle missing files and invalid JSON gracefully.
    room_commands.room_add(None, None)
    lab_commands.lab_add(None, None)
    bad_file = tmp_path / "bad.json"
    bad_file.write_text("{bad json", encoding="utf-8")
    room_commands.room_add(None, str(bad_file))
    lab_commands.lab_add(None, str(bad_file))

    output = capsys.readouterr().out
    assert output.count("No configuration file selected") == 2
    assert "Failed to add room" in output
    assert "Failed to add lab" in output


@pytest.mark.parametrize("module, section, label", RESOURCE_COMMANDS)
def test_resource_helpers_cover_type_empty_list_and_skipped_day_paths(
    module, section, label, monkeypatch
):
    # Verifies type/list errors and the nested availability validator's empty result.
    with pytest.raises(ValueError, match="string"):
        module._clean_str(10)
    with pytest.raises(ValueError, match="List cannot be empty"):
        module._parse_list("", allow_empty=False)
    with pytest.raises(ValueError, match="List cannot be empty"):
        module._parse_list(", ,", allow_empty=False)

    def prompt_with_empty_day(prompt_text, validator_func, default=None):
        if prompt_text.startswith("Does"):
            return True
        validator_func("")
        return default

    monkeypatch.setattr(module, "_prompt_input", prompt_with_empty_day)

    assert getattr(module, f"_prompt_{label}_times")() == {}


@pytest.mark.parametrize("module, section, label", RESOURCE_COMMANDS)
def test_resource_add_creates_missing_section_and_update_rejects_duplicate_name(
    module, section, label, tmp_path, monkeypatch, capsys
):
    # Verifies resource section initialization and duplicate-name update validation.
    path = tmp_path / f"{section}_missing.json"
    path.write_text(json.dumps({"config": {}}), encoding="utf-8")
    responses = iter(["New", "10", "", "n"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(responses))
    getattr(module, f"{label}_add")(None, str(path))
    assert json.loads(path.read_text(encoding="utf-8"))["config"][section][0]["name"] == "New"

    path = _write_config(
        tmp_path,
        section,
        [
            {"name": "First", "capacity": 10, "features": [], "times": None},
            {"name": "Second", "capacity": 20, "features": [], "times": None},
        ],
    )
    responses = iter(["First", "Second", "Third", "15", "", "n"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(responses))
    getattr(module, f"{label}_update")(None, str(path))

    resources = json.loads(path.read_text(encoding="utf-8"))["config"][section]
    assert resources[0]["name"] == "Third"
    assert resources[0]["capacity"] == 15
    assert "already exists" in capsys.readouterr().out


@pytest.mark.parametrize("module, section, label", RESOURCE_COMMANDS)
def test_resource_list_remove_and_update_handle_missing_files_and_bad_json(
    module, section, label, tmp_path, capsys
):
    # Verifies read failures are caught for all resource operations that open files.
    bad_path = tmp_path / f"bad_{section}.json"
    bad_path.write_text("{bad json", encoding="utf-8")

    getattr(module, f"{label}_list")(None, None)
    getattr(module, f"{label}_remove")(None, None)
    getattr(module, f"{label}_update")(None, None)
    getattr(module, f"{label}_list")(None, str(bad_path))
    getattr(module, f"{label}_remove")(None, str(bad_path))

    output = capsys.readouterr().out
    assert output.count("No configuration file selected") == 3
    assert "List failed" in output
    assert "Remove failed" in output
