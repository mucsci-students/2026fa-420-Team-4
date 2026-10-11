import json
import cmd
import runpy
from types import SimpleNamespace

import pytest

import shell


@pytest.fixture
def scheduler_shell():
    # Provides a fresh command shell for each behavior test.
    return shell.SchedulerShell()


@pytest.mark.parametrize(
    "line",
    ["", " help", "exit", "new x", "view", "generate", "noop"],
)
def test_precmd_skips_validation_for_exempt_commands(scheduler_shell, line):
    # Verifies commands that do not target config files bypass file validation.
    assert scheduler_shell.precmd(line) == line


def test_precmd_rejects_missing_invalid_missing_file_and_invalid_config(
    scheduler_shell, tmp_path, monkeypatch, capsys
):
    # Verifies file-target checks prevent commands from reaching invalid configurations.
    monkeypatch.chdir(tmp_path)
    assert scheduler_shell.precmd("room") == "noop"
    assert "Missing target file" in capsys.readouterr().out

    assert scheduler_shell.precmd("room list config.txt") == "noop"
    assert "must end with .json" in capsys.readouterr().out

    assert scheduler_shell.precmd("room list missing.json") == "noop"
    assert "does not exist" in capsys.readouterr().out

    bad_file = tmp_path / "bad.json"
    bad_file.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(shell, "validate_config_file", lambda path: (False, ["bad"]))
    assert scheduler_shell.precmd("room list bad.json") == "noop"
    output = capsys.readouterr().out
    assert "Validation Error" in output
    assert "- bad" in output


def test_precmd_returns_original_line_for_valid_config(scheduler_shell, tmp_path, monkeypatch):
    # Verifies a valid JSON target passes through unchanged after successful validation.
    path = tmp_path / "config.json"
    path.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(shell, "validate_config_file", lambda filename: (True, []))
    command = f"room list {path}"

    assert scheduler_shell.precmd(command) == command


def test_do_new_validates_path_and_writes_template(scheduler_shell, tmp_path, capsys):
    # Verifies new handles bad arguments and writes the complete empty configuration.
    scheduler_shell.do_new("")
    assert "Usage: new" in capsys.readouterr().out

    scheduler_shell.do_new("config.txt")
    assert "must end with .json" in capsys.readouterr().out

    path = tmp_path / "config.json"
    scheduler_shell.do_new(str(path))
    template = json.loads(path.read_text(encoding="utf-8"))
    assert template["config"] == {
        "rooms": [],
        "labs": [],
        "courses": [],
        "faculty": [],
    }
    assert template["time_slot_config"]["classes"] == []
    assert scheduler_shell.filename == str(path)

    scheduler_shell.do_new(str(path))
    assert "File already exists" in capsys.readouterr().out


def test_do_new_reports_creation_error(scheduler_shell, tmp_path, capsys):
    # Verifies creation failures are reported instead of escaping the command handler.
    missing_path = tmp_path / "missing" / "config.json"

    scheduler_shell.do_new(str(missing_path))

    assert "Error creating file" in capsys.readouterr().out


def test_do_load_handles_missing_success_and_failure(scheduler_shell, monkeypatch, capsys):
    # Verifies load handles empty arguments, successful loading, and loader exceptions.
    scheduler_shell.do_load("")
    assert "Usage: load" in capsys.readouterr().out

    config = object()
    monkeypatch.setattr(shell, "load_config_from_file", lambda cls, filename: config)
    scheduler_shell.do_load("config.json")
    assert scheduler_shell.config is config
    assert "Loaded config.json" in capsys.readouterr().out

    def fail_load(cls, filename):
        raise ValueError("bad config")

    monkeypatch.setattr(shell, "load_config_from_file", fail_load)
    scheduler_shell.do_load("bad.json")
    assert "Error loading configuration: bad config" in capsys.readouterr().out


def test_do_save_validates_arguments_and_serializes_loaded_config(
    scheduler_shell, tmp_path, capsys
):
    # Verifies save validates filenames and writes the loaded model as JSON.
    scheduler_shell.do_save("")
    assert "Usage: save" in capsys.readouterr().out

    scheduler_shell.do_save("config.txt")
    assert ".json extension" in capsys.readouterr().out

    scheduler_shell.do_save(str(tmp_path / "config.json"))
    assert "no currently loaded config" in capsys.readouterr().out

    scheduler_shell.config = SimpleNamespace(model_dump_json=lambda: '{"limit": 3}')
    path = tmp_path / "saved.json"
    scheduler_shell.do_save(str(path))
    assert json.loads(path.read_text(encoding="utf-8")) == {"limit": 3}
    assert "successfully saved" in capsys.readouterr().out


def test_do_validate_handles_empty_bad_invalid_and_valid_files(
    scheduler_shell, tmp_path, monkeypatch, capsys
):
    # Verifies validation reports parse failures, diagnostics, and valid fingerprints.
    scheduler_shell.do_validate("")
    assert "Usage: validate" in capsys.readouterr().out

    invalid_file = tmp_path / "invalid.json"
    invalid_file.write_text("{bad", encoding="utf-8")
    scheduler_shell.do_validate(str(invalid_file))
    assert "may not exist or may not be a valid config" in capsys.readouterr().out

    finding = SimpleNamespace(code="E1", path="config", message="bad")
    monkeypatch.setattr(
        shell,
        "validate_combined_config_data",
        lambda data: SimpleNamespace(
            is_valid=False, diagnostics=[finding], configuration_fingerprint=None
        ),
    )
    invalid_file.write_text("{}", encoding="utf-8")
    scheduler_shell.do_validate(str(invalid_file))
    output = capsys.readouterr().out
    assert "Config data is invalid" in output
    assert "E1 config bad" in output

    monkeypatch.setattr(
        shell,
        "validate_combined_config_data",
        lambda data: SimpleNamespace(
            is_valid=True, diagnostics=[], configuration_fingerprint="fingerprint"
        ),
    )
    scheduler_shell.do_validate(str(invalid_file))
    output = capsys.readouterr().out
    assert "Config data has been validated" in output
    assert "fingerprint" in output


