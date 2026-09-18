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
    features = input("Enter lab features: ")

    #Optional weekday lab availability windows; null means unrestricted availability
    #dict[Day, list[TimeRange]] | None
    #Optional
    times = input("Enter lab times: ")

def lab_list(shell):
    pass
def lab_remove(shell,arg):
    pass
def lab_update(shell,arg):
    pass

def lab_handler(shell, arg):
    parts = arg.split()
    if len(parts) == 0:
        print("No command provided. Usage: add | list | remove | update")
        return
    if len(parts) == 0:
        print("Usage course ___ <filename>.json")
        
    command = parts[0]
    filename =parts[1]
    
    if command == "add":
        lab_add(shell,filename)
    elif command == "list":
        lab_list(shell,filename)
    elif command == "remove":
        lab_remove(shell, filename)
    elif command == "update":
        lab_update(shell, filename)
    else:
        print("Invalid command. Usage: add | list | remove | update")