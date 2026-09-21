import json
import re

VALID_DAYS = ["MON", "TUE", "WED", "THU", "FRI"]
TIME_REGEX = re.compile(r"^([0-1][0-9]|2[0-3]):[0-5][0-9]$")


# Loops so user is reprompted on invalid input instead of kicked out
def _prompt_input(prompt_text, validator_func, default=None):
    while True:
        try:
            raw_val = input(prompt_text).strip()

            if not raw_val and default is not None:
                return default

            return validator_func(raw_val)
        except ValueError as e:
            print(f"  Invalid input: {e}. Please try again.\n")


def _clean_str(val, allow_empty=False):
    if val is None:
        if allow_empty:
            return None
        raise ValueError("Field cannot be blank or contain only whitespace")

    if not isinstance(val, str):
        raise ValueError("Field must be a string")

    cleaned = val.strip()
    if not cleaned and not allow_empty:
        raise ValueError("Field cannot be blank or contain only whitespace")
    return cleaned


def _parse_int(val, min_value=1):
    parsed = int(val)
    if parsed < min_value:
        raise ValueError(f"Must be an integer greater than or equal to {min_value}")
    return parsed


def _parse_list(val, allow_empty=True):
    if not val:
        if not allow_empty:
            raise ValueError("List cannot be empty")
        return []

    items = [v.strip() for v in val.split(",") if v.strip()]

    if not items and not allow_empty:
        raise ValueError("List cannot be empty")

    if len(items) != len(set(items)):
        raise ValueError("List cannot contain duplicate items")

    return items


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


def _prompt_lab_times():
    """Prompts for lab time restrictions or returns None for unrestricted availability."""
    is_restricted = _prompt_input(
        "Does this lab have restricted availability hours? (y/n) [n]: ",
        lambda v: v.lower() == "y",
        default=False,
    )

    if not is_restricted:
        return None  # Unrestricted lab availability (null)

    print(
        "\n-- Enter Availability Windows (e.g. 08:00-12:00, 13:00-17:00 | Press Enter to skip day) --"
    )
    times = {}
    for day in VALID_DAYS:

        def validate_ranges(val):
            if not val:
                return []
            raw_ranges = [r.strip() for r in val.split(",") if r.strip()]
            return [_parse_time_range(r) for r in raw_ranges]

        day_times = _prompt_input(
            f"Availability for {day}: ",
            validate_ranges,
            default=[],
        )
        if day_times:
            times[day] = day_times

    return times


# Adds a lab to the given config
def lab_add(shell, filename):
    if filename is None:
        print("No configuration file selected.")
        return

    try:
        with open(filename, "r") as f:
            data = json.load(f)

        existing_labs = data.get("config", {}).get("labs", [])
        existing_names = {l["name"].lower() for l in existing_labs if "name" in l}

        print("\n--- Add New Lab ---")

        def validate_name(v):
            clean = _clean_str(v, allow_empty=False)
            if clean.lower() in existing_names:
                raise ValueError(f"Lab with name '{clean}' already exists")
            return clean

        name = _prompt_input("Enter Lab Name: ", validate_name)

        capacity = _prompt_input(
            "Enter Capacity (positive integer): ",
            lambda v: _parse_int(v, min_value=1),
        )

        features = _prompt_input(
            "Enter Features (comma-separated, e.g. gpu, linux | Press Enter for none): ",
            lambda v: _parse_list(v, allow_empty=True),
            default=[],
        )

        times = _prompt_lab_times()

        lab_entry = {
            "name": name,
            "capacity": capacity,
            "features": features,
            "times": times,
        }

        if "config" not in data or "labs" not in data["config"]:
            data.setdefault("config", {})["labs"] = []

        data["config"]["labs"].append(lab_entry)

        with open(filename, "w") as f:
            json.dump(data, f, indent=4)

        print(f"\nLab '{name}' added successfully.")

    except Exception as error:
        print(f"Failed to add lab: {error}")


