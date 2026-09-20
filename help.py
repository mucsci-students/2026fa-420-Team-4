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
    "optimizer": {
        "title": "OPTIMIZER FLAGS (optimizer)",
        "summary": "Configure preference optimization goals beyond basic feasibility.",
        "usage": "optimizer <add|list|update|remove> <filename.json>",
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
            (
                "same_room",
                "Prefer eligible courses taught by one faculty member to share a resource.",
            ),
            (
                "same_lab",
                "Prefer eligible courses taught by one faculty member to share a resource.",
            ),
            (
                "pack_rooms",
                "Prefer different courses to use the same resource at adjacent meetings. Online meetings and unreserved lab meetings do not count",
            ),
            (
                "pack_labs",
                "Prefer different courses to use the same resource at adjacent meetings. Online meetings and unreserved lab meetings do not count",
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
    "course": {
        "title": "COURSE CONFIGURATIONS (course)",
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
    "room": {
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
    "lab": {
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
    "new": {
        "title": "CREATE NEW CONFIGURATION (new)",
        "summary": "Generate a new empty scheduler JSON configuration file template.",
        "usage": "new <filename.json>",
        "description": (
            "Creates a new, unpopulated JSON configuration file pre-structured with empty sections\n"
            "for rooms, labs, courses, faculty, time slots, class patterns, limits, and optimizer flags."
        ),
    },
    "load": {
        "title": "LOAD CONFIGURATION (load)",
        "summary": "Load a JSON configuration file into the scheduler.",
        "usage": "load <filename.json>",
        "description": (
            "Reads and parses the specified JSON file into a CombinedConfig object in memory.\n"
            "This configuration is used directly by the 'generate' command to solve schedules."
        ),
    },
    "save": {
        "title": "SAVE CONFIGURATION (save)",
        "summary": "Save the currently loaded in-memory configuration to a JSON file.",
        "usage": "save <filename.json>",
        "description": (
            "Writes the active in-memory CombinedConfig object out to the specified file path."
        ),
    },
    "validate": {
        "title": "VALIDATE CONFIGURATION FILE (validate)",
        "summary": "Perform schema and constraint diagnostic checks on a configuration JSON file.",
        "usage": "validate <filename.json>",
        "description": (
            "Parses and runs diagnostics against a target configuration JSON file.\n"
            "Outputs diagnostic codes, error paths, and messages if invalid, or prints\n"
            "the configuration fingerprint if valid."
        ),
    },
    "generate": {
        "title": "GENERATE SCHEDULES (generate)",
        "summary": "Runs the scheduler on the currently loaded configuration.",
        "usage": "generate",
        "description": (
            "Iterates through valid schedule solutions and outputs each assigned course in CSV format."
        ),
    },
    "view": {
        "title": "VIEW SCHEDULE (view)",
        "summary": "Display summary information or inspect active schedule data.",
        "usage": "view",
        "description": ("Inspects and outputs generated schedule details."),
    },
    "exit": {
        "title": "EXIT SHELL (exit)",
        "summary": "Terminate and close the scheduler CLI environment.",
        "usage": "exit",
        "description": "Exits the Scheduler Shell command loop.",
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
    print("  Type 'help <topic>' for details (e.g., 'help new' or 'help room').")
    print("  Type 'exit' to quit the shell.")
    print("-" * 55 + "\n")


def show_topic_help(topic):
    topic_key = topic.lower().strip()
    data = HELP_TOPICS.get(topic_key)

    if not data:
        print(f"\nUnknown help topic '{topic}'.")
        print(f"Available topics: {', '.join(HELP_TOPICS.keys())}\n")
        return

    print("\n" + "=" * 50)
    print(f"  {data['title']}")
    print("=" * 50)
    print(f"Summary: {data['summary']}")
    print(f"Usage:   {data['usage']}\n")

    if "description" in data:
        print("Details:")
        print(f"  {data['description']}\n")

    if "commands" in data:
        print("Commands:")
        for cmd_name, cmd_desc in data["commands"].items():
            print(f"  {topic_key} {cmd_name:<8} - {cmd_desc}")

    if "flags_reference" in data:
        print("\nValid Flags Reference:")
        for flag_name, flag_desc in data["flags_reference"]:
            print(f"  - {flag_name:<16} : {flag_desc}")

    print("-" * 50 + "\n")


def help_handler(shell, arg=""):
    topic = arg.strip()
    if topic:
        show_topic_help(topic)
    else:
        show_general_help()
