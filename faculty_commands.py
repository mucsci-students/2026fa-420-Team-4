import json
import re

VALID_DAYS = ["MON", "TUE", "WED", "THU", "FRI"]
TIME_REGEX = re.compile(r"^([0-1][0-9]|2[0-3]):[0-5][0-9]$")


def _prompt_input(prompt_text, validator_func, default=None):
    """Loop continuously until the user enters a valid input."""
    while True:
        try:
            raw_val = input(prompt_text).strip()

            if not raw_val and default is not None:
                return default

            return validator_func(raw_val)
        except ValueError as e:
            print(f"  Invalid input: {e}. Please try again.\n")


def _clean_str(val, allow_empty=False):
    if not val and not allow_empty:
        raise ValueError("Field cannot be blank or contain only whitespace")
    return val


def _parse_int(val, min_value=0, max_value=None):
    parsed = int(val)
    if parsed < min_value:
        raise ValueError(f"Must be an integer greater than or equal to {min_value}")
    if max_value is not None and parsed > max_value:
        raise ValueError(f"Must be an integer less than or equal to {max_value}")
    return parsed


def _parse_time_range(range_str):
    """Parses 'HH:MM-HH:MM' into {'start': 'HH:MM', 'end': 'HH:MM'} with end > start check."""
    parts = [p.strip() for p in range_str.split("-")]
    if len(parts) != 2:
        raise ValueError("Format must be HH:MM-HH:MM")

    start, end = parts[0], parts[1]

    if not TIME_REGEX.match(start) or not TIME_REGEX.match(end):
        raise ValueError("Times must be in 24-hour HH:MM format (00:00 to 23:59)")

    start_mins = int(start[:2]) * 60 + int(start[3:])
    end_mins = int(end[:2]) * 60 + int(end[3:])

    if end_mins <= start_mins:
        raise ValueError(f"End time ({end}) must be later than start time ({start})")

    return {"start": start, "end": end}


def _prompt_times_dict():
    """Prompts for daily availability ranges."""
    print("\n-- Enter Availability Times (e.g. 09:00-12:00, 14:00-17:00 | Press Enter to skip day) --")
    times = {}
    for day in VALID_DAYS:
        def validate_ranges(val):
            if not val:
                return []
            raw_ranges = [r.strip() for r in val.split(",") if r.strip()]
            parsed_ranges = [_parse_time_range(r) for r in raw_ranges]
            return parsed_ranges

        day_times = _prompt_input(
            f"Availability for {day}: ",
            validate_ranges,
            default=[],
        )
        if day_times:
            times[day] = day_times
    return times


def _prompt_preferences_dict(prompt_label):
    """Prompts for preference mapping with scores 0-10."""
    print(f"\n-- Enter {prompt_label} Preferences (format: KEY:SCORE with score from 0-10, e.g. CS101:10, Room A:5 | Press Enter to skip) --")

    def validate_prefs(val):
        if not val:
            return {}
        pairs = [p.strip() for p in val.split(",") if p.strip()]
        prefs = {}
        for pair in pairs:
            if ":" not in pair:
                raise ValueError(f"Invalid format '{pair}'. Must be KEY:SCORE")
            k, v = pair.split(":", 1)
            key = k.strip()
            if not key:
                raise ValueError("Preference key cannot be blank")
            score = _parse_int(v.strip(), min_value=0, max_value=10)
            prefs[key] = score
        return prefs

    return _prompt_input(
        f"{prompt_label} preferences: ",
        validate_prefs,
        default={},
    )