# Lists the labs in the given congif
def lab_list(shell, filename):
    if filename is None:
        print("No configuration file selected.")
        return

    try:
        with open(filename, "r") as f:
            data = json.load(f)

        labs = data.get("config", {}).get("labs", [])

        if not labs:
            print("No labs found in configuration.")
            return

        print(f"\n--- Lab List ({len(labs)} Total) ---")
        for idx, l in enumerate(labs, 1):
            l_name = l.get("name", "N/A")
            cap = l.get("capacity", "N/A")
            feats = ", ".join(l.get("features", [])) or "None"

            t_data = l.get("times")
            if t_data is None:
                t_str = "Unrestricted (null)"
            else:
                active_days = ", ".join(t_data.keys()) or "None"
                t_str = f"Restricted [{active_days}]"

            print(
                f"[{idx}] {l_name} | Capacity: {cap} | Features: [{feats}] | Availability: {t_str}"
            )
        print("-" * 40 + "\n")

    except Exception as error:
        print(f"List failed: {error}")


# Removes labs from the given config
def lab_remove(shell, filename):
    if filename is None:
        print("No configuration file selected.")
        return

    try:
        with open(filename, "r") as f:
            data = json.load(f)

        labs = data.get("config", {}).get("labs", [])
        if not labs:
            print("No labs available to remove.")
            return

        lab_list(shell, filename)

        def find_match(target_name):
            for i, l in enumerate(labs):
                if l.get("name", "").lower() == target_name.lower():
                    return i
            raise ValueError(f"No lab found matching name '{target_name}'")

        remove_idx = _prompt_input("Enter lab name to remove: ", find_match)

        removed = labs.pop(remove_idx)

        with open(filename, "w") as f:
            json.dump(data, f, indent=4)

        print(f"Lab '{removed.get('name')}' removed successfully.")

    except Exception as error:
        print(f"Remove failed: {error}")


# Updates a lab in the given config
def lab_update(shell, filename):
    if filename is None:
        print("No configuration file selected.")
        return

    try:
        with open(filename, "r") as f:
            data = json.load(f)

        labs = data.get("config", {}).get("labs", [])
        if not labs:
            print("No labs available to update.")
            return

        lab_list(shell, filename)

        def find_match(target_name):
            for i, l in enumerate(labs):
                if l.get("name", "").lower() == target_name.lower():
                    return i
            raise ValueError(f"No lab found with name '{target_name}'")

        update_idx = _prompt_input("Enter lab name to update: ", find_match)
        l_entry = labs[update_idx]

        print("\nUpdating lab (Press ENTER to keep existing value):")

        other_names = {
            item["name"].lower()
            for idx, item in enumerate(labs)
            if idx != update_idx and "name" in item
        }

        def validate_new_name(v):
            clean = _clean_str(v, allow_empty=False)
            if clean.lower() in other_names:
                raise ValueError(f"Lab with name '{clean}' already exists")
            return clean

        l_entry["name"] = _prompt_input(
            f"Name [{l_entry.get('name')}]: ",
            validate_new_name,
            default=l_entry.get("name"),
        )

        l_entry["capacity"] = _prompt_input(
            f"Capacity [{l_entry.get('capacity')}]: ",
            lambda v: _parse_int(v, min_value=1),
            default=l_entry.get("capacity"),
        )

        l_entry["features"] = _prompt_input(
            f"Features [{', '.join(l_entry.get('features', []))}]: ",
            lambda v: _parse_list(v, allow_empty=True),
            default=l_entry.get("features", []),
        )

        update_times = _prompt_input(
            "Update availability times? (y/n) [n]: ",
            lambda v: v.lower() == "y",
            default=False,
        )

        if update_times:
            l_entry["times"] = _prompt_lab_times()

        with open(filename, "w") as f:
            json.dump(data, f, indent=4)

        print(f"Lab '{l_entry['name']}' updated successfully.")

    except Exception as error:
        print(f"Update failed: {error}")


# Handler for lab commands
def lab_handler(shell, arg):
    parts = arg.split()
    if len(parts) < 2:
        print("Usage: lab <add|list|remove|update> <filename.json>")
        return

    command = parts[0].lower()
    filename = parts[1]

    if command == "add":
        lab_add(shell, filename)
    elif command == "list":
        lab_list(shell, filename)
    elif command == "remove":
        lab_remove(shell, filename)
    elif command == "update":
        lab_update(shell, filename)
    else:
        print("Invalid command. Usage: lab <add|list|remove|update> <filename.json>")
