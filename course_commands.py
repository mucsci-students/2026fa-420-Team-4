def course_add(shell):
    #Base course identifier; repeated values create separately numbered sections
    #Python type: Course.
    #Required
    course_id = input("Enter course ID: ")

    #Optional stable section suffix; null uses the generated zero-padded input-order number
    #str | None
    #Optional
    section_id = input("Enter section ID: ")

    #Number of credit hours
    #int
    #Required
    credits = input("Enter number of credits: ")

    #Expected section enrollment that any assigned rooms and labs must accommodate
    #int
    #Required
    capacity = input("Enter capacity: ")

    #Required delivery composition of the selected class pattern
    #CourseModality
    #Allowed values: in_person / online / hybrid
    #Optional
    modality = input("Enter modality (in_person, online, hybrid): ")

    #Allowed room names; empty is valid only for compatible patterns that do not occupy a room
    #list[Room]
    #Required
    room = input("Enter room: ")

    #Acceptable labs; an empty list means the course has no lab meeting
    #list[Lab]
    #Optional
    lab = input("Enter lab: ")

    #Feature tags every assigned lecture room must provide
    #set[str]
    #Optional
    required_room_features = input("Enter required room features: ")

    #Feature tags every assigned lab must provide
    #set[str]
    #Optional
    required_lab_features = input("Enter required lab features: ")

    #Whether the lab meeting also occupies the section's assigned lecture room
    #bool
    reserve_room_during_lab = input("Reserve room during lab? (y/n): ")

    #Base course IDs whose sections cannot overlap; an empty list means no declared conflicts
    #list[Course]
    #Required
    conflicts = input("Enter conflicts: ")

    #Non-empty faculty candidates, or null to derive candidates from faculty course-preference keys
    #list[Faculty] | None
    #Required
    faculty = input("Enter faculty: ")

def course_list(shell):#
    pass

def course_remove(shell,arg):
     pass
def course_update(shell,arg):
    pass


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
        course_remove(shell,arg)
    elif command == "update":
        course_update(shell,arg)
    else:
        print("Invalid command. Usage: add | list | remove | update")