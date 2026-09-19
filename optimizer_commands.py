import json

VALID_OPTIMIZER_FLAGS = [
    "faculty_course",
    "faculty_room",
    "faculty_lab",
    "same_room",
    "same_lab",
    "pack_rooms",
    "pack_labs",
]


def _prompt_input(prompt_text, validator_func, default=None):
    while True:
        try:
            raw_val = input(prompt_text).strip()
            if not raw_val and default is not None:
                return default
            return validator_func(raw_val)
        except ValueError as e:
            print(f"  Invalid input: {e}. Please try again.\n")


def validate_flags_list(raw_flags):
    if not isinstance(raw_flags, list):
        raise ValueError("optimizer_flags must be an array/list of strings")

    invalid = [f for f in raw_flags if f not in VALID_OPTIMIZER_FLAGS]
    if invalid:
        valid_str = ", ".join(VALID_OPTIMIZER_FLAGS)
        raise ValueError(
            f"Unknown flag(s): {', '.join(invalid)}. Valid options are: {valid_str}"
        )

    # Deduplicate preserving order
    seen = set()
    return [f for f in raw_flags if not (f in seen or seen.add(f))]


def _load_data(filename):
    """Loads JSON data from file."""
    with open(filename, "r") as f:
        return json.load(f)


def _save_data(filename, data):
    """Saves JSON data to file."""
    with open(filename, "w") as f:
        json.dump(data, f, indent=4)



def optimizer_add(shell, filename):
    if filename is None:
        print("No configuration file selected.")
        return

    try:
        data = _load_data(filename)
        current_flags = data.get("optimizer_flags", [])

        available = [f for f in VALID_OPTIMIZER_FLAGS if f not in current_flags]
        if not available:
            print("\nAll valid optimizer flags are already active.")
            return

        print("\n--- Add Optimizer Flag(s) ---")
        print("Available flags to add:", ", ".join(available))

        def validate_add_input(v):
            raw_list = [f.strip() for f in v.split(",") if f.strip()]
            if not raw_list:
                raise ValueError("You must enter at least one flag to add")

            invalid = [f for f in raw_list if f not in VALID_OPTIMIZER_FLAGS]
            if invalid:
                raise ValueError(
                    f"Invalid flag(s): {', '.join(invalid)}. Must be from: {', '.join(VALID_OPTIMIZER_FLAGS)}"
                )

            already_active = [f for f in raw_list if f in current_flags]
            if already_active:
                raise ValueError(f"Already active: {', '.join(already_active)}")

            return raw_list

        flags_to_add = _prompt_input("Enter flag(s) to add (comma-separated): ", validate_add_input)

        updated_flags = current_flags + flags_to_add
        data["optimizer_flags"] = validate_flags_list(updated_flags)
        _save_data(filename, data)

        print(f"\nSuccessfully added: {', '.join(flags_to_add)}")
        print(f"Active flags: {data['optimizer_flags']}")

    except Exception as error:
        print(f"Add failed: {error}")


def optimizer_list(shell, filename):
    if filename is None:
        print("No configuration file selected.")
        return

    try:
        data = _load_data(filename)
        active_flags = data.get("optimizer_flags", [])

        print("\n--- Active Optimizer Flags ---")
        if not active_flags:
            print("  [No optimizer flags configured - default feasibility mode]")
        else:
            for idx, flag in enumerate(active_flags, 1):
                print(f"  [{idx}] {flag}")

        print("\n--- Available Valid Flags ---")
        for flag in VALID_OPTIMIZER_FLAGS:
            status = " (active)" if flag in active_flags else ""
            print(f"  - {flag}{status}")
        print("-" * 40 + "\n")

    except Exception as error:
        print(f"List failed: {error}")


def optimizer_update(shell, filename):
    if filename is None:
        print("No configuration file selected.")
        return

    try:
        data = _load_data(filename)
        current_flags = data.get("optimizer_flags", [])
        current_str = ", ".join(current_flags)

        print("\n--- Update Optimizer Flags ---")
        print("Valid flags:", ", ".join(VALID_OPTIMIZER_FLAGS))
        print("Enter comma-separated flags, or press Enter for [] (no extra optimization).\n")

        def parse_flags_str(v):
            if not v:
                return []
            raw_list = [f.strip() for f in v.split(",") if f.strip()]
            return validate_flags_list(raw_list)

        new_flags = _prompt_input(
            f"Optimizer flags [{current_str}]: ",
            parse_flags_str,
            default=current_flags,
        )

        data["optimizer_flags"] = new_flags
        _save_data(filename, data)

        print(f"\nOptimizer flags updated successfully to: {new_flags}")

    except Exception as error:
        print(f"Update failed: {error}")


def optimizer_remove(shell, filename):
    if filename is None:
        print("No configuration file selected.")
        return

    try:
        data = _load_data(filename)
        current_flags = data.get("optimizer_flags", [])

        if not current_flags:
            print("\nNo optimizer flags currently configured to remove.")
            return

        print("\n--- Remove Optimizer Flag(s) ---")
        for idx, flag in enumerate(current_flags, 1):
            print(f"  [{idx}] {flag}")

        def validate_remove_input(v):
            raw_items = [x.strip() for x in v.split(",") if x.strip()]
            if not raw_items:
                raise ValueError("You must enter at least one selection")

            to_remove = set()
            for item in raw_items:
                if item.isdigit():
                    idx = int(item) - 1
                    if not (0 <= idx < len(current_flags)):
                        raise ValueError(f"Index {item} out of range (1-{len(current_flags)})")
                    to_remove.add(current_flags[idx])
                else:
                    if item not in current_flags:
                        raise ValueError(f"Flag '{item}' is not currently active")
                    to_remove.add(item)

            return list(to_remove)

        removed_flags = _prompt_input(
            "\nEnter flag number(s) or name(s) to remove (comma-separated): ",
            validate_remove_input,
        )

        updated_flags = [f for f in current_flags if f not in removed_flags]
        data["optimizer_flags"] = updated_flags
        _save_data(filename, data)

        print(f"\nSuccessfully removed: {', '.join(removed_flags)}")
        print(f"Active flags remaining: {updated_flags}")

    except Exception as error:
        print(f"Remove failed: {error}")



def optimizer_handler(shell, arg):
    parts = arg.split()
    if len(parts) < 2:
        print("Usage: optimizer <add|list|update|remove> <filename.json>")
        return

    command = parts[0].lower()
    filename = parts[1]

    if command == "add":
        optimizer_add(shell, filename)
    elif command == "list":
        optimizer_list(shell, filename)
    elif command == "update":
        optimizer_update(shell, filename)
    elif command == "remove":
        optimizer_remove(shell, filename)
    else:
        print("Invalid command. Usage: optimizer <add|list|update|remove> <filename.json>")