import json

from scheduler.config import (
    CombinedConfig,
    CourseConfig,
)

#gets string from user
def get_clean_str(prompt, required=True, allow_none=False):
    while True:
        val = input(prompt).strip()
        if not val:
            if allow_none:
                return None
            if not required:
                return ""
            print("Error: Field cannot be blank or contain only whitespace.")
            continue
        return val

#gets list from user
def get_clean_list(prompt, allow_empty=True):
    raw = input(prompt)
    items = [v.strip() for v in raw.split(",") if v.strip()]
    

#Adds a course to the config that was created
def course_add(shell, filename):
    if filename is None:
        print("No configuration file selected.")
        return

    try:
        with open(filename, "r") as f:
            data = json.load(f)

        print("\n--- Add New Course ---")
        course_id = get_clean_str("Enter course ID (required): ")
        
        # Optional section_id
        sec_input = input("Enter section ID (optional, press Enter for null): ").strip()
        section_id = sec_input if sec_input else None

        # Number of credits
        credits = int(input("Enter number of credits (positive integer): "))
        if credits <= 0:
            raise ValueError("Credits must be a positive integer.")

        # Expected section enrollment
        capacity = int(input("Enter capacity (positive integer): "))
        if capacity <= 0:
            raise ValueError("Capacity must be a positive integer.")

        # Modality validation
        VALID_MODALITIES = {"in_person", "online", "hybrid"}
        modality = input("Enter modality (in_person, online, hybrid) [default: in_person]: ").strip().lower()
        if not modality:
            modality = "in_person"
        elif modality not in VALID_MODALITIES:
            raise ValueError(f"Invalid modality. Must be one of: {', '.join(VALID_MODALITIES)}")

        # Rules for Online courses
        if modality == "online":
            print("Note: Online modality set. Rooms and Labs will be forced to empty lists.")
            room = []
            lab = []
        else:
            room = get_clean_list("Enter Room(s) (comma-separated, press Enter for empty): ", allow_empty=True)
            lab = get_clean_list("Enter Lab(s) (comma-separated, press Enter for empty): ", allow_empty=True)

        # Features
        req_room_features = get_clean_list("Enter required room features (comma-separated): ", allow_empty=True)
        req_lab_features = get_clean_list("Enter required lab features (comma-separated): ", allow_empty=True)

        # Reserve room during lab
        reserve_str = input("Reserve room during lab? (y/n) [default: y]: ").strip().lower()
        reserve_room_during_lab = False if reserve_str == "n" else True

        # Conflicts
        conflicts = get_clean_list("Enter conflict course IDs (comma-separated): ", allow_empty=True)
        if course_id in conflicts:
            raise ValueError("A course cannot list itself in its conflicts.")

        # Faculty handling
        fac_input = input("Enter faculty candidates (comma-separated, or press Enter to derive from preferences): ").strip()
        if not fac_input:
            faculty = None  # null in JSON
        else:
            faculty = [f.strip() for f in fac_input.split(",") if f.strip()]
            if len(faculty) != len(set(faculty)):
                raise ValueError("Faculty list contains duplicate names.")

        # Build course dict adhering to schema
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
            "faculty": faculty
        }

        if "config" not in data or "courses" not in data["config"]:
            data.setdefault("config", {})["courses"] = []

        data["config"]["courses"].append(course)

        with open(filename, "w") as f:
            json.dump(data, f, indent=4)

        print(f"Successfully added course '{course_id}'.")

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
                f"[{idx}] {course_id}{sec} | Credits: {credits} | Capacity: {capacity} | "
                f"Rooms: [{rooms}] | Labs: [{labs}] | Faculty: {fac_str}"
            )
        print("-" * 35 + "\n")

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
            print("No courses in config")
            return

        #print list so user can pick from it
        course_list(shell, filename)

        target_id = input("Enter course ID to remove: ").strip()
        matching = [i for i, c in enumerate(courses) if c.get("course_id") == target_id]

        if not matching:
            print(f"No course found with ID '{target_id}'.")
            return

        # If duplicate course IDs exist, ask which entry/index to remove
        if len(matching) > 1:
            print(f"Found {len(matching)} entries matching '{target_id}':")
            for pos, idx in enumerate(matching, 1):
                c = courses[idx]
                fac = c.get("faculty")
                print(f"  {pos}. Rooms: {c.get('room')} | Faculty: {fac}")

            choice = int(input("Select entry number to remove: ")) - 1
            if 0 <= choice < len(matching):
                remove_idx = matching[choice]
            else:
                print("Invalid choice selection.")
                return
        else:
            remove_idx = matching[0]

        removed = courses.pop(remove_idx)

        with open(filename, "w") as f:
            json.dump(data, f, indent=4)

        print(f"Course '{removed.get('course_id')}' removed successfully.")

    except Exception as error:
        print(f"Remove failed: {error}")


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
