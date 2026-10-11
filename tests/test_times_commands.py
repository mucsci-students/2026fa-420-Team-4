import json

import pytest

from backend import times_commands


def _write_config(tmp_path, data):
    path = tmp_path / "times.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def test_time_command_helpers_parse_and_locate_configuration():
    # Verifies time and list helpers handle valid inputs, bounds, and fallback sections.
    assert times_commands._clean_str("MON") == "MON"
    assert times_commands._clean_str("", allow_empty=True) == ""
    assert times_commands._parse_int("0", min_value=0) == 0
    assert times_commands._parse_list("online, lab") == ["online", "lab"]
    assert times_commands._parse_list("", allow_empty=True) == []
    assert times_commands._parse_time_range("08:00-12:00") == {
        "start": "08:00",
        "end": "12:00",
    }
    assert times_commands._parse_time_str("23:59") == "23:59"
    assert times_commands._get_times_dict(
        {"time_slot_config": {"times": {"MON": []}}, "config": {"times": {"TUE": []}}}
    ) == ({"MON": []}, "time_slot_config")
    assert times_commands._get_times_dict({"config": {"times": {"TUE": []}}}) == (
        {"TUE": []},
        "config",
    )
    assert times_commands._get_times_dict({}) == ({}, "time_slot_config")
    assert times_commands._get_classes_list(
        {"time_slot_config": {"classes": [1]}, "config": {"classes": [2]}}
    ) == ([1], "time_slot_config")
    assert times_commands._get_classes_list({"config": {"classes": [2]}}) == (
        [2],
        "config",
    )
    assert times_commands._get_classes_list({}) == ([], "time_slot_config")
    with pytest.raises(ValueError, match="List cannot be empty"):
        times_commands._parse_list("", allow_empty=False)


@pytest.mark.parametrize(
    "call, value",
    [
        (times_commands._clean_str, ""),
        (times_commands._parse_int, "bad"),
        (times_commands._parse_list, "one, one"),
        (times_commands._parse_time_range, "08:00"),
        (times_commands._parse_time_range, "24:00-25:00"),
        (times_commands._parse_time_range, "12:00-11:00"),
        (times_commands._parse_time_str, "24:00"),
    ],
)
def test_time_command_helpers_reject_invalid_inputs(call, value):
    # Verifies malformed strings and duplicate values are rejected by the helper APIs.
    with pytest.raises(ValueError):
        call(value)
    with pytest.raises(ValueError):
        times_commands._parse_list(", ,", allow_empty=False)


def test_times_list_displays_all_weekdays_and_handles_empty_and_missing_file(
    tmp_path, capsys
):
    # Verifies listing prints configured blocks, missing weekdays, and empty-state text.
    path = _write_config(
        tmp_path,
        {
            "time_slot_config": {
                "times": {
                    "MON": [{"start": "08:00", "end": "12:00", "spacing": 30}],
                    "WED": [{"start": "09:00", "end": "17:00", "spacing": 60}],
                }
            }
        },
    )
    times_commands.times_list(None, str(path))
    output = capsys.readouterr().out
    assert "MON: 08:00-12:00 (spacing: 30m)" in output
    assert "TUE: [MISSING / EMPTY]" in output

    empty_path = _write_config(tmp_path, {})
    times_commands.times_list(None, str(empty_path))
    assert "No time blocks configured" in capsys.readouterr().out

    times_commands.times_list(None, None)
    assert "No configuration file selected" in capsys.readouterr().out


def test_times_update_retries_invalid_blocks_and_creates_default_section(
    tmp_path, monkeypatch, capsys
):
    # Verifies time updates reject empty, malformed, and nonpositive-spacing blocks.
    path = _write_config(tmp_path, {})
    responses = iter(
        [
            "",
            "08:00-12:00",
            "08:00-12:00@0",
            "08:00-12:00@30,13:00-17:00@30",
            "09:00-17:00@60",
            "09:00-17:00@60",
            "09:00-17:00@60",
            "09:00-17:00@60",
        ]
    )
    monkeypatch.setattr("builtins.input", lambda prompt="": next(responses))

    times_commands.times_update(None, str(path))

    saved = json.loads(path.read_text(encoding="utf-8"))
    assert saved["time_slot_config"]["times"]["MON"] == [
        {"start": "08:00", "spacing": 30, "end": "12:00"},
        {"start": "13:00", "spacing": 30, "end": "17:00"},
    ]
    assert "Time blocks updated successfully" in capsys.readouterr().out


