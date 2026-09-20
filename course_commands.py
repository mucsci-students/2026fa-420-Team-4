import json

"""
from scheduler.config import (
    CombinedConfig,
    CourseConfig,
)
"""
VALID_MODALITIES = {"in_person", "online", "hybrid"}


#Loops so user is reprompted on invalid input
def _prompt_input(prompt_text, validator_func, default=None):
    while True:
        try:
            raw_val = input(prompt_text).strip()

            # If user pressed Enter and there is a default, return the default
            if not raw_val and default is not None:
                return default

            # Pass string into validation function
            return validator_func(raw_val)
        except ValueError as e:
            print(f"  Invalid input: {e}. Please try again.\n")


def _clean_str(val, allow_empty=False):
    if not val and not allow_empty:
        raise ValueError("Field cannot be blank or contain only whitespace")
    return val


def _parse_int(val, min_value=1):
    parsed = int(val)
    if parsed < min_value:
        raise ValueError(f"Must be an integer greater than or equal to {min_value}")
    return parsed


def _parse_list(val, allow_empty=True, exclude_item=None):
    if not val:
        if not allow_empty:
            raise ValueError("List cannot be empty")
        return []

    items = [v.strip() for v in val.split(",") if v.strip()]

    if not items and not allow_empty:
        raise ValueError("List cannot be empty")

    if len(items) != len(set(items)):
        raise ValueError("List cannot contain duplicate items")

    if exclude_item and exclude_item in items:
        raise ValueError(f"Cannot include '{exclude_item}' in this list")

    return items


def course_add(shell, filename):
    if filename is None:
        print("No configuration file selected.")
        return

    try:
        with open(filename, "r") as f:
            data = json.load(f)

        print("\n--- Add New Course ---")

        course_id = _prompt_input(
            "Enter course ID (required): ",
            lambda v: _clean_str(v, allow_empty=False),
        )

        section_id = _prompt_input(
            "Enter section ID (optional, press Enter for null): ",
            lambda v: v if v else None,
            default=None,
        )

        credits = _prompt_input(
            "Enter number of credits (positive integer): ",
            lambda v: _parse_int(v, min_value=1),
        )

        capacity = _prompt_input(
            "Enter capacity (positive integer): ",
            lambda v: _parse_int(v, min_value=1),
        )
    

        def validate_modality(v):
            v_clean = v.lower()
            if v_clean not in VALID_MODALITIES:
                raise ValueError(f"Must be one of: {', '.join(VALID_MODALITIES)}")
            return v_clean

        modality = _prompt_input(
            "Enter modality (in_person, online, hybrid) [in_person]: ",
            validate_modality,
            default="in_person",
        )

        if modality == "online":
            print("Note: Online modality set. Rooms and Labs forced to empty lists.")
            room = []
            lab = []
        else:
            room = _prompt_input(
                "Enter Room(s) (comma-separated, press Enter for none): ",
                lambda v: _parse_list(v, allow_empty=True),
                default=[],
            )
            lab = _prompt_input(
                "Enter Lab(s) (comma-separated, press Enter for none): ",
                lambda v: _parse_list(v, allow_empty=True),
                default=[],
            )

        req_room_features = _prompt_input(
            "Enter required room features (comma-separated, or Enter for none): ",
            lambda v: _parse_list(v, allow_empty=True),
            default=[],
        )

        req_lab_features = _prompt_input(
            "Enter required lab features (comma-separated, or Enter for none): ",
            lambda v: _parse_list(v, allow_empty=True),
            default=[],
        )

        reserve_room_during_lab = _prompt_input(
            "Reserve room during lab? (y/n) [y]: ",
            lambda v: False if v.lower() == "n" else True,
            default=True,
        )

        conflicts = _prompt_input(
            "Enter conflict course IDs (comma-separated, or Enter for none): ",
            lambda v: _parse_list(v, allow_empty=True, exclude_item=course_id),
            default=[],
        )

        def validate_faculty(v):
            if not v or v.lower() == "null":
                return None
            return _parse_list(v, allow_empty=False)

        faculty = _prompt_input(
            "Enter faculty candidates (comma-separated, or Enter/null to derive): ",
            validate_faculty,
            default=None,
        )

        course = {
            "course_id": course_id,
            "section_id": section_id,
            "credits": credits,
            "capacity": capacity,
            "modality": modality,
            "room": room,
            "lab": lab,
            "required_room_features": req_room_features,
            "required_lab_features": req_lab_features,
            "reserve_room_during_lab": reserve_room_during_lab,
            "conflicts": conflicts,
            "faculty": faculty,
        }

        if "config" not in data or "courses" not in data["config"]:
            data.setdefault("config", {})["courses"] = []

        data["config"]["courses"].append(course)

        with open(filename, "w") as f:
            json.dump(data, f, indent=4)

        print(f"\nCourse '{course_id}' added successfully.")

    except Exception as error:
        print(f"Failed to add course due to system error: {error}")


