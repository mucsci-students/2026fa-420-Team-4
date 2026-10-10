
#   This is all of the data that we are looking to contain...

class Course():
    def __init__(self):
        self.course_id = 0
        self.section_id = None
        self.credits = 0
        self.capacity = 0
        self.modality = ""
        self.room = []
        self.lab = []
        self.req_room_features = []
        self.req_lab_features = []
        self.reserve_room_during_lab = True
        self.conflicts = []
        self.faculty = ""