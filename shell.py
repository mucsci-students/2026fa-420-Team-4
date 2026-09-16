import json
from cmd import Cmd
from scheduler import (
    Scheduler,
    load_config_from_file,
)
from scheduler.config import CombinedConfig

from room_commands import *
from lab_commands import *
from course_commands import *
from faculty_commands import *

"""
from scheduler import (
    Scheduler,
    load_config_from_file,
)
from scheduler.config import CombinedConfig

# Load configuration
config = load_config_from_file(CombinedConfig, "example.json")

# Create scheduler
scheduler = Scheduler(config)

# Generate schedules
for schedule in scheduler.get_models():
    print("Schedule:")
    for course in schedule:
        print(f"{course.as_csv()}")

# Diagnose hard-constraint feasibility without consuming a model
diagnosis = scheduler.diagnose()

# Independently validate and score a decoded schedule
first_schedule = next(scheduler.get_models())
audit = scheduler.audit_schedule(first_schedule)
"""


class SchedulerShell(Cmd):
    intro = "Welcome to the Scheduler Shell. Type help or ? to list commands.\n"
    prompt = "scheduler> "

    def __init__(self):
        super().__init__()
        
        self.config: CombinedConfig | None = None


    def do_hello(self, arg):
        print("Hello")

    def do_room(self, arg):
        room_handler(self, arg)

    def do_course(self, arg):
        course_handler(self, arg)

    def do_lab(self, arg):
        lab_handler(self, arg)

    def do_faculty(self, arg):
        faculty_handler(self, arg)
        

    def do_exit(self, arg):
        return True


if __name__ == "__main__":
    SchedulerShell().cmdloop()