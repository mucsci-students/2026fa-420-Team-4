import json

import pytest

import course_commands


def _write_config(tmp_path, courses):
    path = tmp_path / "courses.json"
    path.write_text(json.dumps({"config": {"courses": courses}}), encoding="utf-8")
    return path


def _course(course_id="CS101", section_id="A", modality="in_person"):
    return {
        "course_id": course_id,
        "section_id": section_id,
        "credits": 4,
        "capacity": 30,
        "modality": modality,
        "room": ["R1"],
        "lab": ["L1"],
        "required_room_features": ["projector"],
        "required_lab_features": ["computers"],
        "reserve_room_during_lab": True,
        "conflicts": ["CS202"],
        "faculty": ["F1"],
    }


def test_course_helpers_validate_required_strings_numbers_and_lists():
    # Verifies helper functions accept valid values and reject invalid list contents.
    assert course_commands._clean_str("CS101") == "CS101"
    assert course_commands._clean_str("", allow_empty=True) == ""
    assert course_commands._parse_int("1") == 1
    assert course_commands._parse_list("R1, L1") == ["R1", "L1"]
    assert course_commands._parse_list("", allow_empty=True) == []
    with pytest.raises(ValueError):
        course_commands._clean_str("")
    with pytest.raises(ValueError):
        course_commands._parse_int("0")
    with pytest.raises(ValueError):
        course_commands._parse_list("R1, R1")
    with pytest.raises(ValueError):
        course_commands._parse_list(", ,", allow_empty=False)
    with pytest.raises(ValueError):
        course_commands._parse_list("", allow_empty=False)
    with pytest.raises(ValueError):
        course_commands._parse_list("CS101", exclude_item="CS101")


def test_course_add_online_reprompts_and_forces_empty_resources(
    tmp_path, monkeypatch, capsys
):
    # Verifies online courses bypass resource prompts and retry invalid required values.
    path = _write_config(tmp_path, [])
    responses = iter(
        [
            "",
            "CS101",
            "",
            "0",
            "4",
            "bad",
            "30",
            "virtual",
            "online",
            "projector",
            "",
            "n",
            "CS101",
            "CS202, CS203",
            "null",
        ]
    )
    monkeypatch.setattr("builtins.input", lambda prompt="": next(responses))

    course_commands.course_add(None, str(path))

    added = json.loads(path.read_text(encoding="utf-8"))["config"]["courses"][0]
    assert added == {
        "course_id": "CS101",
        "section_id": None,
        "credits": 4,
        "capacity": 30,
        "modality": "online",
        "room": [],
        "lab": [],
        "required_room_features": ["projector"],
        "required_lab_features": [],
        "reserve_room_during_lab": False,
        "conflicts": ["CS202", "CS203"],
        "faculty": None,
    }
    assert capsys.readouterr().out.count("Invalid input") == 5


def test_course_add_in_person_stores_resources_defaults_and_faculty(
    tmp_path, monkeypatch
):
    # Verifies non-online courses can define rooms, labs, and faculty candidates.
    path = tmp_path / "empty.json"
    path.write_text("{}", encoding="utf-8")
    responses = iter(
        [
            "CS201",
            "02",
            "3",
            "20",
            "in_person",
            "R1, R2",
            "L1",
            "",
            "",
            "",
            "",
            "F1, F2",
        ]
    )
    monkeypatch.setattr("builtins.input", lambda prompt="": next(responses))

    course_commands.course_add(None, str(path))

    added = json.loads(path.read_text(encoding="utf-8"))["config"]["courses"][0]
    assert added["course_id"] == "CS201"
    assert added["section_id"] == "02"
    assert added["room"] == ["R1", "R2"]
    assert added["lab"] == ["L1"]
    assert added["reserve_room_during_lab"] is True
    assert added["faculty"] == ["F1", "F2"]


def test_course_list_shows_optional_values_and_empty_state(tmp_path, capsys):
    # Verifies course listing formats sections and handles missing or derived values.
    path = _write_config(
        tmp_path,
        [
            _course(),
            {
                "course_id": "CS202",
                "section_id": None,
                "room": [],
                "lab": [],
                "faculty": None,
            },
        ],
    )
    course_commands.course_list(None, str(path))
    output = capsys.readouterr().out
    assert "CS101.A" in output
    assert "Modality: in_person" in output
    assert "Faculty: F1" in output
    assert "CS202 | Modality: N/A" in output
    assert "Faculty: Derived (null)" in output

    empty_path = _write_config(tmp_path, [])
    course_commands.course_list(None, str(empty_path))
    assert "No courses found" in capsys.readouterr().out
    course_commands.course_list(None, None)
    assert "No configuration file selected" in capsys.readouterr().out