def test_times_update_uses_config_fallback_and_handles_bad_file(
    tmp_path, monkeypatch, capsys
):
    # Verifies updates use the legacy config section when it owns the time data.
    path = _write_config(tmp_path, {"config": {"times": {}}})
    monkeypatch.setattr(
        "builtins.input", lambda prompt="": "08:00-12:00@30"
    )

    times_commands.times_update(None, str(path))

    saved = json.loads(path.read_text(encoding="utf-8"))
    assert saved["config"]["times"]["FRI"] == [
        {"start": "08:00", "spacing": 30, "end": "12:00"}
    ]

    bad_file = tmp_path / "bad.json"
    bad_file.write_text("{broken", encoding="utf-8")
    times_commands.times_update(None, str(bad_file))
    assert "Update failed" in capsys.readouterr().out


def test_prompt_meetings_validates_each_meeting_field(monkeypatch, capsys):
    # Verifies invalid meeting data is rejected before one valid meeting is returned.
    responses = iter(
        [
            "y",
            "SAT",
            "mon",
            "0",
            "110",
            "hybrid",
            "online",
            "y",
            "bad-time",
            "09:30",
            "n",
        ]
    )
    monkeypatch.setattr("builtins.input", lambda prompt="": next(responses))

    meetings = times_commands._prompt_meetings()

    assert meetings == [
        {
            "day": "MON",
            "duration": 110,
            "delivery": "online",
            "lab": True,
            "start_time": "09:30",
        }
    ]
    assert capsys.readouterr().out.count("Invalid input") == 4


def test_classes_add_persists_class_pattern_and_meeting(tmp_path, monkeypatch):
    # Verifies adding a class pattern creates the time-slot section and stores its fields.
    path = _write_config(tmp_path, {})
    responses = iter(
        [
            "4",
            "09:00",
            "y",
            "y",
            "mon",
            "110",
            "in_person",
            "y",
            "09:30",
            "n",
        ]
    )
    monkeypatch.setattr("builtins.input", lambda prompt="": next(responses))

    times_commands.classes_add(None, str(path))

    pattern = json.loads(path.read_text(encoding="utf-8"))["time_slot_config"]["classes"][0]
    assert pattern == {
        "credits": 4,
        "meetings": [
            {
                "day": "MON",
                "duration": 110,
                "delivery": "in_person",
                "lab": True,
                "start_time": "09:30",
            }
        ],
        "disabled": True,
        "start_time": "09:00",
    }


def test_classes_list_and_helpers_handle_legacy_and_empty_sections(tmp_path, capsys):
    # Verifies class listing formats optional meeting details and legacy placement.
    path = _write_config(
        tmp_path,
        {
            "config": {
                "classes": [
                    {
                        "credits": 4,
                        "disabled": True,
                        "start_time": "09:00",
                        "meetings": [
                            {
                                "day": "MON",
                                "duration": 110,
                                "delivery": "online",
                                "lab": True,
                                "start_time": "09:30",
                            }
                        ],
                    },
                    {},
                ]
            }
        },
    )
    times_commands.classes_list(None, str(path))
    output = capsys.readouterr().out
    assert "Disabled" in output
    assert "MON 110m (online) [LAB] @ 09:30" in output
    assert "Enabled" in output

    empty_path = _write_config(tmp_path, {})
    times_commands.classes_list(None, str(empty_path))
    assert "No class patterns found" in capsys.readouterr().out


