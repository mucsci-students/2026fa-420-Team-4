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

def lab_list(shell):
    pass
def lab_remove(shell,arg):
    pass
def lab_update(shell,arg):
    pass

def lab_handler(shell, arg):
    print("\t\tLab Configuation\n\tCommands: add | remove | update")
    command = input("Enter command: ")
    if command == "add":
        lab_add(shell, arg)
    elif command == "modify":
        lab_list(shell)
    elif command == "remove":
        lab_remove(shell,arg)
    else:
        print("Invalid command. Usage: add | list | remove | update")