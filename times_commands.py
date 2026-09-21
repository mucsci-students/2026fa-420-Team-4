import json
import re

VALID_DAYS = ["MON", "TUE", "WED", "THU", "FRI"]
VALID_DELIVERIES = {"in_person", "online"}
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
    if not val and not allow_empty:
        raise ValueError("Field cannot be blank or contain only whitespace")
    return val


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


def _parse_time_str(time_str):
    if not TIME_REGEX.match(time_str):
        raise ValueError("Time must be in 24-hour HH:MM format (00:00 to 23:59)")
    return time_str


def _get_times_dict(data):
    """Helper to locate 'times' in time_slot_config or fallback to config."""
    if "time_slot_config" in data and "times" in data["time_slot_config"]:
        return data["time_slot_config"]["times"], "time_slot_config"
    if "config" in data and "times" in data["config"]:
        return data["config"]["times"], "config"
    return {}, "time_slot_config"


def _get_classes_list(data):
    """Helper to locate 'classes' in time_slot_config or fallback to config."""
    if "time_slot_config" in data and "classes" in data["time_slot_config"]:
        return data["time_slot_config"]["classes"], "time_slot_config"
    if "config" in data and "classes" in data["config"]:
        return data["config"]["classes"], "config"
    return [], "time_slot_config"


# Time Blocks for use with "times" commands


# List the time blocks on a given config
def times_list(shell, filename):
    if filename is None:
        print("No configuration file selected.")
        return

    try:
        with open(filename, "r") as f:
            data = json.load(f)

        times, _ = _get_times_dict(data)
        if not times:
            print("No time blocks configured.")
            return

        print("\n--- Configured Time Blocks ---")
        for day in VALID_DAYS:
            blocks = times.get(day, [])
            if not blocks:
                print(f"  {day}: [MISSING / EMPTY]")
            else:
                block_strs = [
                    f"{b.get('start')}-{b.get('end')} (spacing: {b.get('spacing')}m)"
                    for b in blocks
                ]
                print(f"  {day}: {', '.join(block_strs)}")
        print("-" * 40 + "\n")

    except Exception as error:
        print(f"List failed: {error}")


# Update the time blocks on the given config
def times_update(shell, filename):
    if filename is None:
        print("No configuration file selected.")
        return

    try:
        with open(filename, "r") as f:
            data = json.load(f)

        print("\n--- Update Time Blocks ---")
        print("Every weekday (MON-FRI) requires at least one valid time block.\n")

        times_dict = {}

        for day in VALID_DAYS:
            print(f"[{day}] Enter time blocks (format: HH:MM-HH:MM@SPACING)")
            print("Example: 09:00-17:00@60  OR  08:00-12:00@30, 13:00-17:00@30")

            def validate_day_blocks(val):
                raw_blocks = [b.strip() for b in val.split(",") if b.strip()]
                if not raw_blocks:
                    raise ValueError(f"{day} must contain at least one time block")

                parsed_blocks = []
                for raw_b in raw_blocks:
                    if "@" not in raw_b:
                        raise ValueError(
                            f"Missing spacing for block '{raw_b}'. Use HH:MM-HH:MM@SPACING"
                        )

                    time_part, spacing_part = raw_b.split("@", 1)

                    time_range = _parse_time_range(time_part.strip())
                    spacing = _parse_int(spacing_part.strip(), min_value=1)

                    parsed_blocks.append(
                        {
                            "start": time_range["start"],
                            "spacing": spacing,
                            "end": time_range["end"],
                        }
                    )
                return parsed_blocks

            times_dict[day] = _prompt_input(f"Blocks for {day}: ", validate_day_blocks)

        _, key_section = _get_times_dict(data)
        if key_section not in data:
            data[key_section] = {}

        data[key_section]["times"] = times_dict

        with open(filename, "w") as f:
            json.dump(data, f, indent=4)

        print("\nTime blocks updated successfully.")

    except Exception as error:
        print(f"Update failed: {error}")


# Class pattern for use with "classes" command


