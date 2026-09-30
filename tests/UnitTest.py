"""Pytest tests for the command methods implemented in shell.py."""

import importlib
import inspect
from pathlib import Path

import pytest


COMMANDS = (
	"do_new",
	"do_view",
	"do_save",
	"do_validate",
	"do_load",
	"do_generate",
)


def _make_shell():
	"""Find and create the class that owns the shell commands."""
	module = importlib.import_module("shell")

	for candidate in vars(module).values():
		if inspect.isclass(candidate) and all(
			callable(getattr(candidate, name, None)) for name in COMMANDS
		):
			try:
				return candidate()
			except TypeError:
				return candidate.__new__(candidate)

	if all(callable(getattr(module, name, None)) for name in COMMANDS):
		return module

	raise AssertionError("shell.py does not expose all required commands")


@pytest.fixture
def shell(monkeypatch, tmp_path):
	"""Run each command in an isolated temporary directory."""
	monkeypatch.chdir(tmp_path)
	return _make_shell()


@pytest.mark.parametrize("command", COMMANDS)
def test_command_is_defined(shell, command):
	assert callable(getattr(shell, command))


@pytest.mark.parametrize("command", COMMANDS)
def test_command_accepts_cmd_input(shell, command):
	"""cmd.Cmd methods receive one string containing the command arguments."""
	method = getattr(shell, command)
	try:
		result = method("")
	except (SystemExit, EOFError) as exc:
		pytest.fail(f"{command} terminated the shell: {exc}")
	except FileNotFoundError as exc:
		pytest.fail(f"{command} used a missing file for empty input: {exc}")

	assert result is None or result is not False


def test_do_new_creates_a_file_that_does_not_exist(shell, tmp_path):
	"""do_new creates a file when the requested name is unused."""
	filename = "new_file.txt"

	shell.do_new(filename)

	assert (tmp_path / filename).is_file()


def test_do_new_with_an_empty_filename_fails(shell, tmp_path):
	"""An empty filename must not create a file."""
	before = set(tmp_path.iterdir())

	shell.do_new("")

	assert set(tmp_path.iterdir()) == before


def test_do_new_with_an_existing_filename_fails(shell, tmp_path):
	"""An existing file must not be overwritten by do_new."""
	path = Path("existing_file.txt")
	path.write_text("original content", encoding="utf-8")

	shell.do_new(path.name)

	assert path.read_text(encoding="utf-8") == "original content"


def test_do_load_with_a_missing_config_file_fails(shell):
	"""do_load must handle a config filename that does not exist."""
	shell.do_load("missing_config.json")


def test_do_load_with_a_new_empty_file_fails(shell, tmp_path):
	"""do_load must handle an empty config file."""
	path = tmp_path / "empty_config.json"
	path.touch()

	shell.do_load(path.name)


def test_do_load_with_a_valid_config_file_works(shell, tmp_path):
	"""do_load should load an existing config file."""
	path = tmp_path / "config.json"
	path.write_text("{}", encoding="utf-8")

	shell.do_load(path.name)


def test_do_save_with_a_missing_filename_fails(shell, tmp_path):
	"""do_save must not create a file when no filename is provided."""
	before = set(tmp_path.iterdir())

	shell.do_save("")

	assert set(tmp_path.iterdir()) == before


def test_do_save_with_an_existing_filename_fails(shell, tmp_path):
	"""do_save must not overwrite an existing file."""
	path = tmp_path / "existing_config.json"
	path.write_text("original content", encoding="utf-8")

	shell.do_save(path.name)

	assert path.read_text(encoding="utf-8") == "original content"


def test_do_validate_with_a_missing_file_fails(shell):
	"""do_validate must handle a file that does not exist."""
	shell.do_validate("missing_config.json")


def test_do_validate_with_an_unformatted_file_fails(shell, tmp_path):
	"""do_validate must reject malformed config content."""
	path = tmp_path / "invalid_config.json"
	path.write_text("not valid json", encoding="utf-8")

	shell.do_validate(path.name)


def test_do_validate_with_a_formatted_file_works(shell, tmp_path):
	"""do_validate should accept a formatted config file."""
	path = tmp_path / "valid_config.json"
	path.write_text("{}", encoding="utf-8")

	shell.do_validate(path.name)


def test_do_view_with_no_loaded_config_fails(shell):
	"""do_view must handle the absence of a loaded config file."""
	shell.do_view("")


def test_do_view_with_an_empty_loaded_file_fails(shell, tmp_path):
	"""do_view must handle a loaded but empty file."""
	path = tmp_path / "empty_config.json"
	path.touch()
	shell.do_load(path.name)

	shell.do_view("")


def test_do_view_with_a_loaded_file_shows_content(shell, tmp_path, capsys):
	"""do_view should display content from the loaded config file."""
	path = tmp_path / "minimal_config.json"
	path.write_text('{"name": "minimal"}', encoding="utf-8")
	shell.do_load(path.name)

	shell.do_view("")

	assert "minimal" in capsys.readouterr().out


def test_do_generate_with_no_loaded_config_fails(shell):
	"""do_generate must handle the absence of a loaded config file."""
	shell.do_generate("")


def test_do_generate_with_a_loaded_config_works(shell, tmp_path):
	"""do_generate should run when a config file is loaded."""
	path = tmp_path / "config.json"
	path.write_text("{}", encoding="utf-8")
	shell.do_load(path.name)

	shell.do_generate("")
