import json

import pytest

import faculty_commands


def _write_config(tmp_path, faculty):
    path = tmp_path / "faculty.json"
    path.write_text(json.dumps({"config": {"faculty": faculty}}), encoding="utf-8")
    return path


def _faculty(name="F1"):
    return {
        "name": name,
        "minimum_credits": 4,
        "maximum_credits": 8,
        "unique_course_limit": 2,
        "maximum_days": 2,
        "mandatory_days": ["MON"],
        "times": {"MON": [{"start": "08:00", "end": "17:00"}]},
        "course_preferences": {"CS101": 5},
        "room_preferences": {},
        "lab_preferences": {},
    }


def test_faculty_helpers_validate_strings_numbers_and_time_ranges():
    # Verifies helper validation accepts valid values and rejects malformed input.
    assert faculty_commands._clean_str(" Faculty ") == " Faculty "
    assert faculty_commands._clean_str(None, allow_empty=True) is None
    assert faculty_commands._parse_int("0", min_value=0) == 0
    assert faculty_commands._parse_int("5", min_value=0, max_value=5) == 5
    assert faculty_commands._parse_time_range("08:00-12:30") == {
        "start": "08:00",
        "end": "12:30",
    }
    assert faculty_commands._parse_time_range("00:00-23:59") == {
        "start": "00:00",
        "end": "23:59",
    }
    with pytest.raises(ValueError):
        faculty_commands._clean_str("")
    with pytest.raises(ValueError):
        faculty_commands._parse_int("-1", min_value=0)
    with pytest.raises(ValueError):
        faculty_commands._parse_int("6", min_value=0, max_value=5)
    with pytest.raises(ValueError):
        faculty_commands._parse_time_range("09:00")
    with pytest.raises(ValueError):
        faculty_commands._parse_time_range("24:00-25:00")
    with pytest.raises(ValueError):
        faculty_commands._parse_time_range("12:00-11:00")


