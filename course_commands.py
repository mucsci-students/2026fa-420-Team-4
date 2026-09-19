import json

from scheduler.config import (
    CombinedConfig,
    CourseConfig,
)

#Adds a course to the config that was created
def course_add(shell, filename):
    if filename is None:
        print("No configuration file selected.")
        return

    try:
        # Open the file created by "new"
        with open(filename, "r") as f:
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



#List the courses currently in the json file
def course_list(shell, filename):  #
    if filename is None:
        print("No configuration file selected")
        return
    
    try:
        with open(filename, "r") as f:
            data = json.load(f)
        courses = data.get("config",{}).get("courses",[])
        
        if not courses:
            print("No courses in config")
            return
        
        print(f"\n--- Courses ({len(courses)} Total) ---")
        for idx, c in enumerate(courses, 1):
            course_id = c.get("course_id", "N/A")
            sec = f" (Sec: {c.get('section_id')})" if c.get("section_id") else ""
            credits = c.get("credits", "N/A")
            capacity = c.get("capacity", "N/A")
            rooms = ", ".join(c.get("room", [])) or "None"
            labs = ", ".join(c.get("lab", [])) or "None"
            faculty = c.get("faculty")
            fac_str = ", ".join(faculty) if isinstance(faculty, list) else (faculty or "None")

            print(
                f"[{idx}] {course_id}{sec} | Credits: {credits} | Cap: {capacity} | "
                f"Rooms: [{rooms}] | Labs: [{labs}] | Faculty: {fac_str}"
            )
        print("-" * 35 + "\n")

    except Exception as error:
        print(f"List failed: {error}")


def course_remove(shell, filename):
    pass


def course_update(shell, filename):
    pass


def course_handler(shell, arg):
    parts = arg.split()
    if len(parts) == 0:
        print("Usage course (add | list | remove | update) <filename>.json")
        return
    
    command = parts[0]
    filename = None
    if len(parts) > 1:
        filename = parts[1]
    if command == "add":
        course_add(shell,filename)
    elif command == "list":
        course_list(shell,filename)
    elif command == "remove":
        course_remove(shell, filename)
    elif command == "update":
        course_update(shell, filename)
    else:
        print("Invalid command. Usage: add | list | remove | update")