def test_course_remove_selects_duplicate_section_and_reprompts(
    tmp_path, monkeypatch, capsys
):
    # Verifies missing IDs and invalid duplicate selection are rejected before deletion.
    path = _write_config(tmp_path, [_course(section_id="A"), _course(section_id="B")])
    responses = iter(["missing", "CS101", "0", "2"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(responses))

    course_commands.course_remove(None, str(path))

    remaining = json.loads(path.read_text(encoding="utf-8"))["config"]["courses"]
    assert [entry["section_id"] for entry in remaining] == ["A"]
    assert "Invalid input" in capsys.readouterr().out


def test_course_remove_handles_empty_and_single_match(tmp_path, monkeypatch, capsys):
    # Verifies empty collections and a single unambiguous match need no index selection.
    empty_path = _write_config(tmp_path, [])
    course_commands.course_remove(None, str(empty_path))
    assert "No courses available to remove" in capsys.readouterr().out

    path = _write_config(tmp_path, [_course()])
    monkeypatch.setattr("builtins.input", lambda prompt="": "CS101")
    course_commands.course_remove(None, str(path))
    assert json.loads(path.read_text(encoding="utf-8"))["config"]["courses"] == []


def test_course_update_online_reprompts_and_clears_resource_assignments(
    tmp_path, monkeypatch, capsys
):
    # Verifies an update can switch a duplicate course to online and validate conflicts.
    path = _write_config(tmp_path, [_course(section_id="A"), _course(section_id="B")])
    responses = iter(
        [
            "missing",
            "CS101",
            "0",
            "2",
            "CS102",
            "null",
            "0",
            "5",
            "40",
            "hybrid?",
            "online",
            "projector",
            "",
            "n",
            "CS102",
            "CS303",
            "null",
        ]
    )
    monkeypatch.setattr("builtins.input", lambda prompt="": next(responses))

    course_commands.course_update(None, str(path))

    updated = json.loads(path.read_text(encoding="utf-8"))["config"]["courses"][1]
    assert updated["course_id"] == "CS102"
    assert updated["section_id"] is None
    assert updated["credits"] == 5
    assert updated["capacity"] == 40
    assert updated["modality"] == "online"
    assert updated["room"] == []
    assert updated["lab"] == []
    assert updated["reserve_room_during_lab"] is False
    assert updated["conflicts"] == ["CS303"]
    assert updated["faculty"] is None
    assert capsys.readouterr().out.count("Invalid input") >= 5


def test_course_update_non_online_fields_and_empty_state(tmp_path, monkeypatch):
    # Verifies non-online updates persist resource lists and can retain omitted values.
    path = _write_config(tmp_path, [_course(modality="hybrid")])
    responses = iter(
        [
            "CS101",
            "CS201",
            "A",
            "3",
            "25",
            "hybrid",
            "R2",
            "L2",
            "screen",
            "gpu",
            "y",
            "CS202",
            "F2",
        ]
    )
    monkeypatch.setattr("builtins.input", lambda prompt="": next(responses))

    course_commands.course_update(None, str(path))

    updated = json.loads(path.read_text(encoding="utf-8"))["config"]["courses"][0]
    assert updated["course_id"] == "CS201"
    assert updated["section_id"] == "A"
    assert updated["modality"] == "hybrid"
    assert updated["room"] == ["R2"]
    assert updated["lab"] == ["L2"]
    assert updated["required_room_features"] == ["screen"]
    assert updated["required_lab_features"] == ["gpu"]
    assert updated["conflicts"] == ["CS202"]
    assert updated["faculty"] == ["F2"]

    empty_path = _write_config(tmp_path, [])
    course_commands.course_update(None, str(empty_path))


def test_course_commands_handle_missing_filename_and_dispatch(
    monkeypatch, capsys
):
    # Verifies command handlers report missing filenames and dispatch supported actions.
    course_commands.course_add(None, None)
    course_commands.course_list(None, None)
    course_commands.course_remove(None, None)
    course_commands.course_update(None, None)
    assert capsys.readouterr().out.count("No configuration file selected") == 4

    dispatched = []
    for command in ("add", "list", "remove", "update"):
        monkeypatch.setattr(
            course_commands,
            f"course_{command}",
            lambda shell, filename, op=command: dispatched.append((op, filename)),
        )

    course_commands.course_handler(None, "ADD config.json")
    course_commands.course_handler(None, "list config.json")
    course_commands.course_handler(None, "remove config.json")
    course_commands.course_handler(None, "update config.json")
    course_commands.course_handler(None, "")
    output = capsys.readouterr().out
    assert "Usage: course" in output

    course_commands.course_handler(None, "unknown config.json")
    assert "Invalid command" in capsys.readouterr().out
    assert dispatched == [(command, "config.json") for command in ("add", "list", "remove", "update")]


def test_course_commands_report_file_errors(tmp_path, capsys):
    # Verifies every file-based course operation reports malformed or missing files.
    bad_path = tmp_path / "bad.json"
    bad_path.write_text("{bad json", encoding="utf-8")
    missing_path = tmp_path / "missing.json"

    course_commands.course_add(None, str(missing_path))
    course_commands.course_add(None, str(bad_path))
    course_commands.course_list(None, str(bad_path))
    course_commands.course_remove(None, str(bad_path))
    course_commands.course_update(None, str(bad_path))

    output = capsys.readouterr().out
    assert "Failed to add course due to system error" in output
    assert "List failed" in output
    assert "Remove failed" in output
    assert "Update failed" in output
