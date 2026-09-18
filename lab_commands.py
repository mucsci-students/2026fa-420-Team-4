SUCCESS = 0
ERROR_UNDEFINED = -1

from scheduler.config import LabConfig


def lab_add(shell,arg):
    #Unique, nonblank lab name used by references and schedule output
    #str
    #Required
    name = input("Enter lab name: ")

    #Maximum number of students the lab can accommodate
    #int
    #Required
    capacity = input("Enter lab capacity: ")

    #Facility and equipment feature tags supplied by this lab
    #set[str]
    #Optional
    features = input("Enter optional lab features: ")

    #Optional weekday lab availability windows; null means unrestricted availability
    #dict[Day, list[TimeRange]] | None
    #Optional
    times = input("Enter optional lab times: ")
    if features == "":
        features = None
    if times == "":
        times = None
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