def test_classes_remove_reprompts_and_persists_selection(tmp_path, monkeypatch, capsys):
    # Verifies removing a class pattern rejects out-of-range choices before success.
    path = _write_config(
        tmp_path,
        {"time_slot_config": {"classes": [{"credits": 3}, {"credits": 4}]}},
    )
    responses = iter(["0", "2"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(responses))

    times_commands.classes_remove(None, str(path))

    assert json.loads(path.read_text(encoding="utf-8"))["time_slot_config"]["classes"] == [
        {"credits": 3}
    ]
    assert "Invalid input" in capsys.readouterr().out


def test_classes_update_replaces_meetings_and_handles_empty_states(
    tmp_path, monkeypatch, capsys
):
    # Verifies class updates validate inputs, replace meetings, and report empty state.
    path = _write_config(
        tmp_path,
        {
            "time_slot_config": {
                "classes": [
                    {
                        "credits": 3,
                        "start_time": "08:00",
                        "disabled": False,
                        "meetings": [],
                    }
                ]
            }
        },
    )
    responses = iter(
        [
            "0",
            "1",
            "0",
            "4",
            "bad",
            "null",
            "y",
            "y",
            "y",
            "tue",
            "90",
            "online",
            "n",
            "null",
            "n",
        ]
    )
    monkeypatch.setattr("builtins.input", lambda prompt="": next(responses))

    times_commands.classes_update(None, str(path))

    updated = json.loads(path.read_text(encoding="utf-8"))["time_slot_config"]["classes"][0]
    assert updated["credits"] == 4
    assert updated["start_time"] is None
    assert updated["disabled"] is True
    assert updated["meetings"] == [
        {"day": "TUE", "duration": 90, "delivery": "online", "lab": False}
    ]
    assert "Invalid input" in capsys.readouterr().out

    empty_path = _write_config(tmp_path, {})
    times_commands.classes_remove(None, str(empty_path))
    times_commands.classes_update(None, str(empty_path))
    output = capsys.readouterr().out
    assert "No class patterns available to remove" in output
    assert "No class patterns available to update" in output


def test_time_and_class_handlers_dispatch_supported_commands(
    tmp_path, monkeypatch, capsys
):
    # Verifies both handlers dispatch every supported command and report invalid usage.
    called = []
    for command in ("list", "update"):
        monkeypatch.setattr(
            times_commands,
            f"times_{command}",
            lambda shell, filename, op=command: called.append(("times", op, filename)),
        )
    for command in ("add", "list", "remove", "update"):
        monkeypatch.setattr(
            times_commands,
            f"classes_{command}",
            lambda shell, filename, op=command: called.append(("classes", op, filename)),
        )

    times_commands.times_handler(None, "list config.json")
    times_commands.times_handler(None, "update config.json")
    times_commands.classes_handler(None, "add config.json")
    times_commands.classes_handler(None, "list config.json")
    times_commands.classes_handler(None, "remove config.json")
    times_commands.classes_handler(None, "update config.json")
    times_commands.times_handler(None, "")
    times_commands.classes_handler(None, "")
    output = capsys.readouterr().out
    assert "Usage: times" in output
    assert "Usage: classes" in output

    times_commands.times_handler(None, "unknown config.json")
    times_commands.classes_handler(None, "unknown config.json")
    output = capsys.readouterr().out
    assert "Invalid command. Usage: times" in output
    assert "Invalid command. Usage: classes" in output
    assert len(called) == 6


def test_class_commands_handle_missing_filename_and_skip_meetings(
    tmp_path, monkeypatch, capsys
):
    # Verifies missing-file requests and no-meeting class patterns are handled.
    times_commands.classes_add(None, None)
    times_commands.classes_list(None, None)
    times_commands.classes_remove(None, None)
    times_commands.classes_update(None, None)
    path = _write_config(tmp_path, {})
    responses = iter(["2", "null", "n", "n"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(responses))
    times_commands.classes_add(None, str(path))

    saved = json.loads(path.read_text(encoding="utf-8"))["time_slot_config"]["classes"][0]
    assert saved == {"credits": 2, "meetings": [], "disabled": False}
    assert capsys.readouterr().out.count("No configuration file selected") == 4


def test_time_prompt_defaults_and_file_errors(tmp_path, monkeypatch, capsys):
    # Verifies blank defaults and read failures for all time and class operations.
    monkeypatch.setattr("builtins.input", lambda prompt="": "")
    assert times_commands._prompt_input("optional", lambda value: value, default=[]) == []

    times_commands.times_update(None, None)
    times_commands.times_list(None, str(_write_config(tmp_path, {})))
    bad_path = tmp_path / "bad_times.json"
    bad_path.write_text("{broken", encoding="utf-8")

    times_commands.times_list(None, str(bad_path))
    times_commands.classes_add(None, str(bad_path))
    times_commands.classes_list(None, str(bad_path))
    times_commands.classes_remove(None, str(bad_path))
    times_commands.classes_update(None, str(bad_path))

    output = capsys.readouterr().out
    assert "No configuration file selected" in output
    assert "List failed" in output
    assert "Failed to add class pattern" in output
    assert "Remove failed" in output
    assert "Update failed" in output