def _prompt_meetings():
    """Prompts for a list of meetings for a class pattern."""
    print("\n-- Enter Meetings for Pattern --")
    meetings = []

    while True:
        add_more = _prompt_input(
            "Add a meeting? (y/n) [y]: ",
            lambda v: v.lower() in ("y", "yes"),
            default=True,
        )
        if not add_more:
            break

        def validate_day(v):
            day_upper = v.strip().upper()
            if day_upper not in VALID_DAYS:
                raise ValueError(f"Day must be one of {', '.join(VALID_DAYS)}")
            return day_upper

        day = _prompt_input("Day (MON, TUE, WED, THU, FRI): ", validate_day)

        duration = _prompt_input(
            "Duration in minutes: ",
            lambda v: _parse_int(v, min_value=1),
        )

        def validate_delivery(v):
            deliv = v.strip().lower()
            if deliv not in VALID_DELIVERIES:
                raise ValueError(
                    f"Delivery must be one of: {', '.join(VALID_DELIVERIES)}"
                )
            return deliv

        delivery = _prompt_input(
            "Delivery (in_person / online) [in_person]: ",
            validate_delivery,
            default="in_person",
        )

        lab = _prompt_input(
            "Is lab? (y/n) [n]: ",
            lambda v: v.lower() == "y",
            default=False,
        )

        def validate_meeting_start(v):
            if not v or v.lower() == "null":
                return None
            return _parse_time_str(v)

        mtg_start = _prompt_input(
            "Meeting start time (HH:MM or Enter for null): ",
            validate_meeting_start,
            default=None,
        )

        meeting = {
            "day": day,
            "duration": duration,
            "delivery": delivery,
            "lab": lab,
        }
        if mtg_start:
            meeting["start_time"] = mtg_start

        meetings.append(meeting)

    return meetings


# Add a class pattern to the given config
def classes_add(shell, filename):
    if filename is None:
        print("No configuration file selected.")
        return

    try:
        with open(filename, "r") as f:
            data = json.load(f)

        print("\n--- Add New Class Pattern ---")

        credits = _prompt_input(
            "Credits (positive integer): ",
            lambda v: _parse_int(v, min_value=1),
        )

        def validate_start_time(v):
            if not v or v.lower() == "null":
                return None
            return _parse_time_str(v)

        pattern_start_time = _prompt_input(
            "Pattern fallback start time (HH:MM or Enter for null): ",
            validate_start_time,
            default=None,
        )

        disabled = _prompt_input(
            "Disable this pattern? (y/n) [n]: ",
            lambda v: v.lower() == "y",
            default=False,
        )

        meetings = _prompt_meetings() or []

        pattern_entry = {
            "credits": credits,
            "meetings": meetings,
            "disabled": disabled,
        }
        if pattern_start_time:
            pattern_entry["start_time"] = pattern_start_time

        _, key_section = _get_classes_list(data)
        if key_section not in data:
            data[key_section] = {}
        if "classes" not in data[key_section]:
            data[key_section]["classes"] = []

        data[key_section]["classes"].append(pattern_entry)

        with open(filename, "w") as f:
            json.dump(data, f, indent=4)

        print("\nClass pattern added successfully.")

    except Exception as error:
        print(f"Failed to add class pattern: {error}")


# List the class patterns in the given config
def classes_list(shell, filename):
    if filename is None:
        print("No configuration file selected.")
        return

    try:
        with open(filename, "r") as f:
            data = json.load(f)

        classes, _ = _get_classes_list(data)
        if not classes:
            print("No class patterns found in configuration.")
            return

        print(f"\n--- Class Patterns List ({len(classes)} Total) ---")
        for idx, cp in enumerate(classes, 1):
            creds = cp.get("credits", "N/A")
            status = "Disabled" if cp.get("disabled", False) else "Enabled"
            fallback_start = cp.get("start_time") or "None"
            meetings = cp.get("meetings") or []

            mtg_strs = []
            for m in meetings:
                lab_flag = " [LAB]" if m.get("lab") else ""
                st = f" @ {m.get('start_time')}" if m.get("start_time") else ""
                deliv = m.get("delivery", "in_person")
                mtg_strs.append(
                    f"{m.get('day')} {m.get('duration')}m ({deliv}){lab_flag}{st}"
                )

            print(
                f"[{idx}] Credits: {creds} | Status: {status} | Fallback Start: {fallback_start}\n"
                f"     Meetings: {'; '.join(mtg_strs) if mtg_strs else 'None'}"
            )
        print("-" * 40 + "\n")

    except Exception as error:
        print(f"List failed: {error}")


