import json

import pytest

import config_commands


ROOM = ("R1", 30, ["projector"], None)
LAB = ("L1", 20, ["computers"], None)
COURSE = ("CS101", 4, 30, ["R1"], ["L1"], [], ["F1"], None, None, None, None, None)
FACULTY = ("F1", 4, 4, 1, None, None, None, None, None, None)


@pytest.mark.parametrize(
    "add, modify, delete, record",
    [
        (config_commands.room_add, config_commands.room_modify, config_commands.room_delete, ROOM),
        (config_commands.lab_add, config_commands.lab_modify, config_commands.lab_delete, LAB),
        (config_commands.course_add, config_commands.course_modify, config_commands.course_delete, COURSE),
        (config_commands.faculty_add, config_commands.faculty_modify, config_commands.faculty_delete, FACULTY),
    ],
)
def test_config_record_commands_add_modify_and_delete(add, modify, delete, record):
    # Verifies each public command wrapper applies its action to the expected section.
    config = {}

    added, success = add(config, record)
    assert success is True
    assert added[next(iter(added))] == [list(record)]
    assert config == {}

    replacement = (*record[:1], *record[1:-1], "updated")
    modified, success = modify(added, replacement)
    assert success is True
    assert modified[next(iter(modified))] == [list(replacement)]

    deleted, success = delete(modified, replacement)
    assert success is True
    assert deleted[next(iter(deleted))] == []


def test_command_skeleton_persists_successful_file_update(tmp_path):
    # Verifies a successful path-based operation updates the JSON file on disk.
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"rooms": []}), encoding="utf-8")

    result, success = config_commands.room_add(str(path), ROOM)

    assert success is True
    assert result["rooms"] == [list(ROOM)]
    assert json.loads(path.read_text(encoding="utf-8")) == result


@pytest.mark.parametrize(
    "values",
    [
        ["R1", 30, [], None],
        ("R1", 30, []),
        ("R1", 30, [], None, "extra"),
    ],
)
def test_command_skeleton_rejects_values_with_wrong_shape(values):
    # Verifies malformed records are rejected without mutating the input config.
    config = {"rooms": []}

    result, success = config_commands._command_skeleton(
        config, values, 4, "rooms", "add"
    )

    assert success is False
    assert result == config
    assert result is not config


@pytest.mark.parametrize(
    "config, values, action",
    [
        ({"rooms": [["R1", 10, [], None]]}, ROOM, "add"),
        ({"rooms": []}, ROOM, "modify"),
        ({"rooms": []}, ROOM, "delete"),
        ({"rooms": "not-a-list"}, ROOM, "add"),
        (["not", "an", "object"], ROOM, "add"),
    ],
)
def test_command_skeleton_rejects_duplicate_missing_or_invalid_records(
    config, values, action
):
    # Verifies invalid targets or section shapes fail without changing caller data.
    original = json.loads(json.dumps(config))

    result, success = config_commands._command_skeleton(
        config, values, 4, "rooms", action
    )

    assert success is False
    assert result == original
    assert config == original


@pytest.mark.parametrize("action", ["modify", "delete"])
def test_command_skeleton_uses_first_record_value_as_identifier(action):
    # Verifies matching records are found by their identifier even among malformed entries.
    config = {"rooms": [None, [], ["R1", 10, [], None], ["R2", 20, [], None]]}

    result, success = config_commands._command_skeleton(
        config, ROOM, 4, "rooms", action
    )

    assert success is True
    if action == "modify":
        assert result["rooms"][2] == list(ROOM)
    else:
        assert result["rooms"] == [None, [], ["R2", 20, [], None]]


@pytest.mark.parametrize(
    "file_content, values",
    [
        ("{invalid json", ROOM),
        ("{}", ["R1", 30, [], None]),
    ],
)
def test_command_skeleton_returns_failure_for_unreadable_or_unwritable_input(
    tmp_path, file_content, values
):
    # Verifies read and persistence errors return failure without reporting success.
    path = tmp_path / "config.json"
    path.write_text(file_content, encoding="utf-8")

    result, success = config_commands.room_add(str(path), values)

    assert success is False
    assert result == str(path)


def test_command_skeleton_rejects_unknown_action_without_persisting():
    # Verifies unsupported actions follow the existing delete-not-found failure path.
    config = {"rooms": []}

    result, success = config_commands._command_skeleton(
        config, ROOM, 4, "rooms", "unsupported"
    )

    assert success is False
    assert result == config
