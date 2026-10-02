import json

import pytest

import lab_commands
import room_commands


def test_clean_str_accepts_valid_value():
    # Verifies a non-empty string is returned unchanged.
    assert room_commands._clean_str("Room 101") == "Room 101"


@pytest.mark.parametrize(
    "value, allow_empty, expected",
    [
        ("   ", False, ValueError),
        ("", False, ValueError),
        (None, False, ValueError),
        ("", True, ""),
        (None, True, None),
    ],
)
def test_clean_str_rejects_blank_and_null_values(value, allow_empty, expected):
    # Verifies blank and null values are rejected unless empty strings are explicitly allowed.
    if expected is ValueError:
        with pytest.raises(ValueError):
            room_commands._clean_str(value, allow_empty=allow_empty)
    else:
        assert room_commands._clean_str(value, allow_empty=allow_empty) == expected


def test_parse_int_accepts_valid_positive_values_and_lower_bound():
    # Verifies normal positive integers and the minimum valid boundary are accepted.
    assert room_commands._parse_int("12") == 12
    assert room_commands._parse_int("1", min_value=1) == 1


@pytest.mark.parametrize(
    "value, min_value, exc",
    [("0", 1, ValueError), ("-5", 1, ValueError), ("abc", 1, ValueError), (None, 1, TypeError)],
)
def test_parse_int_rejects_invalid_numbers_and_types(value, min_value, exc):
    # Verifies invalid numeric values and wrong data types raise errors instead of being accepted.
    with pytest.raises(exc):
        room_commands._parse_int(value, min_value=min_value)


def test_parse_list_parses_valid_features_and_rejects_duplicates():
    # Verifies comma-separated features are normalized and duplicates are rejected.
    assert room_commands._parse_list("projector, whiteboard") == ["projector", "whiteboard"]
    with pytest.raises(ValueError):
        room_commands._parse_list("projector, projector")


@pytest.mark.parametrize(
    "value, allow_empty, expected",
    [
        ("", True, []),
        (None, True, []),
        ("", False, ValueError),
        (None, False, ValueError),
    ],
)
def test_parse_list_handles_empty_and_null_input(value, allow_empty, expected):
    # Verifies empty input is accepted only when explicitly permitted.
    if expected is ValueError:
        with pytest.raises(ValueError):
            room_commands._parse_list(value, allow_empty=allow_empty)
    else:
        assert room_commands._parse_list(value, allow_empty=allow_empty) == expected


@pytest.mark.parametrize(
    "value, expected",
    [
        ("08:00-12:00", {"start": "08:00", "end": "12:00"}),
        ("00:00-23:59", {"start": "00:00", "end": "23:59"}),
    ],
)
def test_parse_time_range_accepts_valid_windows(value, expected):
    # Verifies valid time ranges are parsed into start and end values.
    assert room_commands._parse_time_range(value) == expected


@pytest.mark.parametrize(
    "value, exc",
    [("12:00", ValueError), ("25:00-12:00", ValueError), ("09:00-09:00", ValueError), ("09:00-08:00", ValueError)],
)
def test_parse_time_range_rejects_invalid_syntax_and_boundaries(value, exc):
    # Verifies malformed and non-increasing time windows fail validation.
    with pytest.raises(exc):
        room_commands._parse_time_range(value)


def test_prompt_room_times_returns_none_when_unrestricted(monkeypatch):
    # Verifies unrestricted rooms return None without prompting for daily ranges.
    responses = iter(["n"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(responses))

    assert room_commands._prompt_room_times() is None


def test_prompt_room_times_returns_restricted_windows_for_active_days(monkeypatch):
    # Verifies restricted rooms store time windows for specific weekdays.
    responses = iter(["y", "08:00-12:00", "", "", "", "", ""])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(responses))

    result = room_commands._prompt_room_times()
    assert result == {"MON": [{"start": "08:00", "end": "12:00"}]}


