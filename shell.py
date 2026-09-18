import json
from cmd import Cmd
from scheduler import (
    Scheduler,
    load_config_from_file,
)
from scheduler.config import CombinedConfig
from scheduler.validation import validate_combined_config_data

import room_commands
import lab_commands
import course_commands
import faculty_commands

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
        self.filename: str | None = None


    def do_hello(self, arg):
        print("Hello")

    def do_new(self,arg):
        filename = arg.strip().strip("\"'")

        if filename == "":
            print("Usage: new <filename>")
            return

        try:
            self.config = load_config_from_file(
                CombinedConfig,
                filename
            )

            self.filename = filename

            print(f"Created configuration from {filename}")

        except Exception as error:
            print(f"Error creating configuration: {error}")
            
            
    def do_load(self, arg):
        filename = arg.strip()

        if filename == "":
            print("Usage: load <filename>")
            return

        try:
            self.config = load_config_from_file(
                CombinedConfig,
                filename
            )

            print(f"Loaded {filename}")

        except Exception as error:
            print(
                f"Error loading configuration: "
                f"{error}"
            )
            
            
    def do_save(self, arg):
        pass

    def do_validate(self, arg):
        pass

    def do_generate(self, arg):
        pass

    def do_view(self, arg): 
        pass

    def do_room(self, arg):
        room_commands.room_handler(self, arg)

    def do_course(self, arg):
        course_commands.course_handler(self, arg)

    def do_lab(self, arg):
        lab_commands.lab_handler(self, arg)

    def do_faculty(self, arg):
        faculty_commands.faculty_handler(self, arg)
        

    def do_exit(self, arg):
        return True


if __name__ == "__main__":
    SchedulerShell().cmdloop()