import csv
import io
import json
import sys
from dataclasses import dataclass
from types import ModuleType, SimpleNamespace

import pytest

from backend import ScheduleExporter


def test_schedule_export_filename_uses_loaded_json_basename():
    assert ScheduleExporter.schedule_export_filename(
        r"C:\configs\fall-term.json", ".csv"
    ) == "fall-term_schedules.csv"


def test_schedule_export_filename_falls_back_without_source_filename():
    assert ScheduleExporter.schedule_export_filename(None, ".json") == "schedules.json"


def test_schedule_export_filename_does_not_duplicate_schedule_suffix():
    """Verify an imported export filename keeps a single schedules suffix."""
    assert ScheduleExporter.schedule_export_filename(
        "fall-term_schedules.json", ".json"
    ) == "fall-term_schedules.json"


def test_schedules_to_csv_serializes_generated_schedule_rows():
    schedules = [
        {
            "schedule_id": 1,
            "courses": ["CS101, Room A1, Monday 09:00"],
        },
        {
            "schedule_id": 2,
            "courses": ["CS201, Room B2, Tuesday 10:00"],
        },
    ]

    rows = list(csv.DictReader(io.StringIO(ScheduleExporter.schedules_to_csv(schedules))))

    assert rows == [
        {
            "schedule_number": "1",
            "schedule_id": "1",
            "courses": '["CS101, Room A1, Monday 09:00"]',
        },
        {
            "schedule_number": "2",
            "schedule_id": "2",
            "courses": '["CS201, Room B2, Tuesday 10:00"]',
        },
    ]


def test_schedules_to_json_preserves_schedule_array():
    """Verify JSON serialization preserves the schedule collection on round trip."""
    schedules = [{"schedule_id": 1, "courses": ["CS101"]}]

    assert json.loads(ScheduleExporter.schedules_to_json(schedules)) == schedules


@pytest.mark.parametrize("prefix", ["=", "+", "-", "@", "\t", "\r"])
def test_schedules_to_csv_escapes_formula_like_strings(prefix):
    value = prefix + "SUM(1,2)"
    rows = list(csv.DictReader(io.StringIO(
        ScheduleExporter.schedules_to_csv([[{"name": value}]])
    )))

    assert rows[0]["name"] == "'" + value


def test_schedules_to_csv_preserves_other_values_and_nested_json():
    schedule = {
        "name": "CS101",
        "empty": "",
        "number": -42,
        "decimal": -1.5,
        "enabled": True,
        "missing": None,
        "courses": ["=CS101"],
        "details": {"room": "@A1"},
    }
    rows = list(csv.DictReader(io.StringIO(
        ScheduleExporter.schedules_to_csv([schedule])
    )))

    assert rows == [{
        "schedule_number": "1",
        "name": "CS101",
        "empty": "",
        "number": "-42",
        "decimal": "-1.5",
        "enabled": "True",
        "missing": "",
        "courses": '["=CS101"]',
        "details": '{"room": "@A1"}',
    }]


def test_schedule_export_filename_rejects_unsupported_extension():
    with pytest.raises(ValueError, match="extension must be .json or .csv"):
        ScheduleExporter.schedule_export_filename("config.json", ".txt")


def test_serializable_conversion_handles_models_mappings_and_dataclasses():
    @dataclass
    class Record:
        value: int

    class DumpModel:
        def model_dump(self):
            return {"record": Record(2)}

    class DictModel:
        def to_dict(self):
            return {"values": (1, 2)}

    class AttributeModel:
        def __init__(self):
            self.public = "visible"
            self._private = "hidden"

    converted = ScheduleExporter._to_serializable(
        {
            1: [
                Record(1),
                DumpModel(),
                DictModel(),
                AttributeModel(),
            ]
        }
    )

    assert converted == {
        "1": [
            {"value": 1},
            {"record": {"value": 2}},
            {"values": [1, 2]},
            {"public": "visible"},
        ]
    }


