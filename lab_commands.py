SUCCESS = 0
ERROR_UNDEFINED = -1

import ast

from scheduler.config import LabConfig


def lab_add(shell,arg):
    #Unique, nonblank lab name used by references and schedule output
    #str
    #Required
    name = input("Enter lab name: ")

    #Maximum number of students the lab can accommodate
    #int
    #Required
    capacity = int ( input ( "Enter lab capacity: " ) )

    #Facility and equipment feature tags supplied by this lab
    #set[str]
    #Optional
    features = set()
    while True:
        feature = input("Enter optional lab feature (press Enter when finished): ")
        if feature == "":
            break
        features.add(feature)

    #Optional weekday lab availability windows; null means unrestricted availability
    #dict[Day, list[TimeRange]] | None
    #Optional
    times_text = input("Enter optional lab times as a dictionary (press Enter for unrestricted): ")
    times: dict | None = None
    if times_text.strip():
        parsed_times = ast.literal_eval(times_text)
        if not isinstance(parsed_times, dict):
            raise ValueError("Lab times must be a dictionary.")
        times = parsed_times
    return LabConfig(name=name, capacity=capacity, features=features, times=times)

def lab_remove(shell,arg):
    return "LABDNE"
def lab_modify(shell,arg):
    return ERROR_UNDEFINED

def lab_handler(shell, arg):
    print("\n\t\tLab Configuation\n\tCommands: add | modify | remove | exit")
    command = input("Enter command: ")
    commandValid = ["add", "modify", "remove","exit"]
    while command not in commandValid:
        print("\nInvalid command. Usage: add | modify | remove | exit")
        command = input("Enter command: ")
    if command == "add":
        return lab_add(shell, arg)
    elif command == "modify":
        return lab_modify(shell, arg)
    elif command == "remove":
        return lab_remove(shell,arg)
    elif command == "exit":
        return SUCCESS
    else:
        return ERROR_UNDEFINED