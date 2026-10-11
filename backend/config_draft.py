"""
    This is all of the data that we are looking to contain...
    Main idea:
        have a class/series of classes that holds all of the necessary data parameters
        if the user loads/closes a config, then the stuff is saved... 
"""
from dataclasses import dataclass, field
from typing import Any

@dataclass
class Meeting:
    day: str = ""
    duration: int = 0
    delivery: str = ""
    lab: bool = False

@dataclass
class Pattern:
    credits: int = 0
    meetings: list[Meeting] = field(default_factory=list)
    disabled: bool = False


@dataclass
class Room:
    name: str = ""
    capacity: int = 0
    features: list[str] = field(default_factory=list)
    times: dict[str, Any] = field(default_factory=dict)


@dataclass
class Lab:
    name: str = ""
    capacity: int = 0
    features: list[str] = field(default_factory=list)
    times: dict[str, Any] = field(default_factory=dict)


@dataclass
class Course:
    course_id: str = ""
    section_id: str = ""
    credits: int = 0
    capacity: int = 0
    modality: str = ""
    room: str | None = None
    lab: str | None = None
    required_room_features: list[str] = field(default_factory=list)
    required_lab_features: list[str] = field(default_factory=list)
    reserve_room_during_lab: bool = False
    conflicts: list[Any] = field(default_factory=list)
    faculty: list[str] = field(default_factory=list)


@dataclass
class Faculty:
    name: str = ""
    maximum_credits: int = 0
    minimum_credits: int = 0
    unique_course_limit: int = 0
    maximum_days: int = 5
    mandatory_days: list[str] = field(default_factory=list)
    times: dict[str, Any] = field(default_factory=dict)
    course_preferences: list[Any] = field(default_factory=list)
    room_preferences: list[Any] = field(default_factory=list)
    lab_preferences: list[Any] = field(default_factory=list)


# -------------------------
# Time-slot configuration
# -------------------------

@dataclass
class TimeSlotConfig:
    times: dict[str, list[Any]] = field(
        default_factory=lambda: {
            "MON": [],
            "TUE": [],
            "WED": [],
            "THU": [],
            "FRI": [],
        }
    )
    classes: list[Any] = field(default_factory=list)


# -------------------------
# Configuration containers
# -------------------------

@dataclass
class ConfigData:
    rooms: list[Room] = field(default_factory=list)
    labs: list[Lab] = field(default_factory=list)
    courses: list[Course] = field(default_factory=list)
    faculty: list[Faculty] = field(default_factory=list)


@dataclass
class Config:
    config: ConfigData = field(default_factory=ConfigData)
    time_slot_config: TimeSlotConfig = field(
        default_factory=TimeSlotConfig
    )
    limit: int = 0
    optimizer_flags: list[str] = field(default_factory=list)