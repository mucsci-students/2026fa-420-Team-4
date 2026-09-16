"""
Validation rules
minimum_credits ≤ maximum_credits.

mandatory_days must be a subset of days that appear in times.

maximum_days ≥ number of mandatory_days.

Preference keys must reference existing courses / rooms / labs.

Faculty name values must be unique.

Faculty names cannot be blank or contain leading or trailing whitespace.

Availability ranges require end later than start; ranges are not merged or inferred.

Time format
24-hour HH:MM-HH:MM.

Multiple ranges per day are allowed, e.g. ["09:00-12:00", "14:00-17:00"].

Preference scale
0 — no objective contribution. An omitted key also contributes zero.
1-3 — low, 4-6 — medium, 7-8 — high, 9-10 — very high.
Preferences interact with optimizer flags (see Optimizer flags).

For a course with faculty: null, the presence of the course id as a course_preferences key makes this faculty eligible even when its score is 0. Explicit course faculty lists are never expanded from preferences.
"""

def faculty_add(shell,arg):
    #Faculty member"s name
    #Faculty
    #Required
    name = input("Enter faculty name: ")

    #Maximum credit hours they can teach
    #int
    #Required
    maximum_credits = input("Enter maximum credits: ")

    #Minimum credit hours they must teach
    #int
    #Required
    minimum_credits = input("Enter minimum credits: ")

    #Maximum number of different courses they can teach
    #int
    #Required
    unique_course_limit = input("Enter unique course limit: ")

    #Maximum number of days they are willing to teach (0-5, optional)
    #int
    #Required
    maximum_days = input("Enter maximum days: ")

    #Set of days the faculty must teach on
    #set[Day]
    #Allowed values: {MON, TUE, WED, THU, FRI}
    #Optional
    mandatory_days = input("Enter mandatory days: ")

    #Availability ranges keyed by weekday; omitted days and empty lists mean unavailable
    #dict[Day, list[TimeRange]]
    #Required
    times = input("Enter times: ")

    #Dictionary mapping course IDs to preference scores
    #dict[Course, Preference]
    #Optional
    course_preferences = input("Enter course preferences: ")

    #Dictionary mapping room IDs to preference scores
    #dict[Room, Preference]
    #Optional
    room_preferences = input("Enter room preferences: ")

    #Dictionary mapping lab IDs to preference scores
    #dict[Lab, Preference]
    #Optional
    lab_preferences = input("Enter lab preferences: ")
