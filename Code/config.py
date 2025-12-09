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

B_DAY_PERIODS = {1: 'Spanish', 2: 'ELA', 3: 'Math', 4: 'Health', 5: 'Science', 6: 'SS'}

# Period lengths (in minutes)
PERIOD_LENGTH = 51
PASSING_TIME = 4

# Additional settings
lunchlength = "25"
abday = "true"
# Manual A/B day selection (can be "auto", "a", or "b")
# Set to "a" or "b" to manually select, or "auto" for automatic rotation
AB_DAY_MODE = "auto"  # "auto", "a", or "b"
MANUAL_AB_DAY = "a"   # Current day when in manual mode ("a" or "b")

# WiFi Networks
# List of (SSID, PASSWORD) tuples. Use empty string "" for open networks
WIFI_NETWORKS = [
    # ("Network Name", "Password"),
    # ("Open Network", ""),
]

# Time Sync Settings
# Automatic time sync control: "disabled", "on_boot", or "periodic"
TIME_SYNC_MODE = "disabled"  # "disabled" = manual only, "on_boot" = sync on startup, "periodic" = sync every N hours
TIME_SYNC_INTERVAL = 6  # Hours between periodic syncs (only used if TIME_SYNC_MODE = "periodic")

# Progress Bar Settings
# Display mode: "time_in_class", "time_in_day", or "lunch_day"
PROGRESS_BAR_MODE = "time_in_class"  # What the progress bar shows