def faculty_add(shell, filename):
    if filename is None:
        print("No configuration file selected.")
        return

    try:
        with open(filename, "r") as f:
            data = json.load(f)

        existing_faculty = data.get("config", {}).get("faculty", [])
        existing_names = {f["name"].lower() for f in existing_faculty if "name" in f}

        print("\n--- Add New Faculty Member ---")

        def validate_name(v):
            clean = _clean_str(v, allow_empty=False)
            if clean.lower() in existing_names:
                raise ValueError(f"Faculty with name '{clean}' already exists")
            return clean

        name = _prompt_input("Enter Faculty Name: ", validate_name)

        min_credits = _prompt_input(
            "Minimum credits (>=0): ",
            lambda v: _parse_int(v, min_value=0),
        )

        def validate_max_credits(v):
            max_c = _parse_int(v, min_value=0)
            if max_c < min_credits:
                raise ValueError(f"maximum_credits ({max_c}) must be >= minimum_credits ({min_credits})")
            return max_c

        max_credits = _prompt_input("Maximum credits: ", validate_max_credits)

        unique_course_limit = _prompt_input(
            "Unique course limit (>=0): ",
            lambda v: _parse_int(v, min_value=0),
        )

        times = _prompt_times_dict()
        available_days = set(times.keys())

        def validate_mandatory_days(v):
            if not v:
                return []
            days = [d.strip().upper() for d in v.split(",") if d.strip()]
            invalid_days = [d for d in days if d not in VALID_DAYS]
            if invalid_days:
                raise ValueError(f"Invalid day(s): {', '.join(invalid_days)}. Allowed: {', '.join(VALID_DAYS)}")
            
            if len(days) != len(set(days)):
                raise ValueError("mandatory_days cannot contain duplicate entries")

            missing_from_times = set(days) - available_days
            if missing_from_times:
                raise ValueError(f"Mandatory days {list(missing_from_times)} are not present in specified 'times' availability")
            return days

        mandatory_days = _prompt_input(
            "Enter mandatory days (comma-separated, e.g. MON,WED | Press Enter for none): ",
            validate_mandatory_days,
            default=[],
        )

        def validate_max_days(v):
            max_d = _parse_int(v, min_value=0, max_value=5)
            if max_d < len(mandatory_days):
                raise ValueError(f"maximum_days ({max_d}) cannot be less than mandatory_days count ({len(mandatory_days)})")
            return max_d

        maximum_days = _prompt_input(
            "Maximum days to teach (0-5) [5]: ",
            validate_max_days,
            default=5,
        )

        course_preferences = _prompt_preferences_dict("Course")
        room_preferences = _prompt_preferences_dict("Room")
        lab_preferences = _prompt_preferences_dict("Lab")

        faculty_entry = {
            "name": name,
            "maximum_credits": max_credits,
            "minimum_credits": min_credits,
            "unique_course_limit": unique_course_limit,
            "maximum_days": maximum_days,
            "mandatory_days": mandatory_days,
            "times": times,
            "course_preferences": course_preferences,
            "room_preferences": room_preferences,
            "lab_preferences": lab_preferences,
        }

        if "config" not in data or "faculty" not in data["config"]:
            data.setdefault("config", {})["faculty"] = []

        data["config"]["faculty"].append(faculty_entry)

        with open(filename, "w") as f:
            json.dump(data, f, indent=4)

        print(f"\nFaculty '{name}' added successfully.")

    except Exception as error:
        print(f"Failed to add faculty: {error}")


def faculty_list(shell, filename):
    if filename is None:
        print("No configuration file selected.")
        return

    try:
        with open(filename, "r") as f:
            data = json.load(f)

        faculty_members = data.get("config", {}).get("faculty", [])

        if not faculty_members:
            print("No faculty found in configuration.")
            return

        print(f"\n--- Faculty List ({len(faculty_members)} Total) ---")
        for idx, f_entry in enumerate(faculty_members, 1):
            f_name = f_entry.get("name", "N/A")
            min_c = f_entry.get("minimum_credits", 0)
            max_c = f_entry.get("maximum_credits", 0)
            u_lim = f_entry.get("unique_course_limit", 0)
            max_d = f_entry.get("maximum_days", 5)
            mand_d = ", ".join(f_entry.get("mandatory_days", [])) or "None"
            active_days = ", ".join(f_entry.get("times", {}).keys()) or "None"

            print(
                f"[{idx}] {f_name} | Credits: {min_c}-{max_c} | Max Course Limit: {u_lim} | "
                f"Max Days: {max_d} | Mandatory: [{mand_d}] | Days Available: [{active_days}]"
            )
        print("-" * 40 + "\n")

    except Exception as error:
        print(f"List failed: {error}")


def faculty_remove(shell, filename):
    if filename is None:
        print("No configuration file selected.")
        return

    try:
        with open(filename, "r") as f:
            data = json.load(f)

        faculty_members = data.get("config", {}).get("faculty", [])
        if not faculty_members:
            print("No faculty available to remove.")
            return

        faculty_list(shell, filename)

        def find_match(target_name):
            for i, f_entry in enumerate(faculty_members):
                if f_entry.get("name", "").lower() == target_name.lower():
                    return i
            raise ValueError(f"No faculty member found matching name '{target_name}'")

        remove_idx = _prompt_input("Enter faculty name to remove: ", find_match)

        if len(faculty_members) == 1:
            print("Warning: The configuration requires at least one faculty policy.")

        removed = faculty_members.pop(remove_idx)

        with open(filename, "w") as f:
            json.dump(data, f, indent=4)

        print(f"Faculty member '{removed.get('name')}' removed successfully.")

    except Exception as error:
        print(f"Remove failed: {error}")


