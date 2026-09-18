"""
To test
new ____.json creates empty config
course add ___.json adds info to course section of selected json
load ___.json loads into scheduler
generate makes schedule



TODO: 
Save a generated schedule
Print a schedule
Validate - check docs

"""





import json
from cmd import Cmd
from scheduler import (
    Scheduler,
    load_config_from_file,
)
from scheduler.config import CombinedConfig
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

        self.config: CombinedConfig | None = None
        self.filename: str | None = None


#Creates an empty config to load in
    def do_new(self,arg):
        filename = arg.strip().strip("\"'")

        if filename == "":
            print("Usage: new <filename>.json")
            return
        else:
            empty_config = {
                "config": {
                "rooms": [],
                "labs": [],
                "courses": [],
                "faculty": []
                },
                "time_slot_config": {
                "times": {
                    "MON": [],
                    "TUE": [],
                    "WED": [],
                    "THU": [],
                    "FRI": []
                },
                "classes": []
                },
                "limit": 0,
                "optimizer_flags": []
            }
        with open(filename, "w") as f:
            json.dump(empty_config, f, indent=4)
            
        self.filename = filename

        print(f"Created new config file: {filename}")



    #Load config into scheduler       
    def do_load(self, arg):
        filename = arg.strip()

        if filename == "":
            print("Usage: load <filename> with .json extension")
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
    
    
#Generates schedules based on the loaded .json
#No need to pass anything in just type generate to make schedules
    def do_generate(self, arg):
        if self.config is None:
            print("No configuration loaded.")
            return

        scheduler = Scheduler(self.config)

        found = False

        for schedule in scheduler.get_models():
            found = True
            print("Schedule:")
            for course in schedule:
                print(course.as_csv())

        if not found:
            print("No schedules found.")


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