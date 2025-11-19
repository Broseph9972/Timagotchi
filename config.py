# School Schedule Configuration

# Time format: "HH:MM" (24-hour format)
SCHOOL_START = "09:05"  # Regular school start time
SCHOOL_END = "15:55"    # Regular school end time
USE_24_HOUR = False  # Set to False for 12-hour format (e.g. "3:45 PM")

# Advisory period
ADVISORY_START = "09:20"
advisory = "true"
advisorylength = "36"
advisorydays = "m,t"
freetimedaus = "w,th,f"

# Period start times
PERIODS = {
    1: "09:56", 2: "10:51", 3: "11:46", 4: "12:41", 5: "13:36", 6: "14:31"
}

# Lunch information
LUNCH_START = "13:40"
LUNCH_END = "14:05"

# Period names
A_DAY_PERIODS = {1: 'Spanish', 2: 'ELA', 3: 'Math', 4: 'Gym', 5: 'Science', 6: 'SS'}

B_DAY_PERIODS = {}

# Period lengths (in minutes)
PERIOD_LENGTH = 51
PASSING_TIME = 4

# Additional settings
lunchlength = "25"
abday = "true"