def test_room_add_creates_a_room_and_persists_json(tmp_path, monkeypatch):
    # Verifies a valid room request is added to the configured room list.
    file_path = tmp_path / "rooms.json"
    file_path.write_text(json.dumps({"config": {"rooms": []}}))

    responses = iter(["Room 101", "12", "projector, whiteboard", "n"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(responses))

    room_commands.room_add(None, str(file_path))

    data = json.loads(file_path.read_text())
    assert data["config"]["rooms"][0]["name"] == "Room 101"
    assert data["config"]["rooms"][0]["capacity"] == 12
    assert data["config"]["rooms"][0]["features"] == ["projector", "whiteboard"]
    assert data["config"]["rooms"][0]["times"] is None


def test_room_add_handles_missing_filename_and_invalid_json(tmp_path, capsys):
    # Verifies null file selection and malformed JSON are reported as handled errors.
    room_commands.room_add(None, None)
    out = capsys.readouterr().out
    assert "No configuration file selected." in out

    bad_file = tmp_path / "bad.json"
    bad_file.write_text("{not-valid-json}")
    room_commands.room_add(None, str(bad_file))
    out = capsys.readouterr().out
    assert "Failed to add room:" in out


def test_room_list_prints_rooms_and_reports_empty_config(tmp_path, capsys):
    # Verifies the room list output includes rooms and the empty-state message when no rooms exist.
    room_file = tmp_path / "rooms.json"
    room_file.write_text(json.dumps({"config": {"rooms": [{"name": "Room A", "capacity": 20, "features": ["projector"], "times": None}]}}))

    room_commands.room_list(None, str(room_file))
    out = capsys.readouterr().out
    assert "Room A" in out
    assert "Capacity: 20" in out
    assert "Unrestricted (null)" in out

    room_file.write_text(json.dumps({"config": {"rooms": []}}))
    room_commands.room_list(None, str(room_file))
    out = capsys.readouterr().out
    assert "No rooms found in configuration." in out


def test_room_remove_deletes_matching_room_and_handles_empty_or_missing_names(tmp_path, monkeypatch, capsys):
    # Verifies removing an existing room works, and empty configs or bad names are rejected safely.
    room_file = tmp_path / "rooms.json"
    room_file.write_text(json.dumps({"config": {"rooms": [{"name": "Room A", "capacity": 10, "features": [], "times": None}, {"name": "Room B", "capacity": 8, "features": [], "times": None}]}}))

    responses = iter(["Room A"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(responses))
    room_commands.room_remove(None, str(room_file))
    data = json.loads(room_file.read_text())
    assert [room["name"] for room in data["config"]["rooms"]] == ["Room B"]

    room_file.write_text(json.dumps({"config": {"rooms": []}}))
    room_commands.room_remove(None, str(room_file))
    out = capsys.readouterr().out
    assert "No rooms available to remove." in out


def test_room_update_changes_fields_and_handles_missing_room_names(tmp_path, monkeypatch, capsys):
    # Verifies updating a room changes its fields and that unknown room names fail gracefully.
    room_file = tmp_path / "rooms.json"
    room_file.write_text(json.dumps({"config": {"rooms": [{"name": "Room A", "capacity": 10, "features": ["whiteboard"], "times": None}]}}))

    responses = iter(["Room A", "Room B", "25", "projector, screen", "n"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(responses))
    room_commands.room_update(None, str(room_file))
    data = json.loads(room_file.read_text())
    assert data["config"]["rooms"][0]["name"] == "Room B"
    assert data["config"]["rooms"][0]["capacity"] == 25
    assert data["config"]["rooms"][0]["features"] == ["projector", "screen"]

    room_file.write_text(json.dumps({"config": {"rooms": [{"name": "Room A", "capacity": 10, "features": [], "times": None}]}}))
    responses = iter(["Missing Room"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(responses))
    room_commands.room_update(None, str(room_file))
    out = capsys.readouterr().out
    assert "Update failed:" in out


def test_room_handler_routes_valid_commands_and_rejects_bad_usage(monkeypatch):
    # Verifies the command router calls the correct room action and rejects malformed usage.
    calls = []

    def fake_room_add(shell, filename):
        calls.append(("add", shell, filename))

    def fake_room_list(shell, filename):
        calls.append(("list", shell, filename))

    def fake_room_remove(shell, filename):
        calls.append(("remove", shell, filename))

    def fake_room_update(shell, filename):
        calls.append(("update", shell, filename))

    monkeypatch.setattr(room_commands, "room_add", fake_room_add)
    monkeypatch.setattr(room_commands, "room_list", fake_room_list)
    monkeypatch.setattr(room_commands, "room_remove", fake_room_remove)
    monkeypatch.setattr(room_commands, "room_update", fake_room_update)

    room_commands.room_handler("shell", "add rooms.json")
    room_commands.room_handler("shell", "list rooms.json")
    room_commands.room_handler("shell", "remove rooms.json")
    room_commands.room_handler("shell", "update rooms.json")
    assert calls == [
        ("add", "shell", "rooms.json"),
        ("list", "shell", "rooms.json"),
        ("remove", "shell", "rooms.json"),
        ("update", "shell", "rooms.json"),
    ]

    room_commands.room_handler("shell", "bad")
    assert True


@pytest.mark.parametrize(
    "value, validator, default, expected",
    [
        ("Room 200", lambda v: v, None, "Room 200"),
        ("", lambda v: v if v else "fallback", "fallback", "fallback"),
    ],
)
def test_prompt_input_accepts_valid_values_and_default_blank_input(value, validator, default, expected):
    # Verifies prompting accepts valid input and applies defaults when the input is blank.
    responses = iter([value])

    import builtins

    builtins.input = lambda prompt="": next(responses)
    try:
        assert room_commands._prompt_input("Prompt: ", validator, default=default) == expected
    finally:
        builtins.input = __import__("builtins").input


@pytest.mark.parametrize(
    "value, validator, default",
    [
        ("bad", lambda v: (_ for _ in ()).throw(ValueError("not valid")), None),
        ("", lambda v: (_ for _ in ()).throw(ValueError("not valid")), None),
    ],
)
def test_prompt_input_retries_until_valid_input(value, validator, default, monkeypatch):
    # Verifies prompt validation retries until a valid value is entered.
    responses = iter([value, "good"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(responses))

    assert room_commands._prompt_input("Prompt: ", lambda v: "good" if v == "good" else validator(v), default=default) == "good"


# -----------------------------------------------------------------------------
# LAB COMMAND TESTS
# -----------------------------------------------------------------------------

def test_lab_clean_str_accepts_valid_value():
    # Verifies a non-empty lab name is returned unchanged.
    assert lab_commands._clean_str("Lab 101") == "Lab 101"


@pytest.mark.parametrize(
    "value, allow_empty, expected",
    [
        ("   ", False, ValueError),
        ("", False, ValueError),
        (None, False, ValueError),
        ("", True, ""),
        (None, True, None),
    ],
)
def test_lab_clean_str_rejects_blank_and_null_values(value, allow_empty, expected):
    # Verifies blank and null lab values are rejected unless explicitly allowed.
    if expected is ValueError:
        with pytest.raises(ValueError):
            lab_commands._clean_str(value, allow_empty=allow_empty)
    else:
        assert lab_commands._clean_str(value, allow_empty=allow_empty) == expected


def test_lab_parse_int_accepts_valid_positive_values_and_lower_bound():
    # Verifies normal lab capacities and the minimum valid boundary are accepted.
    assert lab_commands._parse_int("16") == 16
    assert lab_commands._parse_int("1", min_value=1) == 1


@pytest.mark.parametrize(
    "value, min_value, exc",
    [("0", 1, ValueError), ("-4", 1, ValueError), ("abc", 1, ValueError), (None, 1, TypeError)],
)
def test_lab_parse_int_rejects_invalid_numbers_and_types(value, min_value, exc):
    # Verifies invalid lab capacities and data types raise errors.
    with pytest.raises(exc):
        lab_commands._parse_int(value, min_value=min_value)


def test_lab_parse_list_parses_valid_features_and_rejects_duplicates():
    # Verifies lab feature lists are normalized and duplicate entries are rejected.
    assert lab_commands._parse_list("gpu, linux") == ["gpu", "linux"]
    with pytest.raises(ValueError):
        lab_commands._parse_list("gpu, gpu")


@pytest.mark.parametrize(
    "value, allow_empty, expected",
    [
        ("", True, []),
        (None, True, []),
        ("", False, ValueError),
        (None, False, ValueError),
    ],
)
def test_lab_parse_list_handles_empty_and_null_input(value, allow_empty, expected):
    # Verifies empty lab feature input is only accepted when explicitly permitted.
    if expected is ValueError:
        with pytest.raises(ValueError):
            lab_commands._parse_list(value, allow_empty=allow_empty)
    else:
        assert lab_commands._parse_list(value, allow_empty=allow_empty) == expected


@pytest.mark.parametrize(
    "value, expected",
    [
        ("08:00-12:00", {"start": "08:00", "end": "12:00"}),
        ("00:00-23:59", {"start": "00:00", "end": "23:59"}),
    ],
)
def test_lab_parse_time_range_accepts_valid_windows(value, expected):
    # Verifies valid lab availability windows are parsed into start and end values.
    assert lab_commands._parse_time_range(value) == expected


@pytest.mark.parametrize(
    "value, exc",
    [("12:00", ValueError), ("25:00-12:00", ValueError), ("09:00-09:00", ValueError), ("09:00-08:00", ValueError)],
)
def test_lab_parse_time_range_rejects_invalid_syntax_and_boundaries(value, exc):
    # Verifies malformed or non-increasing lab time windows fail validation.
    with pytest.raises(exc):
        lab_commands._parse_time_range(value)


def test_lab_prompt_lab_times_returns_none_when_unrestricted(monkeypatch):
    # Verifies unrestricted labs return None without asking for time blocks.
    responses = iter(["n"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(responses))

    assert lab_commands._prompt_lab_times() is None


def test_lab_prompt_lab_times_returns_restricted_windows_for_active_days(monkeypatch):
    # Verifies restricted labs record only the active weekdays with their time windows.
    responses = iter(["y", "08:00-12:00", "", "", "", "", ""])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(responses))

    result = lab_commands._prompt_lab_times()
    assert result == {"MON": [{"start": "08:00", "end": "12:00"}]}


def test_lab_add_creates_a_lab_and_persists_json(tmp_path, monkeypatch):
    # Verifies a valid lab request is saved into the configuration file.
    file_path = tmp_path / "labs.json"
    file_path.write_text(json.dumps({"config": {"labs": []}}))

    responses = iter(["Lab 101", "20", "gpu, linux", "n"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(responses))

    lab_commands.lab_add(None, str(file_path))

    data = json.loads(file_path.read_text())
    assert data["config"]["labs"][0]["name"] == "Lab 101"
    assert data["config"]["labs"][0]["capacity"] == 20
    assert data["config"]["labs"][0]["features"] == ["gpu", "linux"]
    assert data["config"]["labs"][0]["times"] is None


def test_lab_add_handles_missing_filename_and_invalid_json(tmp_path, capsys):
    # Verifies null file selection and malformed JSON are reported as handled failures.
    lab_commands.lab_add(None, None)
    out = capsys.readouterr().out
    assert "No configuration file selected." in out

    bad_file = tmp_path / "bad.json"
    bad_file.write_text("{not-valid-json}")
    lab_commands.lab_add(None, str(bad_file))
    out = capsys.readouterr().out
    assert "Failed to add lab:" in out


def test_lab_list_prints_labs_and_reports_empty_config(tmp_path, capsys):
    # Verifies the lab list includes entries and reports the empty state when no labs exist.
    lab_file = tmp_path / "labs.json"
    lab_file.write_text(json.dumps({"config": {"labs": [{"name": "Lab A", "capacity": 30, "features": ["gpu"], "times": None}]}}))

    lab_commands.lab_list(None, str(lab_file))
    out = capsys.readouterr().out
    assert "Lab A" in out
    assert "Capacity: 30" in out
    assert "Unrestricted (null)" in out

    lab_file.write_text(json.dumps({"config": {"labs": []}}))
    lab_commands.lab_list(None, str(lab_file))
    out = capsys.readouterr().out
    assert "No labs found in configuration." in out


def test_lab_remove_deletes_matching_lab_and_handles_empty_or_missing_names(tmp_path, monkeypatch, capsys):
    # Verifies removing a lab works and empty config or bad names are rejected safely.
    lab_file = tmp_path / "labs.json"
    lab_file.write_text(json.dumps({"config": {"labs": [{"name": "Lab A", "capacity": 12, "features": [], "times": None}, {"name": "Lab B", "capacity": 8, "features": [], "times": None}]}}))

    responses = iter(["Lab A"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(responses))
    lab_commands.lab_remove(None, str(lab_file))
    data = json.loads(lab_file.read_text())
    assert [lab["name"] for lab in data["config"]["labs"]] == ["Lab B"]

    lab_file.write_text(json.dumps({"config": {"labs": []}}))
    lab_commands.lab_remove(None, str(lab_file))
    out = capsys.readouterr().out
    assert "No labs available to remove." in out


def test_lab_update_changes_fields_and_handles_missing_lab_names(tmp_path, monkeypatch, capsys):
    # Verifies updating a lab changes its data and missing names fail gracefully.
    lab_file = tmp_path / "labs.json"
    lab_file.write_text(json.dumps({"config": {"labs": [{"name": "Lab A", "capacity": 12, "features": ["gpu"], "times": None}]}}))

    responses = iter(["Lab A", "Lab B", "25", "linux, cuda", "n"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(responses))
    lab_commands.lab_update(None, str(lab_file))
    data = json.loads(lab_file.read_text())
    assert data["config"]["labs"][0]["name"] == "Lab B"
    assert data["config"]["labs"][0]["capacity"] == 25
    assert data["config"]["labs"][0]["features"] == ["linux", "cuda"]

    lab_file.write_text(json.dumps({"config": {"labs": [{"name": "Lab A", "capacity": 12, "features": [], "times": None}]}}))
    responses = iter(["Missing Lab"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(responses))
    lab_commands.lab_update(None, str(lab_file))
    out = capsys.readouterr().out
    assert "Update failed:" in out


def test_lab_handler_routes_valid_commands_and_rejects_bad_usage(monkeypatch):
    # Verifies the lab router delegates to the right action and rejects malformed usage.
    calls = []

    def fake_lab_add(shell, filename):
        calls.append(("add", shell, filename))

    def fake_lab_list(shell, filename):
        calls.append(("list", shell, filename))

    def fake_lab_remove(shell, filename):
        calls.append(("remove", shell, filename))

    def fake_lab_update(shell, filename):
        calls.append(("update", shell, filename))

    monkeypatch.setattr(lab_commands, "lab_add", fake_lab_add)
    monkeypatch.setattr(lab_commands, "lab_list", fake_lab_list)
    monkeypatch.setattr(lab_commands, "lab_remove", fake_lab_remove)
    monkeypatch.setattr(lab_commands, "lab_update", fake_lab_update)

    lab_commands.lab_handler("shell", "add labs.json")
    lab_commands.lab_handler("shell", "list labs.json")
    lab_commands.lab_handler("shell", "remove labs.json")
    lab_commands.lab_handler("shell", "update labs.json")
    assert calls == [
        ("add", "shell", "labs.json"),
        ("list", "shell", "labs.json"),
        ("remove", "shell", "labs.json"),
        ("update", "shell", "labs.json"),
    ]

    lab_commands.lab_handler("shell", "bad")
    assert True


@pytest.mark.parametrize(
    "value, validator, default, expected",
    [
        ("Lab 200", lambda v: v, None, "Lab 200"),
        ("", lambda v: v if v else "fallback", "fallback", "fallback"),
    ],
)
def test_lab_prompt_input_accepts_valid_values_and_default_blank_input(value, validator, default, expected):
    # Verifies lab prompts accept valid values and use defaults when the input is blank.
    responses = iter([value])

    import builtins

    builtins.input = lambda prompt="": next(responses)
    try:
        assert lab_commands._prompt_input("Prompt: ", validator, default=default) == expected
    finally:
        builtins.input = __import__("builtins").input


@pytest.mark.parametrize(
    "value, validator, default",
    [
        ("bad", lambda v: (_ for _ in ()).throw(ValueError("not valid")), None),
        ("", lambda v: (_ for _ in ()).throw(ValueError("not valid")), None),
    ],
)
def test_lab_prompt_input_retries_until_valid_input(value, validator, default, monkeypatch):
    # Verifies lab prompts keep retrying until valid input is received.
    responses = iter([value, "good"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(responses))

    assert lab_commands._prompt_input("Prompt: ", lambda v: "good" if v == "good" else validator(v), default=default) == "good"

