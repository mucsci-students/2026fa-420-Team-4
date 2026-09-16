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