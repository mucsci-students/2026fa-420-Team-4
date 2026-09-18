import json

from scheduler.config import (
    CombinedConfig,
    CourseConfig,
)

"""
def course_add(shell):
    if shell.config is None:
        print("No configuration loaded.")
        return
    try:
        # Base course identifier; repeated values create separately numbered sections
        # Python type: Course.
        # Required
        course_id = input("Enter course ID: ")

        # Optional stable section suffix; null uses the generated zero-padded input-order number
        # str | None
        # Optional
        section_id = input("Enter section ID: ").strip()

        if section_id == "":
            section_id = None

        # Number of credit hours
        # int
        # Required
        credits = int(input("Enter number of credits: "))

        # Expected section enrollment that any assigned rooms and labs must accommodate
        # int
        # Required
        capacity = int(input("Enter capacity: "))

        # Required delivery composition of the selected class pattern
        # CourseModality
        # Allowed values: in_person / online / hybrid
        # Optional
        modality = input("Enter modality (in_person, online, hybrid): ")

        # Allowed room names; empty is valid only for compatible patterns that do not occupy a room
        # list[Room]
        # Required
        room = [
            value.strip()
            for value in input("Enter Room(s) (comma separated): ").split(",")
            if value.strip()
        ]

        # Acceptable labs; an empty list means the course has no lab meeting
        # list[Lab]
        # Optional
        lab = [
            value.strip()
            for value in input("Enter Lab(s) (comma separated): ").split(",")
            if value.strip()
        ]

        # Feature tags every assigned lecture room must provide
        # set[str]
        # Optional
        required_room_features = {
            value.strip()
            for value in input(
                "Enter required room features (comma separated): "
            ).split(",")
            if value.strip()
        }

        # Feature tags every assigned lab must provide
        # set[str]
        # Optional
        required_lab_features = {
            value.strip()
            for value in input("Enter required lab features (comma separated): ").split(
                ","
            )
            if value.strip()
        }

        # Whether the lab meeting also occupies the section's assigned lecture room
        # bool
        reserve_room_during_lab = (
            input("Reserve room during lab? (y/n): ").lower() == "y"
        )

        # Base course IDs whose sections cannot overlap; an empty list means no declared conflicts
        # list[Course]
        # Required
        conflicts = [
            value.strip()
            for value in input("Enter conflict(s) (comma separated): ").split(",")
            if value.strip()
        ]

        # Non-empty faculty candidates, or null to derive candidates from faculty course-preference keys
        # list[Faculty] | None
        # Required
        faculty = [
            value.strip()
            for value in input("Enter faculty (comma separated): ").split(",")
            if value.strip()
        ]
        course = CourseConfig(
            course_id=course_id,
            section_id=section_id,
            credits=credits,
            capacity=capacity,
            modality=modality,
            room=room,
            lab=lab,
            required_room_features=required_room_features,
            required_lab_features=required_lab_features,
            reserve_room_during_lab=reserve_room_during_lab,
            conflicts=conflicts,
            faculty=faculty,
        )
        candidate = copy.deepcopy(shell.config)

        candidate.config.courses.append(course)

        CombinedConfig.model_validate(candidate.model_dump())

        shell.config = candidate

        print("Course added.")

    except Exception as error:
        print(f"Add failed: " f"{error}")
"""


def course_add(shell):
    if shell.filename is None:
        print("No configuration file selected.")
        return

    try:
        # Open the file created by "new"
        with open(shell.filename, "r") as f:
            data = json.load(f)

        # Base course identifier
        course_id = input("Enter course ID: ")

        # Optional section ID
        section_id = input("Enter section ID: ").strip()
        if section_id == "":
            section_id = None

        # Number of credits
        credits = int(input("Enter number of credits: "))

        # Expected section enrollment
        capacity = int(input("Enter capacity: "))

        # Course modality
        modality = input(
            "Enter modality (in_person, online, hybrid): "
        )

        # Allowed rooms
        room = [
            value.strip()
            for value in input(
                "Enter Room(s) (comma separated): "
            ).split(",")
            if value.strip()
        ]

        # Acceptable labs
        lab = [
            value.strip()
            for value in input(
                "Enter Lab(s) (comma separated): "
            ).split(",")
            if value.strip()
        ]

        # Required room features
        required_room_features = [
            value.strip()
            for value in input(
                "Enter required room features (comma separated): "
            ).split(",")
            if value.strip()
        ]

        # Required lab features
        required_lab_features = [
            value.strip()
            for value in input(
                "Enter required lab features (comma separated): "
            ).split(",")
            if value.strip()
        ]

        # Whether the room stays reserved during the lab
        reserve_room_during_lab = input(
            "Reserve room during lab? (y/n): "
        ).lower() == "y"

        # Course conflicts
        conflicts = [
            value.strip()
            for value in input(
                "Enter conflict(s) (comma separated): "
            ).split(",")
            if value.strip()
        ]

        # Faculty
        faculty = [
            value.strip()
            for value in input(
                "Enter faculty (comma separated): "
            ).split(",")
            if value.strip()
        ]

        # Create course dictionary
        course = {
            "course_id": course_id,
            "section_id": section_id,
            "credits": credits,
            "capacity": capacity,
            "modality": modality,
            "room": room,
            "lab": lab,
            "required_room_features": required_room_features,
            "required_lab_features": required_lab_features,
            "reserve_room_during_lab": reserve_room_during_lab,
            "conflicts": conflicts,
            "faculty": faculty
        }

        # Add course to configuration
        data["config"]["courses"].append(course)

        # Save configuration back to the same file
        with open(shell.filename, "w") as f:
            json.dump(data, f, indent=4)

        print("Course added.")

    except Exception as error:
        print(f"Add failed: {error}")












def course_list(shell):  #
    pass


def course_remove(shell, arg):
    pass


def course_update(shell, arg):
    pass


def course_handler(shell, arg):
    parts = arg.split()
    if len(parts) == 0:
        print("No command provided. Usage: add | list | remove | update")
        return
    command = parts[0]
    if command == "add":
        course_add(shell)
    elif command == "list":
        course_list(shell)
    elif command == "remove":
        course_remove(shell, arg)
    elif command == "update":
        course_update(shell, arg)
    else:
        print("Invalid command. Usage: add | list | remove | update")
