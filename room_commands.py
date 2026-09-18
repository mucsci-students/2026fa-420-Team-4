def room_add(shell, arg):
    #Unique, nonblank room name used by references and schedule output
    #str
    #Required
    name = input("Enter room name: ")

    #Maximum number of students the room can accommodate
    #int
    #Required
    capacity = input("Enter room capacity: ")

    #Facility and equipment feature tags supplied by this room
    #set[str].
    #Optional
    features = input("Enter room features: ")

    #Optional weekday room availability windows; null means unrestricted availability
    #dict[Day, list[TimeRange]] | None
    #Optional
    """
    times.*[*] start format: "^([0-1][0-9]|2[0-3]):[0-5][0-9]$"
    Start time of the time range
    Python type: TimeString.

    times.*[*] end format: "^([0-1][0-9]|2[0-3]):[0-5][0-9]$"
    End time of the time range
    Python type: TimeString.
    """
    times = input("Enter room times: ")

def room_list(shell):
    pass
def room_remove(shell,arg):
    pass
def room_update(shell,arg):
    pass

        
def room_handler(shell, arg):
    parts = arg.split()
    if len(parts) == 0:
        print("No command provided. Usage: add | list | remove | update")
        return
    if len(parts) == 0:
        print("Usage course ___ <filename>.json")
        
    command = parts[0]
    filename =parts[1]
    
    if command == "add":
        room_add(shell,filename)
    elif command == "list":
        room_list(shell,filename)
    elif command == "remove":
        room_remove(shell, filename)
    elif command == "update":
        room_update(shell, filename)
    else:
        print("Invalid command. Usage: add | list | remove | update")