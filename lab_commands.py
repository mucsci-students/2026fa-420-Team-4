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
    selected_lab = input("Enter the name of the lab to remove: ")
    # ``arg`` is the configuration file passed to this command.
    if not isinstance(arg, dict):
        return "LABDNE"

    labs = arg.get("labs")
    if not isinstance(labs, list):
        return "LABDNE"

    for index, lab in enumerate(labs):
        if isinstance(lab, dict):
            lab_name = lab.get("name")
        elif isinstance(lab, (tuple, list)) and lab:
            lab_name = lab[0]
        else:
            lab_name = None

        if lab_name == selected_lab:
            del labs[index]
            return arg

    return "LABDNE"
def lab_modify(shell,arg):
    try:
        # Support both current and legacy configuration attribute names.
        config = getattr(shell, "config", None)
        if config is None:
            config = getattr(shell, "config_file", None)

        # Read the configured labs, or use an empty list when unavailable.
        labs = config.get("labs", []) if isinstance(config, dict) else []

        def lab_identity(lab):
            if isinstance(lab, dict):
                return lab.get("name"), lab.get("capacity")
            if isinstance(lab, (tuple, list)) and len(lab) >= 2:
                return lab[0], lab[1]
            return None

        target = lab_identity(arg)

        for lab in labs:
            if target is not None and lab_identity(lab) == target:
                return lab
    except (AttributeError, TypeError, KeyError):
        pass

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