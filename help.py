HELP_TOPICS = {
    "times": {
        "title": "TIME BLOCKS (times)",
        "summary": "Manage allowed teaching hours and spacing for weekdays (MON-FRI).",
        "usage": "times <list|update> <filename.json>",
        "commands": {
            "list": "Display all configured weekday time blocks and spacing.",
            "update": "Set time ranges and spacing per weekday (e.g., 09:00-17:00@60).",
        },
    },
    "classes": {
        "title": "CLASS PATTERNS (classes)",
        "summary": "Manage course meeting patterns, credits, fallbacks, and lab settings.",
        "usage": "classes <add|list|update|remove> <filename.json>",
        "commands": {
            "add": "Add a new class pattern with credit count and individual meetings.",
            "list": "View all configured class patterns, credits, status, and meeting details.",
            "update": "Modify an existing class pattern or re-enter its meeting schedules.",
            "remove": "Remove a class pattern by its index number.",
        },
    },
    "flags": {
        "title": "OPTIMIZER FLAGS (flags)",
        "summary": "Configure preference optimization goals beyond basic feasibility.",
        "usage": "flags <add|list|update|remove> <filename.json>",
        "commands": {
            "add": "Add specific flag(s) to the active optimizer flags list.",
            "list": "View currently active flags alongside all available valid flags.",
            "update": "Overwrite the entire optimizer flags list (or set to []).",
            "remove": "Remove active flags by index or name.",
        },
        "flags_reference": [
            (
                "faculty_course",
                "Prefer faculty assignments matching course preferences.",
            ),
            (
                "faculty_room",
                "Prefer room assignments matching faculty room preferences.",
            ),
            ("faculty_lab", "Prefer lab assignments matching faculty lab preferences."),
            ("same_room", "Prefer courses taught by the same faculty to share a room."),
            ("same_lab", "Prefer courses taught by the same faculty to share a lab."),
            (
                "pack_rooms",
                "Prefer adjacent meetings of different courses in the same room.",
            ),
            (
                "pack_labs",
                "Prefer adjacent meetings of different courses in the same lab.",
            ),
        ],
    },
    "limit": {
        "title": "SCHEDULE GENERATION LIMIT (limit)",
        "summary": "Set the maximum number of distinct schedules the engine generates (Default: 10).",
        "usage": "limit <add|list|update|remove> <filename.json>",
        "commands": {
            "add": "Explicitly set a generation limit (defaults to 10).",
            "list": "Display the current limit setting or engine default status.",
            "update": "Change the schedule generation limit value.",
            "remove": "Remove the limit key to revert to engine default (10).",
        },
    },
    "courses": {
        "title": "COURSE CONFIGURATIONS (courses)",
        "summary": "Manage individual course sections, capacity, modalities, rooms, labs, and faculty.",
        "usage": "course <add|list|update|remove> <filename.json>",
        "commands": {
            "add": "Interactive prompt to create a new course section with options for modality, rooms, labs, features, conflicts, and faculty.",
            "list": "View summary table of all configured courses including modality, rooms, labs, capacity, and faculty.",
            "update": "Select a course by ID to update its fields (press Enter to keep existing values).",
            "remove": "Remove a course section by its Course ID (prompts for selection if duplicates exist).",
        },
    },
    "faculty": {
        "title": "FACULTY CONFIGURATIONS (faculty)",
        "summary": "Manage faculty profiles, credit limits, teaching days, availability, and preferences.",
        "usage": "faculty <add|list|update|remove> <filename.json>",
        "commands": {
            "add": "Interactive prompt to create a new faculty member with credit bounds, teaching day limits, daily availability windows, and course/room/lab preference scores (0-10).",
            "list": "View summary table of all configured faculty members including credit ranges, unique course limits, max/mandatory days, and active availability days.",
            "update": "Select a faculty member by name to update their workload constraints, availability, or preference mappings (press Enter to keep existing values).",
            "remove": "Remove a faculty member profile by name from the configuration file.",
        },
    },
    "rooms": {
        "title": "ROOM CONFIGURATIONS (room)",
        "summary": "Manage room assets, seating capacity, features, and availability windows.",
        "usage": "room <add|list|update|remove> <filename.json>",
        "commands": {
            "add": "Interactive prompt to add a room with name, capacity, features, and restricted hours.",
            "list": "View summary table of all configured rooms, capacities, features, and restrictions.",
            "update": "Select a room by name to update fields or availability times.",
            "remove": "Remove a room by name from the configuration file.",
        },
    },
    "labs": {
        "title": "LAB CONFIGURATIONS (lab)",
        "summary": "Manage specialized lab spaces, capacity, features, and availability windows.",
        "usage": "lab <add|list|update|remove> <filename.json>",
        "commands": {
            "add": "Interactive prompt to add a lab with name, capacity, features, and restricted hours.",
            "list": "Display all configured labs, capacities, features, and availability status.",
            "update": "Select a lab by name to update capacity, features, or availability times.",
            "remove": "Remove a lab by name from the configuration file.",
        },
    },
}


def show_general_help():
    print("\n" + "=" * 55)
    print("           SCHEDULER CLI COMMAND REFERENCE")
    print("=" * 55)

    for topic_key, data in HELP_TOPICS.items():
        print(f"\n[{data['title']}]")
        print(f"  Summary: {data['summary']}")
        print(f"  Usage:   {data['usage']}")

    print("\n" + "-" * 55)
    print("  Type 'help <topic>' for details (e.g., 'help flags').")
    print("  Type 'exit' to quit the shell.")
    print("-" * 55 + "\n")


def help_handler(shell, arg=""):
    show_general_help()
