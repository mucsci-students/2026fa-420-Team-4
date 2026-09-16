from pydantic import ValidationError
from scheduler.config import CourseConfig

def course_add(shell):
    #Base course identifier; repeated values create separately numbered sections
    #Python type: Course.
    #Required
    if shell.config is None:
        print("No config loaded")
        return
    course_id = input("Enter course ID: ").strip()

    #Optional stable section suffix; null uses the generated zero-padded input-order number
    #str | None
    #Optional
    section_id = input("Enter section ID (optional): ").strip()
    if section_id == "":
        section_id = None

    #Number of credit hours
    #int
    #Required
    credits = int(input("Enter number of credits: "))

    #Expected section enrollment that any assigned rooms and labs must accommodate
    #int
    #Required
    capacity = int(input("Enter capacity: "))

    #Required delivery composition of the selected class pattern
    #CourseModality
    #Allowed values: in_person / online / hybrid
    #Optional
    modality = input("Enter modality (in_person, online, hybrid): ").strip()

    #Allowed room names; empty is valid only for compatible patterns that do not occupy a room
    #list[Room]
    #Required
    room_input = input("Enter rooms (comma-separated): ")
    room = [
        item.strip()
        for item in room_input.split(",")
        if item.strip()
    ]

    #Acceptable labs; an empty list means the course has no lab meeting
    #list[Lab]
    #Optional
    lab_input = input("Enter rooms (comma-separated): ")
    lab = [
        item.strip()
        for item in lab_input.split(",")
        if item.strip()
    ]

    #Feature tags every assigned lecture room must provide
    #set[str]
    #Optional
    required_room_features_input = input("Enter required room features (comma-separated): ")
    required_room_features = {
        item.strip()
        for item in required_room_features_input.split(",")
        if item.strip()
    }

    #Feature tags every assigned lab must provide
    #set[str]
    #Optional
    required_lab_features_input = input("Enter required lab features (comma-separated): ")
    required_lab_features = {
        item.strip()
        for item in required_lab_features_input.split(",")
        if item.strip()
    }

    #Whether the lab meeting also occupies the section's assigned lecture room
    #bool
    reserve_input = input("Reserve room during lab? (y/n): ").strip()
    if reserve_input.lower() == "y":
        reserve_room_during_lab = True
    elif reserve_input.lower() == "n":
        reserve_room_during_lab = False
    else:
        print("Enter y or n")
        return
    #Base course IDs whose sections cannot overlap; an empty list means no declared conflicts
    #list[Course]
    #Required
    conflicts_input = input("Enter conflicts (comma-separated): ")
    conflicts = [
        item.strip()
        for item in conflicts_input.split(",")
        if item.strip()
    ]

    #Non-empty faculty candidates, or null to derive candidates from faculty course-preference keys
    #list[Faculty] | None
    #Required
    faculty_input = input("Enter faculty (comma-separated or blank for automatic): ")
    if faculty_input.strip() == "":
        faculty = None
    else:
        faculty = [
            item.strip()
            for item in faculty_input.split(",")
            if item.strip()
        ]
    try:
        course = CourseConfig(
            course_id=course_id,
            section_id=section_id,
            credits=credits,
            capacity=capacity,
            modality=modality,
            room=room,
            lab=lab,
            required_room_features=required_room_features,
            required_lab_features=required_lab_features,
            reserve_room_during_lab=reserve_room_during_lab,
            conflicts=conflicts,
            faculty=faculty,
        )
        shell.config.config.courses.append(course)
    
        shell.config.config = shell.config.config.model_validate(shell.config.config.model_dump())
    
        print("Course added")
    
    
    except ValidationError as error:
        print("Course could not be added:")
        print(error)




def course_list(shell):
    if shell.config is None:
        print("No configuration loaded.")
        return

    courses = shell.config.config.courses

    if not courses:
        print("No courses configured.")
        return

    for course in courses:
        print(
            f"{course.course_id}"
            f".{course.section_id if course.section_id else ''}"
            f" | Credits: {course.credits}"
            f" | Capacity: {course.capacity}"
            f" | Modality: {course.modality.value}"
            f" | Rooms: {course.room}"
            f" | Labs: {course.lab}"
            f" | Faculty: {course.faculty}"
        )




def course_remove(shell,arg):
    if shell.config is None:
        print("No configuration loaded.")
        return

    parts = arg.split()

    if len(parts) < 2:
        print("Usage: course remove <course_id>")
        return
    
    if len(shell.config.config.courses) == 1:
        print("Cannot remove the last course.")
        return

    course_id = parts[1]

    courses = shell.config.config.courses

    for course in courses:
        if course.course_id == course_id:
            courses.remove(course)

            try:
                shell.config.config = shell.config.config.model_validate(
                    shell.config.config.model_dump()
                )
                print("Course removed.")
            except ValidationError as error:
                print("Configuration became invalid:")
                print(error)

            return

    print("Course not found.")
    
    
    
def course_update(shell,arg):
    if shell.config is None:
        print("No configuration loaded.")
        return

    parts = arg.split()

    if len(parts) < 2:
        print("Usage: course update <course_id>")
        return

    course_id = parts[1]

    for course in shell.config.config.courses:
        if course.course_id == course_id:
            print("Course found.")
            print("Course update functionality goes here.")
            return

    print("Course not found.")


def course_handler(shell, arg):
    parts = arg.split()

    if len(parts) == 0:
        print("No command provided. Usage: add | list | remove | update")
        return

    command = parts[0]

    if command == "add":
        course_add(shell)

    elif command == "list":
        course_list(shell)

    elif command == "remove":
        course_remove(shell, arg)

    elif command == "update":
        course_update(shell, arg)

    else:
        print("Invalid command. Usage: add | list | remove | update")
