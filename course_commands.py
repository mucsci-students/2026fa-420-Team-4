def course_add(shell,arg):
    #Base course identifier; repeated values create separately numbered sections
    #Python type: Course.
    course_id = input("Enter course ID: ")

    #Optional stable section suffix; null uses the generated zero-padded input-order number
    #str | None
    section_id = input("Enter section ID: ")

    #Number of credit hours
    #int
    credits = input("Enter number of credits: ")

    #Expected section enrollment that any assigned rooms and labs must accommodate
    #int
    capacity = input("Enter capacity: ")

    #Required delivery composition of the selected class pattern
    #CourseModality
    #llowed values: in_person / online / hybrid
    modality = input("Enter modality (in_person, online, hybrid): ")

    #Allowed room names; empty is valid only for compatible patterns that do not occupy a room
    #list[Room]
    room = input("Enter room: ")

    #Acceptable labs; an empty list means the course has no lab meeting
    #list[Lab]
    lab = input("Enter lab: ")

    #Feature tags every assigned lecture room must provide
    #set[str]
    required_room_features = input("Enter required room features: ")

    #Feature tags every assigned lab must provide
    #set[str]
    required_lab_features = input("Enter required lab features: ")

    #Whether the lab meeting also occupies the section's assigned lecture room
    #bool
    reserve_room_during_lab = input("Reserve room during lab? (y/n): ")

    #Base course IDs whose sections cannot overlap; an empty list means no declared conflicts
    #list[Course]
    conflicts = input("Enter conflicts: ")

    #Non-empty faculty candidates, or null to derive candidates from faculty course-preference keys
    #list[Faculty] | None
    faculty = input("Enter faculty: ")