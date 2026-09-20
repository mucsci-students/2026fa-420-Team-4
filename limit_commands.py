import json

DEFAULT_LIMIT = 10


def _prompt_input(prompt_text, validator_func, default=None):
    while True:
        try:
            raw_val = input(prompt_text).strip()
            if not raw_val and default is not None:
                return default
            return validator_func(raw_val)
        except ValueError as e:
            print(f"  Invalid input: {e}. Please try again.\n")


def validate_limit(value):
    try:
        parsed = int(value)
    except (ValueError, TypeError):
        raise ValueError("Limit must be an integer")

    if parsed < 1:
        raise ValueError("Limit must be a positive integer (>= 1)")

    return parsed


def _load_data(filename):
    with open(filename, "r") as f:
        return json.load(f)


def _save_data(filename, data):
    with open(filename, "w") as f:
        json.dump(data, f, indent=4)


def limit_add(shell, filename):
    if filename is None:
        print("No configuration file selected.")
        return

    try:
        data = _load_data(filename)

        if "limit" in data:
            print(f"\nLimit is already configured as {data['limit']}. Use 'update' to change it.")
            return

        print("\n--- Add Schedule Generation Limit ---")
        new_limit = _prompt_input(
            f"Enter limit [{DEFAULT_LIMIT}]: ",
            validate_limit,
            default=DEFAULT_LIMIT,
        )

        data["limit"] = new_limit
        _save_data(filename, data)

        print(f"\nLimit successfully added and set to {new_limit}.")

    except Exception as error:
        print(f"Add limit failed: {error}")


def limit_list(shell, filename):
    if filename is None:
        print("No configuration file selected.")
        return

    try:
        data = _load_data(filename)

        print("\n--- Schedule Generation Limit ---")
        if "limit" in data:
            print(f"  Current limit: {data['limit']}")
        else:
            print(f"  Current limit: Omitted (Defaults to {DEFAULT_LIMIT})")
        print("-" * 40 + "\n")

    except Exception as error:
        print(f"List limit failed: {error}")


def limit_update(shell, filename):
    if filename is None:
        print("No configuration file selected.")
        return

    try:
        data = _load_data(filename)
        current_limit = data.get("limit", DEFAULT_LIMIT)

        print("\n--- Update Schedule Generation Limit ---")
        new_limit = _prompt_input(
            f"Enter limit [{current_limit}]: ",
            validate_limit,
            default=current_limit,
        )

        data["limit"] = new_limit
        _save_data(filename, data)

        print(f"\nLimit successfully updated to {new_limit}.")

    except Exception as error:
        print(f"Update limit failed: {error}")


def limit_remove(shell, filename):
    if filename is None:
        print("No configuration file selected.")
        return

    try:
        data = _load_data(filename)

        if "limit" not in data:
            print(f"\nNo explicit limit found in configuration. Already using the default ({DEFAULT_LIMIT}).")
            return

        removed_val = data.pop("limit")
        _save_data(filename, data)

        print(f"\nSuccessfully removed limit ({removed_val}). Default is ({DEFAULT_LIMIT}).")

    except Exception as error:
        print(f"Remove limit failed: {error}")



def limit_handler(shell, arg):
    parts = arg.split()
    if len(parts) < 2:
        print("Usage: limit <add|list|update|remove> <filename.json>")
        return

    command = parts[0].lower()
    filename = parts[1]

    if command == "add":
        limit_add(shell, filename)
    elif command == "list":
        limit_list(shell, filename)
    elif command == "update":
        limit_update(shell, filename)
    elif command == "remove":
        limit_remove(shell, filename)
    else:
        print("Invalid command. Usage: limit <add|list|update|remove> <filename.json>")