def test_do_generate_handles_unloaded_empty_and_populated_schedules(
    scheduler_shell, monkeypatch, capsys
):
    # Verifies generation reports empty state and prints all courses in returned models.
    scheduler_shell.do_generate("")
    assert "No configuration loaded" in capsys.readouterr().out

    class EmptyScheduler:
        def __init__(self, config):
            pass

        def get_models(self):
            return []

    scheduler_shell.config = object()
    monkeypatch.setattr(shell, "Scheduler", EmptyScheduler)
    scheduler_shell.do_generate("")
    assert "No schedules found" in capsys.readouterr().out

    class Course:
        def as_csv(self):
            return "CS101, F1, R1"

    class PopulatedScheduler:
        def __init__(self, config):
            pass

        def get_models(self):
            return [[Course()], [Course()]]

    monkeypatch.setattr(shell, "Scheduler", PopulatedScheduler)
    scheduler_shell.do_generate("")
    output = capsys.readouterr().out
    assert "Schedule 1:" in output
    assert "Schedule 2:" in output
    assert output.count("CS101, F1, R1") == 2


def test_do_view_renders_all_configuration_sections_and_empty_states(
    scheduler_shell, capsys
):
    # Verifies the viewer prints resource, course, faculty, and time-slot details.
    scheduler_shell.do_view("")
    assert "no currently loaded config" in capsys.readouterr().out

    data = {
        "limit": 4,
        "config": {
            "rooms": [
                {"name": "R1", "capacity": 30, "features": ["projector", "screen"]},
                {"name": "R2", "capacity": 20, "features": []},
            ],
            "labs": [
                {"name": "L1", "capacity": 25, "features": ["computers"]},
                {"name": "L2", "capacity": 10, "features": []},
            ],
            "courses": [
                {
                    "course_id": "CS101",
                    "credits": 4,
                    "capacity": 30,
                    "room": ["R1"],
                    "lab": ["L1"],
                    "conflicts": ["CS202"],
                    "faculty": ["F1"],
                },
                {
                    "course_id": "CS202",
                    "credits": 3,
                    "capacity": 20,
                    "room": [],
                    "lab": [],
                    "conflicts": [],
                    "faculty": None,
                },
            ],
            "faculty": [
                {
                    "name": "F1",
                    "minimum_credits": 3,
                    "maximum_credits": 6,
                    "unique_course_limit": 2,
                    "maximum_days": None,
                    "mandatory_days": ["MON", "WED"],
                },
                {
                    "name": "F2",
                    "minimum_credits": 0,
                    "maximum_credits": 4,
                    "unique_course_limit": 1,
                    "maximum_days": 5,
                    "mandatory_days": [],
                },
            ],
        },
        "time_slot_config": {
            "times": {"MON": [{"start": "08:00", "end": "12:00"}]},
            "max_time_gap": 60,
            "min_time_overlap": 0,
        },
    }
    scheduler_shell.config = SimpleNamespace(model_dump=lambda: data)

    scheduler_shell.do_view("")

    output = capsys.readouterr().out
    for expected in (
        "Maximum generated schedules: 4",
        "Room R1: Capacity of 30",
        "Room has no features.",
        "L1 Lab: Capacity of 25",
        "Lab has no features.",
        "CS101:",
        "acceptable labs are L1",
        "Conflicts with CS202",
        "no other classes",
        "No assigned faculty.",
        "no max days",
        "Mandatory days are MON, WED",
        "No mandatory days",
        "Max time gap of 60, min time overlap of 0",
    ):
        assert expected in output


@pytest.mark.parametrize(
    "method, module_name, handler_name",
    [
        ("do_room", "room_commands", "room_handler"),
        ("do_course", "course_commands", "course_handler"),
        ("do_lab", "lab_commands", "lab_handler"),
        ("do_faculty", "faculty_commands", "faculty_handler"),
        ("do_times", "times_commands", "times_handler"),
        ("do_classes", "times_commands", "classes_handler"),
        ("do_optimizer", "optimizer_commands", "optimizer_handler"),
        ("do_limit", "limit_commands", "limit_handler"),
        ("do_help", "help", "help_handler"),
    ],
)
def test_shell_command_methods_delegate_to_handlers(
    scheduler_shell, monkeypatch, method, module_name, handler_name
):
    # Verifies each shell command forwards its shell instance and arguments.
    module = getattr(shell, module_name)
    seen = []
    monkeypatch.setattr(
        module,
        handler_name,
        lambda command_shell, arg: seen.append((command_shell, arg)),
    )

    getattr(scheduler_shell, method)("arguments")

    assert seen == [(scheduler_shell, "arguments")]


def test_do_exit_and_noop(scheduler_shell):
    # Verifies exit stops the command loop while noop returns without side effects.
    assert scheduler_shell.do_exit("") is True
    assert scheduler_shell.do_noop("") is None


def test_running_shell_module_starts_command_loop(monkeypatch):
    # Verifies executing the shell module invokes the interactive command loop.
    started = []
    monkeypatch.setattr(cmd.Cmd, "cmdloop", lambda instance: started.append(instance))

    runpy.run_path(shell.__file__, run_name="__main__")

    assert len(started) == 1
    assert started[0].__class__.__name__ == "SchedulerShell"
