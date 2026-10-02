"""Commands for modifying the scheduler configuration JSON file."""

from copy import deepcopy
import json
from os import PathLike
from typing import Any, Tuple


def _command_skeleton(
	configfile: Any,
	values: tuple,
	expected_size: int,
	section: str,
	action: str,
) -> tuple:
	"""Apply a command to a JSON configuration and return ``(config, success)``.

	``configfile`` may be a path or an already loaded configuration dictionary.
	For a path, the updated configuration is written back to that file.
	The first tuple value is used as the record identifier for modify/delete.
	"""
	if not isinstance(values, tuple) or len(values) != expected_size:
		# Reject malformed commands before reading or changing the configuration.
		return deepcopy(configfile), False

	try:
		# A path is loaded from disk; dictionary input is copied so callers do
		# not observe partial changes when a command fails.
		path = configfile if isinstance(configfile, (str, bytes, PathLike)) else None
		if path is not None:
			with open(path, "r", encoding="utf-8") as stream:
				config = json.load(stream)
		else:
			config = deepcopy(configfile)

		# The configuration must be an object, and each target section must be
		# a list of records that can be added to, modified, or deleted.
		if not isinstance(config, dict):
			return deepcopy(configfile), False
		items = config.setdefault(section, [])
		if not isinstance(items, list):
			return deepcopy(configfile), False

		# Locate the record by its first value, which serves as its identifier.
		index = next((i for i, item in enumerate(items)
				if isinstance(item, (list, tuple)) and item and item[0] == values[0]
				), None)
		if action == "add":
			# Adding is only valid when no record uses this identifier yet.
			if index is not None:
				return deepcopy(configfile), False
			items.append(list(values))
		elif action == "modify":
			# Replace the complete existing record with the supplied values.
			if index is None:
				return deepcopy(configfile), False
			items[index] = list(values)
		else:
			# Deletion also requires an existing record to be found.
			if index is None:
				return deepcopy(configfile), False
			items.pop(index)

		if path is not None:
			# Persist successful changes only when the caller supplied a file path.
			with open(path, "w", encoding="utf-8") as stream:
				json.dump(config, stream, indent=2)
		return config, True
	except (OSError, TypeError, ValueError, json.JSONDecodeError):
		return deepcopy(configfile), False


def room_add(configfile: Any, room: Tuple[Any, Any, Any, Any]) -> tuple:
	return _command_skeleton(configfile, room, 4, "rooms", "add")


def room_modify(configfile: Any, room: Tuple[Any, Any, Any, Any]) -> tuple:
	return _command_skeleton(configfile, room, 4, "rooms", "modify")


def room_delete(configfile: Any, room: Tuple[Any, Any, Any, Any]) -> tuple:
	return _command_skeleton(configfile, room, 4, "rooms", "delete")


def lab_add(configfile: Any, lab: Tuple[Any, Any, Any, Any]) -> tuple:
	return _command_skeleton(configfile, lab, 4, "labs", "add")


def lab_modify(configfile: Any, lab: Tuple[Any, Any, Any, Any]) -> tuple:
	return _command_skeleton(configfile, lab, 4, "labs", "modify")


def lab_delete(configfile: Any, lab: Tuple[Any, Any, Any, Any]) -> tuple:
	return _command_skeleton(configfile, lab, 4, "labs", "delete")


def course_add(configfile: Any, course: Tuple[Any, ...]) -> tuple:
	return _command_skeleton(configfile, course, 12, "courses", "add")


def course_modify(configfile: Any, course: Tuple[Any, ...]) -> tuple:
	return _command_skeleton(configfile, course, 12, "courses", "modify")


def course_delete(configfile: Any, course: Tuple[Any, ...]) -> tuple:
	return _command_skeleton(configfile, course, 12, "courses", "delete")


def faculty_add(configfile: Any, faculty: Tuple[Any, ...]) -> tuple:
	return _command_skeleton(configfile, faculty, 10, "faculty", "add")


def faculty_modify(configfile: Any, faculty: Tuple[Any, ...]) -> tuple:
	return _command_skeleton(configfile, faculty, 10, "faculty", "modify")


def faculty_delete(configfile: Any, faculty: Tuple[Any, ...]) -> tuple:
	return _command_skeleton(configfile, faculty, 10, "faculty", "delete")
