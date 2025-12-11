
def get_time_input(prompt, use_24h=False):
    while True:
        try:
            time_str = input(prompt + (" (HH:MM): " if use_24h else " (HH:MM): "))
            if not use_24h and ":" in time_str:
                from datetime import datetime
                # Strip any AM/PM if provided
                time_str = time_str.replace("am", "").replace("pm", "").replace("AM", "").replace("PM", "").strip()
                hour, minute = map(int, time_str.split(":"))
                
                # Auto-assign AM/PM based on time ranges
                if 7 <= hour <= 11:
                    time_str += " AM"
                elif 1 <= hour <= 5:
                    time_str += " PM"
                elif hour == 12:
                    time_str += " PM"
                elif hour == 6:
                    # Ask for AM/PM for 6:XX times
                    ampm = input("Is this AM or PM? ").upper().strip()
                    time_str += f" {ampm}"
                
                time = datetime.strptime(time_str, "%I:%M %p")
                return time.strftime("%H:%M")
            return time_str
        except ValueError:
            print("Invalid time format. Please try again.")

def get_period_names(day_label, num_periods=6):
    periods = {}
    print(f"\nEnter {day_label} period names (or press Enter to skip):")
    for i in range(1, num_periods + 1):
        name = input(f"{day_label} period {i} name: ").strip()
        if name:
            periods[i] = name
    return periods