def course_list(shell, filename):
    if filename is None:
        print("No configuration file selected.")
        return

    try:
        with open(filename, "r") as f:
            data = json.load(f)

        courses = data.get("config", {}).get("courses", [])

        if not courses:
            print("No courses found in configuration.")
            return

        print(f"\n--- Course List ({len(courses)} Total) ---")
        for idx, c in enumerate(courses, 1):
            c_id = c.get("course_id", "N/A")
            sec = f".{c.get('section_id')}" if c.get("section_id") else ""
            mod = c.get("modality", "N/A")
            creds = c.get("credits", "N/A")
            cap = c.get("capacity", "N/A")
            rooms = ", ".join(c.get("room", [])) or "None"
            labs = ", ".join(c.get("lab", [])) or "None"

            fac = c.get("faculty")
            fac_str = ", ".join(fac) if isinstance(fac, list) else "Derived (null)"

            print(
                f"[{idx}] {c_id}{sec} | Modality: {mod} | Credits: {creds} | Cap: {cap} | "
                f"Rooms: [{rooms}] | Labs: [{labs}] | Faculty: {fac_str}"
            )
        print("-" * 40 + "\n")

    except Exception as error:
        print(f"List failed: {error}")


def course_remove(shell, filename):
    if filename is None:
        print("No configuration file selected.")
        return

    try:
        with open(filename, "r") as f:
            data = json.load(f)

        courses = data.get("config", {}).get("courses", [])
        if not courses:
            print("No courses available to remove.")
            return

        course_list(shell, filename)

        def find_matches(target_id):
            matching = [
                i for i, c in enumerate(courses) if c.get("course_id") == target_id
            ]
            if not matching:
                raise ValueError(f"No course found matching ID '{target_id}'")
            return matching

        matching = _prompt_input(
            "Enter course ID to remove: ",
            find_matches,
        )

        if len(matching) > 1:
            print(
                f"\nFound {len(matching)} entries for '{courses[matching[0]]['course_id']}':"
            )
            for pos, idx in enumerate(matching, 1):
                c = courses[idx]
                sec = f" (Sec: {c.get('section_id')})" if c.get("section_id") else ""
                print(
                    f"  {pos}. {c.get('course_id')}{sec} | Rooms: {c.get('room')} | Faculty: {c.get('faculty')}"
                )

            def validate_choice(val):
                choice = int(val) - 1
                if not (0 <= choice < len(matching)):
                    raise ValueError(f"Choice must be between 1 and {len(matching)}")
                return matching[choice]

            remove_idx = _prompt_input(
                "Select entry number to remove: ", validate_choice
            )
        else:
            remove_idx = matching[0]

        removed = courses.pop(remove_idx)

        with open(filename, "w") as f:
            json.dump(data, f, indent=4)

        print(f"Course '{removed.get('course_id')}' removed successfully.")

    except Exception as error:
        print(f"Remove failed: {error}")


