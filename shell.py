"""
To test
new ____.json creates empty config
course add ___.json adds info to course section of selected json
load ___.json loads into scheduler
generate makes schedule dont need to specify the file automatically uses what was loaded in



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
    validate_combined_config_data,
)
from scheduler.config import CombinedConfig
import room_commands
import lab_commands
import course_commands
import faculty_commands
import times_commands
import optimizer_commands
import limit_commands
import help

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
    intro = "Welcome to the Scheduler Shell. Type help to list commands.\n"
    prompt = "scheduler> "
    def __init__(self):
        super().__init__()

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
        filename = arg.strip()
        if filename == "":
            print("Usage: save the currently loaded configuration to <filename> with .json extension")
            return
        if filename[-5:] != ".json":
            print("File name must include .json extension")
            return
        if not self.config == None:
            # opens specified file and writes config data onto it
            with open(filename, "w") as file:
                file.write(self.config.model_dump_json())
            print("Config data successfully saved to " + filename)
        else:
            print("There is no currently loaded config data to save.")

    def do_validate(self, arg):
        # mostly gotten from the diagnostics and auditing section
        # of the scheduler documentation linked below
        # https://mucsci-scheduler.docs.buildwithfern.com/concepts/diagnostics-and-auditing
        filename = arg.strip()
        if filename == "":
            print("Usage: validate the contents of config file <filename>")
            return
        # reads specified file and validates its contents
        try:
            with open(filename, "r") as data:
                v_results = validate_combined_config_data(json.loads(data.read()))
        except FileNotFoundError:
            print("File could not be found.")
            return
        if not v_results.is_valid:
            print("Config data is invalid.")
            for finding in v_results.diagnostics:
                print(finding.code, finding.path, finding.message)
        else:
            print("Config data has been validated.")
            print(v_results.configuration_fingerprint)
    
    
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
        if self.config == None:
            print("There is no currently loaded config data to view.")
            return
        data = self.config.model_dump()
        # data contains config, time_slot_config, and limit
        # config contains rooms, labs, courses, and faculty
        # time_slot_config contains times and classes
        print("Maximum generated schedules: " + str(data["limit"]))
        for room in data["config"]["rooms"]:
            print("Room " + room["name"] + ": Capacity of " + str(room["capacity"]))
            if len(room["features"]) != 0:
                features = ''
                for feature in room["features"]:
                    features += feature + ", "
                print("Features include " + features[:-2])
            else:
                print("Room has no features.")
        for room in data["config"]["labs"]:
            print(room["name"] + " Lab: Capacity of " + str(room["capacity"]))
            if len(room["features"]) != 0:
                features = ''
                for feature in room["features"]:
                    features += feature + ", "
                print("Features include " + features[:-2])
            else:
                print("Lab has no features.")
        for course in data["config"]["courses"]:
            print(course["course_id"] + ":")
            print(str(course["credits"]) + " credits, capacity of " + str(course["capacity"]))
            rooms = '' 
            labs = ''
            for room in course["room"]:
                rooms += room + ", "
            for lab in course["lab"]:
                labs += lab + ", "
            labs = "acceptable labs are " + labs
            print("Teachable in " + rooms[:-2] + ", " + ("no lab" if course["lab"] == [] else labs[:-2]))
            conflicts = ''
            for conflict in course["conflicts"]:
                conflicts += conflict + ", "
            print("Conflicts with " + conflicts[:-2] if course["conflicts"] != [] else "no other classes")
            if course["faculty"] != None:
                faculty_list = ''
                for faculty in course["faculty"]:
                    faculty_list += faculty + ", "
                print("Teachable by " + faculty_list[:-2])
            else:
                print("No assigned faculty.")
        for faculty in data["config"]["faculty"]:
            print(faculty["name"] + ":")
            print(str(faculty["minimum_credits"]) + " min credits, " + str(faculty["maximum_credits"]) + " max credits, " + str(faculty["unique_course_limit"]) + " max unique courses, " + "no max days" if faculty["maximum_days"] == None else (str(faculty["maximum_days"]) + " max days"))
            if len(faculty["mandatory_days"]) != 0:
                days = ''
                for day in faculty["mandatory_days"]:
                    days += day + ", "
                print("Mandatory days are " + days[:-2])
            else:
                print("No mandatory days")
        print(data["time_slot_config"]["times"])
        print("Max time gap of " + str(data["time_slot_config"]["max_time_gap"]) + ", min time overlap of " + str(data["time_slot_config"]["min_time_overlap"]))


    def do_room(self, arg):
        room_commands.room_handler(self, arg)

    def do_course(self, arg):
        course_commands.course_handler(self, arg)

    def do_lab(self, arg):
        lab_commands.lab_handler(self, arg)

    def do_faculty(self, arg):
        faculty_commands.faculty_handler(self, arg)
    
    def do_times(self,arg):
        times_commands.times_handler(self,arg)
        
    def do_classes(self,arg):
        times_commands.classes_handler(self,arg)
        
    def do_optimizer(self,arg):
        optimizer_commands.optimizer_handler(self,arg)
        
    def do_limit(self, arg):
        limit_commands.limit_handler(self,arg)
        
    def do_help(self, arg):
        help.help_handler(self,arg)
        

    def do_exit(self, arg):
        return True

if __name__ == "__main__":
    SchedulerShell().cmdloop()