def test_faculty_time_and_preference_prompts_reprompt_after_invalid_entries(
    monkeypatch, capsys
):
    # Verifies daily availability and preference prompt validators reject bad values.
    responses = iter(["bad-range", "08:00-12:00", "", "", "", "", "bad", "CS101:11", "CS101:10"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(responses))

    times = faculty_commands._prompt_times_dict()
    preferences = faculty_commands._prompt_preferences_dict("Course")

    assert times == {"MON": [{"start": "08:00", "end": "12:00"}]}
    assert preferences == {"CS101": 10}
    assert capsys.readouterr().out.count("Invalid input") == 3


def test_faculty_prompt_helpers_validate_empty_days_and_preference_keys(
    monkeypatch, capsys
):
    # Verifies empty prompt validators and blank preference keys have explicit behavior.
    original_prompt = faculty_commands._prompt_input

    def invoke_empty_validators(prompt_text, validator_func, default=None):
        if prompt_text.startswith("Availability"):
            assert validator_func("") == []
            return []
        if prompt_text.startswith("Course preferences"):
            assert validator_func("") == {}
            return {}
        return original_prompt(prompt_text, validator_func, default)

    monkeypatch.setattr(faculty_commands, "_prompt_input", invoke_empty_validators)
    assert faculty_commands._prompt_times_dict() == {}
    assert faculty_commands._prompt_preferences_dict("Course") == {}

    monkeypatch.setattr(faculty_commands, "_prompt_input", original_prompt)
    responses = iter([":5", "CS101:5"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(responses))
    assert faculty_commands._prompt_preferences_dict("Room") == {"CS101": 5}
    assert "Invalid input" in capsys.readouterr().out


def test_faculty_add_persists_valid_member_after_retrying_invalid_fields(
    tmp_path, monkeypatch, capsys
):
    # Verifies faculty creation validates credit bounds, days, availability, and preferences.
    path = _write_config(tmp_path, [])
    responses = iter(
        [
            "Dr New",
            "4",
            "2",
            "6",
            "3",
            "08:00-12:00",
            "",
            "",
            "",
            "",
            "SAT",
            "MON,MON",
            "TUE",
            "MON",
            "0",
            "1",
            "bad",
            "CS101:11",
            "CS101:9",
            "",
            "L1:0",
        ]
    )
    monkeypatch.setattr("builtins.input", lambda prompt="": next(responses))

    faculty_commands.faculty_add(None, str(path))

    added = json.loads(path.read_text(encoding="utf-8"))["config"]["faculty"][0]
    assert added["name"] == "Dr New"
    assert added["minimum_credits"] == 4
    assert added["maximum_credits"] == 6
    assert added["unique_course_limit"] == 3
    assert added["times"] == {"MON": [{"start": "08:00", "end": "12:00"}]}
    assert added["mandatory_days"] == ["MON"]
    assert added["maximum_days"] == 1
    assert added["course_preferences"] == {"CS101": 9}
    assert added["room_preferences"] == {}
    assert added["lab_preferences"] == {"L1": 0}
    assert capsys.readouterr().out.count("Invalid input") == 7


def test_faculty_add_rejects_duplicate_name_and_handles_missing_filename(
    tmp_path, monkeypatch, capsys
):
    # Verifies duplicate names trigger a retry and missing filenames are reported.
    path = _write_config(tmp_path, [_faculty("F1")])
    responses = iter(
        ["f1", "F2", "0", "1", "0", "", "", "", "", "", "", "", "", "", ""]
    )
    monkeypatch.setattr("builtins.input", lambda prompt="": next(responses))

    faculty_commands.faculty_add(None, str(path))
    faculty_commands.faculty_add(None, None)

    faculty = json.loads(path.read_text(encoding="utf-8"))["config"]["faculty"]
    assert [member["name"] for member in faculty] == ["F1", "F2"]
    output = capsys.readouterr().out
    assert "already exists" in output
    assert "No configuration file selected" in output


def test_faculty_list_displays_members_defaults_and_empty_state(tmp_path, capsys):
    # Verifies faculty listing formats configured values and reports an empty collection.
    path = _write_config(tmp_path, [_faculty(), {}])
    faculty_commands.faculty_list(None, str(path))
    output = capsys.readouterr().out
    assert "F1" in output
    assert "Credits: 4-8" in output
    assert "Mandatory: [MON]" in output
    assert "N/A" in output
    assert "Days Available: [None]" in output

    empty_path = _write_config(tmp_path, [])
    faculty_commands.faculty_list(None, str(empty_path))
    assert "No faculty found" in capsys.readouterr().out
    faculty_commands.faculty_list(None, None)
    assert "No configuration file selected" in capsys.readouterr().out


def test_faculty_remove_reprompts_and_warns_when_removing_last_member(
    tmp_path, monkeypatch, capsys
):
    # Verifies matching is case-insensitive and removing the last policy warns the user.
    path = _write_config(tmp_path, [_faculty()])
    responses = iter(["missing", "f1"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(responses))

    faculty_commands.faculty_remove(None, str(path))

    assert json.loads(path.read_text(encoding="utf-8"))["config"]["faculty"] == []
    output = capsys.readouterr().out
    assert "Invalid input" in output
    assert "requires at least one faculty policy" in output


def test_faculty_update_changes_settings_with_invalid_intermediate_responses(
    tmp_path, monkeypatch, capsys
):
    # Verifies update re-prompts invalid values and can replace times and preferences.
    path = _write_config(tmp_path, [_faculty(), _faculty("Other")])
    responses = iter(
        [
            "missing",
            "F1",
            "Other",
            "F1 New",
            "5",
            "3",
            "7",
            "0",
            "y",
            "08:00-17:00",
            "",
            "",
            "",
            "",
            "SAT",
            "MON,MON",
            "TUE",
            "MON",
            "0",
            "6",
            "1",
            "y",
            "CS101:8",
            "",
            "L1:12",
            "L1:7",
        ]
    )
    monkeypatch.setattr("builtins.input", lambda prompt="": next(responses))

    faculty_commands.faculty_update(None, str(path))

    updated = json.loads(path.read_text(encoding="utf-8"))["config"]["faculty"][0]
    assert updated["name"] == "F1 New"
    assert updated["minimum_credits"] == 5
    assert updated["maximum_credits"] == 7
    assert updated["unique_course_limit"] == 0
    assert updated["mandatory_days"] == ["MON"]
    assert updated["maximum_days"] == 1
    assert updated["course_preferences"] == {"CS101": 8}
    assert updated["room_preferences"] == {}
    assert updated["lab_preferences"] == {"L1": 7}
    assert capsys.readouterr().out.count("Invalid input") >= 7


def test_faculty_update_keeps_existing_values_when_prompts_are_skipped(
    tmp_path, monkeypatch
):
    # Verifies pressing Enter and declining optional changes retains existing settings.
    original = _faculty()
    path = _write_config(tmp_path, [original])
    responses = iter(["F1", "", "", "", "", "n", "", "", "n"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(responses))
    original_prompt = faculty_commands._prompt_input

    def invoke_empty_mandatory_validator(prompt_text, validator_func, default=None):
        if prompt_text.startswith("Mandatory Days"):
            assert validator_func("") == []
        return original_prompt(prompt_text, validator_func, default)

    monkeypatch.setattr(
        faculty_commands, "_prompt_input", invoke_empty_mandatory_validator
    )

    faculty_commands.faculty_update(None, str(path))

    saved = json.loads(path.read_text(encoding="utf-8"))["config"]["faculty"][0]
    assert saved == original


def test_faculty_add_initializes_missing_section_and_reports_file_errors(
    tmp_path, monkeypatch, capsys
):
    # Verifies adding initializes a missing faculty section and catches file failures.
    path = tmp_path / "new_config.json"
    path.write_text(json.dumps({"config": {}}), encoding="utf-8")
    responses = iter(["Dr Empty", "0", "0", "0"] + [""] * 10)
    monkeypatch.setattr("builtins.input", lambda prompt="": next(responses))
    original_prompt = faculty_commands._prompt_input

    def invoke_empty_mandatory_validator(prompt_text, validator_func, default=None):
        if prompt_text.startswith("Enter mandatory days"):
            assert validator_func("") == []
        return original_prompt(prompt_text, validator_func, default)

    monkeypatch.setattr(
        faculty_commands, "_prompt_input", invoke_empty_mandatory_validator
    )
    faculty_commands.faculty_add(None, str(path))
    assert json.loads(path.read_text(encoding="utf-8"))["config"]["faculty"][0][
        "name"
    ] == "Dr Empty"

    bad_path = tmp_path / "bad.json"
    bad_path.write_text("{bad", encoding="utf-8")
    faculty_commands.faculty_add(None, str(bad_path))
    faculty_commands.faculty_list(None, None)
    faculty_commands.faculty_list(None, str(bad_path))
    faculty_commands.faculty_remove(None, None)
    faculty_commands.faculty_remove(None, str(bad_path))
    faculty_commands.faculty_update(None, None)
    faculty_commands.faculty_update(None, str(bad_path))

    output = capsys.readouterr().out
    assert "Failed to add faculty" in output
    assert "List failed" in output
    assert "Remove failed" in output
    assert "Update failed" in output
    assert output.count("No configuration file selected") == 3


def test_faculty_commands_handle_empty_states_and_dispatch(
    tmp_path, monkeypatch, capsys
):
    # Verifies empty update/remove states, handler usage, and all handler operations.
    path = _write_config(tmp_path, [])
    faculty_commands.faculty_remove(None, str(path))
    faculty_commands.faculty_update(None, str(path))
    output = capsys.readouterr().out
    assert "No faculty available to remove" in output
    assert "No faculty available to update" in output

    dispatched = []
    for command in ("add", "list", "remove", "update"):
        monkeypatch.setattr(
            faculty_commands,
            f"faculty_{command}",
            lambda shell, filename, op=command: dispatched.append((op, filename)),
        )

    faculty_commands.faculty_handler(None, "ADD file.json")
    faculty_commands.faculty_handler(None, "list file.json")
    faculty_commands.faculty_handler(None, "remove file.json")
    faculty_commands.faculty_handler(None, "update file.json")
    faculty_commands.faculty_handler(None, "")
    assert "Usage:" in capsys.readouterr().out

    faculty_commands.faculty_handler(None, "unknown file.json")
    assert "Invalid command" in capsys.readouterr().out
    assert dispatched == [(command, "file.json") for command in ("add", "list", "remove", "update")]