def course_update(shell, filename):
    if filename is None:
        print("No configuration file selected.")
        return

    try:
        with open(filename, "r") as f:
            data = json.load(f)

        courses = data.get("config", {}).get("courses", [])
        if not courses:
            print("No courses available to update.")
            return

        course_list(shell, filename)

        def find_matches(target_id):
            matching = [
                i for i, c in enumerate(courses) if c.get("course_id") == target_id
            ]
            if not matching:
                raise ValueError(f"No course found matching ID '{target_id}'")
            return matching

        matching = _prompt_input(
            "Enter course ID to update: ",
            find_matches,
        )

        if len(matching) > 1:
            print(f"\nFound {len(matching)} entries:")
            for pos, idx in enumerate(matching, 1):
                c = courses[idx]
                sec = f" (Sec: {c.get('section_id')})" if c.get("section_id") else ""
                print(f"  {pos}. {c.get('course_id')}{sec} | Rooms: {c.get('room')}")

            def validate_choice(val):
                choice = int(val) - 1
                if not (0 <= choice < len(matching)):
                    raise ValueError(f"Choice must be between 1 and {len(matching)}")
                return matching[choice]

            update_idx = _prompt_input(
                "Select entry number to update: ", validate_choice
            )
        else:
            update_idx = matching[0]

        c = courses[update_idx]
        print("\nUpdating course (Press ENTER to keep existing value):")

        c["course_id"] = _prompt_input(
            f"Course ID [{c.get('course_id')}]: ",
            lambda v: _clean_str(v, allow_empty=False),
            default=c.get("course_id"),
        )

        c["section_id"] = _prompt_input(
            f"Section ID [{c.get('section_id')}]: ",
            lambda v: None if v.lower() == "null" else v,
            default=c.get("section_id"),
        )

        c["credits"] = _prompt_input(
            f"Credits [{c.get('credits')}]: ",
            lambda v: _parse_int(v, min_value=1),
            default=c.get("credits"),
        )

        c["capacity"] = _prompt_input(
            f"Capacity [{c.get('capacity')}]: ",
            lambda v: _parse_int(v, min_value=1),
            default=c.get("capacity"),
        )

        def validate_modality(v):
            v_clean = v.lower()
            if v_clean not in VALID_MODALITIES:
                raise ValueError(f"Must be one of: {', '.join(VALID_MODALITIES)}")
            return v_clean

        c["modality"] = _prompt_input(
            f"Modality [{c.get('modality')}]: ",
            validate_modality,
            default=c.get("modality"),
        )

        if c["modality"] == "online":
            c["room"] = []
            c["lab"] = []
        else:
            c["room"] = _prompt_input(
                f"Rooms [{', '.join(c.get('room', []))}]: ",
                lambda v: _parse_list(v, allow_empty=True),
                default=c.get("room", []),
            )

            c["lab"] = _prompt_input(
                f"Labs [{', '.join(c.get('lab', []))}]: ",
                lambda v: _parse_list(v, allow_empty=True),
                default=c.get("lab", []),
            )

        c["required_room_features"] = _prompt_input(
            f"Required Room Features [{', '.join(c.get('required_room_features', []))}]: ",
            lambda v: _parse_list(v, allow_empty=True),
            default=c.get("required_room_features", []),
        )

        c["required_lab_features"] = _prompt_input(
            f"Required Lab Features [{', '.join(c.get('required_lab_features', []))}]: ",
            lambda v: _parse_list(v, allow_empty=True),
            default=c.get("required_lab_features", []),
        )

        res_default = "y" if c.get("reserve_room_during_lab", True) else "n"
        c["reserve_room_during_lab"] = _prompt_input(
            f"Reserve Room During Lab? (y/n) [{res_default}]: ",
            lambda v: False if v.lower() == "n" else True,
            default=c.get("reserve_room_during_lab", True),
        )

        c["conflicts"] = _prompt_input(
            f"Conflicts [{', '.join(c.get('conflicts', []))}]: ",
            lambda v: _parse_list(v, allow_empty=True, exclude_item=c["course_id"]),
            default=c.get("conflicts", []),
        )

        fac_curr = (
            ", ".join(c.get("faculty"))
            if isinstance(c.get("faculty"), list)
            else "null"
        )

        def validate_faculty(v):
            if v.lower() == "null":
                return None
            return _parse_list(v, allow_empty=False)

        c["faculty"] = _prompt_input(
            f"Faculty (comma-separated or 'null') [{fac_curr}]: ",
            validate_faculty,
            default=c.get("faculty"),
        )

        with open(filename, "w") as f:
            json.dump(data, f, indent=4)

        print(f"Course '{c['course_id']}' updated successfully.")

    except Exception as error:
        print(f"Update failed: {error}")


def course_handler(shell, arg):
    parts = arg.split()
    if len(parts) < 2:
        print("Usage: course <add|list|remove|update> <filename.json>")
        return

    command = parts[0].lower()
    filename = parts[1]

    if command == "add":
        course_add(shell, filename)
    elif command == "list":
        course_list(shell, filename)
    elif command == "remove":
        course_remove(shell, filename)
    elif command == "update":
        course_update(shell, filename)
    else:
        print("Invalid command. Usage: course <add|list|remove|update> <filename.json>")