def main():
    print("School Schedule Configuration\n")

    use_24h = input("Use 24-hour time format? (y/n): ").lower() == 'y'
    school_start = get_time_input("School start time", use_24h)
    school_end = get_time_input("School end time", use_24h)

    from datetime import datetime, timedelta

    # Get passing time and period length
    passing_time = input("\nPassing time between periods (minutes): ")
    period_length = input("Regular period length (minutes): ")

    # Advisory period configuration
    has_advisory = input("\nDoes your school have advisory? (y/n): ").lower() == 'y'
    if has_advisory:
        advisory_start = get_time_input("Advisory start time", use_24h)
        advisory_length = input("Advisory length (minutes): ")
        print("\nWhich days have advisory?")
        print("Enter days as comma-separated abbreviations: m,t,w,th,f")
        advisory_days = input("Advisory days (e.g., m,t): ").strip().lower()
    else:
        advisory_start = school_start
        advisory_length = "0"
        advisory_days = ""

    lunch_start = get_time_input("\nLunch start time", use_24h)
    lunch_end = get_time_input("Lunch end time", use_24h)
    lunch_start_time = datetime.strptime(lunch_start, "%H:%M")
    lunch_end_time = datetime.strptime(lunch_end, "%H:%M")
    lunch_length = str(int((lunch_end_time - lunch_start_time).seconds / 60))

    num_periods = int(input("\nHow many periods are there (not including lunch and advisory)? "))
    lunch_after_period = int(input("Which period does lunch come after? "))
    print("\nCalculating period start times...")
    periods = {}

    # Calculate time difference between start and end of school day
    school_start_time = datetime.strptime(school_start, "%H:%M")
    school_end_time = datetime.strptime(school_end, "%H:%M")

    # Simulate timeline from school start and assign period start times.
    # Lunch comes after the specified period.
    current_time = school_start_time
    period_len = int(period_length)
    pass_min = int(passing_time)

    for i in range(1, num_periods + 1):
        periods[i] = current_time.strftime("%H:%M")

        # Class ends after period length
        class_end = current_time + timedelta(minutes=period_len)

        # Next period normally starts after class end + passing time
        next_start = class_end + timedelta(minutes=pass_min)

        # If this is the period after which lunch should occur, insert lunch
        if i == lunch_after_period:
            # Insert lunch instead of next period
            next_start = lunch_end_time

        current_time = next_start

    has_ab = input("\nDoes your school use A/B day scheduling? (y/n): ").lower() == 'y'
    a_day_periods = {}
    b_day_periods = {}
    ab_day_mode = "auto"
    manual_ab_day = "a"
    
    if has_ab:
        a_day_periods = get_period_names("A day", num_periods)
        b_day_periods = get_period_names("B day", num_periods)
        
        # A/B Day Mode Configuration
        print("\n" + "="*50)
        print("A/B Day Mode Configuration")
        print("="*50)
        print("Choose A/B day mode:")
        print("1. Auto (rotates based on calendar)")
        print("2. Manual (you set current day as A or B)")
        ab_mode_choice = input("Select mode (1 or 2, default: 1): ").strip()
        ab_day_mode = "auto" if ab_mode_choice != "2" else "manual"
        if ab_day_mode == "manual":
            manual_ab_day = input("Set current day as (a or b, default: a): ").strip().lower()
            if manual_ab_day not in ["a", "b"]:
                manual_ab_day = "a"

    # WiFi Network Configuration
    print("\n" + "="*50)
    print("WiFi Network Configuration")
    print("="*50)
    num_networks = int(input("How many WiFi networks do you want to connect to? "))
    wifi_networks = []
    
    for i in range(num_networks):
        print(f"\nNetwork {i+1}:")
        ssid = input(f"  Network name (SSID): ").strip()
        password = input(f"  Password (leave empty for open network): ").strip()
        wifi_networks.append((ssid, password))
    
    wifi_networks_str = "[\n"
    for ssid, password in wifi_networks:
        wifi_networks_str += f'    ("{ssid}", "{password}"),\n'
    wifi_networks_str += "]"

    # Ask about time sync settings
    print("\n=== Time Sync Settings ===")
    print("How should the system handle time synchronization?")
    print("  1) Disabled (manual only, no automatic sync)")
    print("  2) On Boot (sync once when system starts)")
    print("  3) Periodic (sync every N hours)")
    
    sync_choice = input("\nSelect time sync mode (1-3, default 1): ").strip()
    
    # Get timezone setting
    print("\nEnter your timezone (e.g., America/New_York, America/Chicago, America/Los_Angeles)")
    print("See full list at: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones")
    timezone = input("Timezone (default: America/New_York): ").strip()
    if not timezone:
        timezone = "America/New_York"
    
    if sync_choice == "2":
        time_sync_mode = "on_boot"
        time_sync_interval = 6  # Not used but set to default
    elif sync_choice == "3":
        time_sync_mode = "periodic"
        sync_hours = input("How many hours between syncs? (default 6): ").strip()
        try:
            time_sync_interval = int(sync_hours)
        except ValueError:
            time_sync_interval = 6
    else:
        time_sync_mode = "disabled"
        time_sync_interval = 6  # Not used but set to default
    
    # Build the configuration content using regular string formatting
    config_lines = [
        "# School Schedule Configuration\n",
        "# Time format: \"HH:MM\" (24-hour format)",
        f'SCHOOL_START = "{school_start}"  # Regular school start time',
        f'SCHOOL_END = "{school_end}"    # Regular school end time',
        f"USE_24_HOUR = {str(use_24h)}  # Set to False for 12-hour format (e.g. \"3:45 PM\")",
        "",
        "# Advisory period",
        f'ADVISORY_START = "{advisory_start}"',
        f'advisory = "{str(has_advisory).lower()}"',
        f'advisorylength = "{advisory_length}"',
        f'advisorydays = "{advisory_days}"',
        '# Free time days (no advisory)',
        'freetimedaus = "w,th,f"',
        "",
        "# Period start times",
        "PERIODS = {",
        "    " + ", ".join(f'{k}: "{v}"' for k, v in periods.items()),
        "}",
        "",
        "# Lunch information",
        f'LUNCH_START = "{lunch_start}"',
        f'LUNCH_END = "{lunch_end}"',
        "",
        "# Period names",
        f"A_DAY_PERIODS = {a_day_periods}",
        "",
        f"B_DAY_PERIODS = {b_day_periods}",
        "",
        "# Period lengths (in minutes)",
        f"PERIOD_LENGTH = {period_length}",
        f"PASSING_TIME = {passing_time}",
        "",
        "# Additional settings",
        f'lunchlength = "{lunch_length}"',
        f'abday = "{str(has_ab).lower()}"',
        "# Manual A/B day selection (can be \"auto\", \"a\", or \"b\")",
        "# Set to \"a\" or \"b\" to manually select, or \"auto\" for automatic rotation",
        f'AB_DAY_MODE = "{ab_day_mode}"  # "auto" or "manual"',
        f'MANUAL_AB_DAY = "{manual_ab_day}"   # Current day when in manual mode ("a" or "b")',
        "",
        "# WiFi Networks",
        "# List of (SSID, PASSWORD) tuples. Use empty string \"\" for open networks",
        f"WIFI_NETWORKS = {wifi_networks_str}",
        "",
        "# Time Synchronization Settings",
        "# TIME_SYNC_MODE options:",
        "#   - \"disabled\": Manual sync only (hold Key3 for 2 seconds in Set Time)",
        "#   - \"on_boot\": Sync once when system starts",
        "#   - \"periodic\": Sync every TIME_SYNC_INTERVAL hours",
        f'TIME_SYNC_MODE = "{time_sync_mode}"',
        f"TIME_SYNC_INTERVAL = {time_sync_interval}  # Hours between periodic syncs (if using periodic mode)",
        f'TIMEZONE = "{timezone}"  # System timezone (e.g., America/New_York)',
        "",
        "# Progress Bar Settings",
        "# Display mode: \"time_in_class\", \"time_in_day\", or \"lunch_day\"",
        'PROGRESS_BAR_MODE = "time_in_class"  # What the progress bar shows',
    ]

    config_content = "\n".join(config_lines)

    with open('config.py', 'w') as f:
        f.write(config_content)

    print("\nConfiguration has been saved to config.py!")

if __name__ == "__main__":
    main()