# Remove a class pattern in the given config
def classes_remove(shell, filename):
    if filename is None:
        print("No configuration file selected.")
        return

    try:
        with open(filename, "r") as f:
            data = json.load(f)

        classes, key_section = _get_classes_list(data)
        if not classes:
            print("No class patterns available to remove.")
            return

        classes_list(shell, filename)

        def validate_choice(v):
            idx = int(v) - 1
            if not (0 <= idx < len(classes)):
                raise ValueError(f"Selection must be between 1 and {len(classes)}")
            return idx

        remove_idx = _prompt_input("Select pattern number to remove: ", validate_choice)

        removed = classes.pop(remove_idx)

        with open(filename, "w") as f:
            json.dump(data, f, indent=4)

        print(f"Class pattern #{remove_idx + 1} removed successfully.")

    except Exception as error:
        print(f"Remove failed: {error}")


# Update deatils of a class pattern in the given config
def classes_update(shell, filename):
    if filename is None:
        print("No configuration file selected.")
        return

    try:
        with open(filename, "r") as f:
            data = json.load(f)

        classes, key_section = _get_classes_list(data)
        if not classes:
            print("No class patterns available to update.")
            return

        classes_list(shell, filename)

        def validate_choice(v):
            idx = int(v) - 1
            if not (0 <= idx < len(classes)):
                raise ValueError(f"Selection must be between 1 and {len(classes)}")
            return idx

        update_idx = _prompt_input("Select pattern number to update: ", validate_choice)
        cp = classes[update_idx]

        print(
            f"\nUpdating Pattern #{update_idx + 1} (Press ENTER to keep existing value):"
        )

        cp["credits"] = _prompt_input(
            f"Credits [{cp.get('credits')}]: ",
            lambda v: _parse_int(v, min_value=1),
            default=cp.get("credits"),
        )

        def validate_start_time(v):
            if v.lower() == "null":
                return None
            return _parse_time_str(v)

        cp["start_time"] = _prompt_input(
            f"Pattern fallback start time [{cp.get('start_time')}]: ",
            validate_start_time,
            default=cp.get("start_time"),
        )

        cp["disabled"] = _prompt_input(
            f"Disable pattern? (y/n) [{'y' if cp.get('disabled') else 'n'}]: ",
            lambda v: v.lower() == "y",
            default=cp.get("disabled", False),
        )

        update_mtgs = _prompt_input(
            "Re-enter all meetings for this pattern? (y/n) [n]: ",
            lambda v: v.lower() == "y",
            default=False,
        )

        if update_mtgs:
            cp["meetings"] = _prompt_meetings() or []

        with open(filename, "w") as f:
            json.dump(data, f, indent=4)

        print(f"Class pattern #{update_idx + 1} updated successfully.")

    except Exception as error:
        print(f"Update failed: {error}")


# Handler for times commands
def times_handler(shell, arg):
    parts = arg.split()
    if len(parts) < 2:
        print("Usage: times <list|update> <filename.json>")
        return

    command = parts[0].lower()
    filename = parts[1]

    if command == "list":
        times_list(shell, filename)
    elif command == "update":
        times_update(shell, filename)
    else:
        print("Invalid command. Usage: times <list|update> <filename.json>")


# Handler for classes commands
def classes_handler(shell, arg):
    parts = arg.split()
    if len(parts) < 2:
        print("Usage: classes <add|list|remove|update> <filename.json>")
        return

    command = parts[0].lower()
    filename = parts[1]

    if command == "add":
        classes_add(shell, filename)
    elif command == "list":
        classes_list(shell, filename)
    elif command == "remove":
        classes_remove(shell, filename)
    elif command == "update":
        classes_update(shell, filename)
    else:
        print(
            "Invalid command. Usage: classes <add|list|remove|update> <filename.json>"
        )