def test_serializable_conversion_rejects_values_without_supported_representation():
    class Unsupported:
        __slots__ = ()

    with pytest.raises(TypeError, match="cannot be converted"):
        ScheduleExporter._to_serializable(Unsupported())


@pytest.mark.parametrize("schedules", ["not schedules", b"not schedules", {}])
def test_schedule_serializers_reject_non_sequence_inputs(schedules):
    with pytest.raises(TypeError, match="must be a sequence"):
        ScheduleExporter.schedules_to_json(schedules)
    with pytest.raises(TypeError, match="must be a sequence"):
        ScheduleExporter.schedules_to_csv(schedules)
    with pytest.raises(TypeError, match="must be a sequence"):
        ScheduleExporter.export_schedules(schedules)


def test_schedules_to_csv_handles_empty_and_nested_schedule_rows():
    output = ScheduleExporter.schedules_to_csv([[], ["legacy", {"course": "CS101"}]])
    rows = list(csv.DictReader(io.StringIO(output)))

    assert rows == [
        {"schedule_number": "1", "item_number": "", "value": "", "course": ""},
        {"schedule_number": "2", "item_number": "1", "value": "legacy", "course": ""},
        {"schedule_number": "2", "item_number": "2", "value": "", "course": "CS101"},
    ]
    assert ScheduleExporter.schedules_to_csv([]) == ""


def test_choose_export_path_configures_dialog_and_destroys_window(monkeypatch):
    window = SimpleNamespace(withdraw=lambda: None, destroy=lambda: setattr(window, "destroyed", True))
    window.destroyed = False
    dialog_arguments = {}
    tkinter_module = ModuleType("tkinter")
    tkinter_module.Tk = lambda: window
    tkinter_module.filedialog = SimpleNamespace(
        asksaveasfilename=lambda **kwargs: dialog_arguments.update(kwargs) or "chosen.csv"
    )
    monkeypatch.setitem(sys.modules, "tkinter", tkinter_module)

    result = ScheduleExporter._choose_export_path("fall_schedules.json")

    assert result == "chosen.csv"
    assert window.destroyed is True
    assert dialog_arguments["initialfile"] == "fall_schedules.json"
    assert dialog_arguments["defaultextension"] == ".json"


@pytest.mark.parametrize("extension", [".json", ".csv"])
def test_export_schedules_writes_selected_format(tmp_path, monkeypatch, extension):
    path = tmp_path / f"schedules{extension}"
    monkeypatch.setattr(ScheduleExporter, "_choose_export_path", lambda initial: str(path))
    schedules = [{"schedule_id": 1, "courses": []}]

    result = ScheduleExporter.export_schedules(schedules, "fall.json")

    assert result == path
    if extension == ".json":
        assert json.loads(path.read_text(encoding="utf-8")) == schedules
    else:
        assert "schedule_number" in path.read_text(encoding="utf-8")


def test_export_schedules_handles_cancelled_dialog_and_unsupported_extension(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(ScheduleExporter, "_choose_export_path", lambda initial: "")
    assert ScheduleExporter.export_schedules([]) is None

    path = tmp_path / "schedules.txt"
    monkeypatch.setattr(ScheduleExporter, "_choose_export_path", lambda initial: str(path))
    with pytest.raises(ValueError, match="ending in .json or .csv"):
        ScheduleExporter.export_schedules([])


def test_choose_export_path_destroys_window_when_dialog_raises(monkeypatch):
    window = SimpleNamespace(withdraw=lambda: None, destroyed=False)

    def destroy():
        window.destroyed = True

    window.destroy = destroy
    tkinter_module = ModuleType("tkinter")
    tkinter_module.Tk = lambda: window

    def fail_dialog(**kwargs):
        raise RuntimeError("dialog failed")

    tkinter_module.filedialog = SimpleNamespace(asksaveasfilename=fail_dialog)
    monkeypatch.setitem(sys.modules, "tkinter", tkinter_module)

    with pytest.raises(RuntimeError, match="dialog failed"):
        ScheduleExporter._choose_export_path()
    assert window.destroyed is True