def faculty_update(shell, filename):
    if filename is None:
        print("No configuration file selected.")
        return

    try:
        with open(filename, "r") as f:
            data = json.load(f)

        faculty_members = data.get("config", {}).get("faculty", [])
        if not faculty_members:
            print("No faculty available to update.")
            return

        faculty_list(shell, filename)

        def find_match(target_name):
            for i, f_entry in enumerate(faculty_members):
                if f_entry.get("name", "").lower() == target_name.lower():
                    return i
            raise ValueError(f"No faculty member found with name '{target_name}'")

        update_idx = _prompt_input("Enter faculty name to update: ", find_match)
        f_entry = faculty_members[update_idx]

        print("\nUpdating faculty (Press ENTER to keep existing value):")

        other_names = {
            f_item["name"].lower()
            for idx, f_item in enumerate(faculty_members)
            if idx != update_idx and "name" in f_item
        }

        def validate_new_name(v):
            clean = _clean_str(v, allow_empty=False)
            if clean.lower() in other_names:
                raise ValueError(f"Faculty with name '{clean}' already exists")
            return clean

        f_entry["name"] = _prompt_input(
            f"Name [{f_entry.get('name')}]: ",
            validate_new_name,
            default=f_entry.get("name"),
        )

        f_entry["minimum_credits"] = _prompt_input(
            f"Minimum credits [{f_entry.get('minimum_credits', 0)}]: ",
            lambda v: _parse_int(v, min_value=0),
            default=f_entry.get("minimum_credits", 0),
        )

        def validate_max_credits(v):
            max_c = _parse_int(v, min_value=0)
            if max_c < f_entry["minimum_credits"]:
                raise ValueError(f"maximum_credits ({max_c}) must be >= minimum_credits ({f_entry['minimum_credits']})")
            return max_c

        f_entry["maximum_credits"] = _prompt_input(
            f"Maximum credits [{f_entry.get('maximum_credits', 0)}]: ",
            validate_max_credits,
            default=f_entry.get("maximum_credits", 0),
        )

        f_entry["unique_course_limit"] = _prompt_input(
            f"Unique course limit [{f_entry.get('unique_course_limit', 0)}]: ",
            lambda v: _parse_int(v, min_value=0),
            default=f_entry.get("unique_course_limit", 0),
        )

        update_times_str = _prompt_input(
            "Update availability times? (y/n) [n]: ",
            lambda v: v.lower() == "y",
            default=False,
        )
        if update_times_str:
            f_entry["times"] = _prompt_times_dict()

        available_days = set(f_entry.get("times", {}).keys())

        def validate_mandatory_days(v):
            if not v:
                return []
            days = [d.strip().upper() for d in v.split(",") if d.strip()]
            invalid_days = [d for d in days if d not in VALID_DAYS]
            if invalid_days:
                raise ValueError(f"Invalid day(s): {', '.join(invalid_days)}. Allowed: {', '.join(VALID_DAYS)}")

            if len(days) != len(set(days)):
                raise ValueError("mandatory_days cannot contain duplicate entries")

            missing = set(days) - available_days
            if missing:
                raise ValueError(f"Mandatory days {list(missing)} must be present in 'times' availability")
            return days

        mand_curr = ", ".join(f_entry.get("mandatory_days", []))
        f_entry["mandatory_days"] = _prompt_input(
            f"Mandatory Days [{mand_curr}]: ",
            validate_mandatory_days,
            default=f_entry.get("mandatory_days", []),
        )

        def validate_max_days(v):
            max_d = _parse_int(v, min_value=0, max_value=5)
            if max_d < len(f_entry["mandatory_days"]):
                raise ValueError(f"maximum_days ({max_d}) cannot be less than mandatory_days count ({len(f_entry['mandatory_days'])})")
            return max_d

        f_entry["maximum_days"] = _prompt_input(
            f"Maximum days to teach (0-5) [{f_entry.get('maximum_days', 5)}]: ",
            validate_max_days,
            default=f_entry.get("maximum_days", 5),
        )

        update_prefs_str = _prompt_input(
            "Update preferences? (y/n) [n]: ",
            lambda v: v.lower() == "y",
            default=False,
        )
        if update_prefs_str:
            f_entry["course_preferences"] = _prompt_preferences_dict("Course")
            f_entry["room_preferences"] = _prompt_preferences_dict("Room")
            f_entry["lab_preferences"] = _prompt_preferences_dict("Lab")

        with open(filename, "w") as f:
            json.dump(data, f, indent=4)

        print(f"Faculty member '{f_entry['name']}' updated successfully.")

    except Exception as error:
        print(f"Update failed: {error}")


def faculty_handler(shell, arg):
    parts = arg.split()
    if len(parts) < 2:
        print("Usage: faculty <add|list|remove|update> <filename.json>")
        return

    command = parts[0].lower()
    filename = parts[1]

    if command == "add":
        faculty_add(shell, filename)
    elif command == "list":
        faculty_list(shell, filename)
    elif command == "remove":
        faculty_remove(shell, filename)
    elif command == "update":
        faculty_update(shell, filename)
    else:
        print("Invalid command. Usage: faculty <add|list|remove|update> <filename.json>")