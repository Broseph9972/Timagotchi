
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

def get_period_names(day_label):
    periods = {}
    print(f"\nEnter {day_label} period names (or press Enter to skip):")
    for i in range(1, 7):
        name = input(f"{day_label} period {i} name: ").strip()
        if name:
            periods[i] = name
    return periods

def main():
    print("School Schedule Configuration\n")

    use_24h = input("Use 24-hour time format? (y/n): ").lower() == 'y'
    school_start = get_time_input("School start time", use_24h)
    school_end = get_time_input("School end time", use_24h)

    has_advisory = input("\nDoes your school have advisory periods? (y/n): ").lower() == 'y'
    advisory_config = "true" if has_advisory else "false"
    from datetime import datetime, timedelta

    # Get passing time first
    passing_time = input("\nPassing time between periods (minutes): ")
    period_length = input("Regular period length (minutes): ")

    if has_advisory:
        advisory_start = get_time_input("Advisory start time", use_24h)
        advisory_end = get_time_input("Advisory end time", use_24h)
        advisory_start_time = datetime.strptime(advisory_start, "%H:%M")
        advisory_end_time = datetime.strptime(advisory_end, "%H:%M")
        advisory_length = str(int((advisory_end_time - advisory_start_time).seconds / 60))
        advisory_days = input("Advisory days (e.g., m,t,w): ").lower()
    else:
        advisory_start = school_start
        advisory_end = school_start
        advisory_length = "0"
        advisory_days = ""

    lunch_start = get_time_input("\nLunch start time", use_24h)
    lunch_end = get_time_input("Lunch end time", use_24h)
    lunch_start_time = datetime.strptime(lunch_start, "%H:%M")
    lunch_end_time = datetime.strptime(lunch_end, "%H:%M")
    lunch_length = str(int((lunch_end_time - lunch_start_time).seconds / 60))

    num_periods = int(input("\nHow many periods are there (not including lunch and advisory)? "))
    print("\nCalculating period start times...")
    periods = {}
    
    # Calculate time difference between start and end of school day
    school_start_time = datetime.strptime(school_start, "%H:%M")
    school_end_time = datetime.strptime(school_end, "%H:%M")
    
    # Start from after advisory if it exists
    current_time = advisory_end_time if has_advisory else school_start_time
    
    # Calculate period start times
    for i in range(1, num_periods + 1):
        if current_time >= lunch_start_time and current_time <= lunch_end_time:
            current_time = lunch_end_time
        periods[i] = current_time.strftime("%H:%M")
        current_time += timedelta(minutes=int(period_length) + int(passing_time))
    
    # Calculate period start times
    current_time = school_start_time
    if has_advisory:
        current_time = advisory_end_time
        
    for i in range(1, num_periods + 1):
        if current_time >= lunch_start_time and current_time <= lunch_end_time:
            current_time = lunch_end_time
        periods[i] = current_time.strftime("%H:%M")
        current_time += timedelta(minutes=int(period_length) + int(passing_time))

    has_ab = input("\nDoes your school use A/B day scheduling? (y/n): ").lower() == 'y'
    a_day_periods = get_period_names("A day") if has_ab else {}
    b_day_periods = get_period_names("B day") if has_ab else {}

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
        f'advisory = "{advisory_config}"',
        f'advisorylength = "{advisory_length}"',
        f'advisorydays = "{advisory_days}"',
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
        f'abday = "{str(has_ab).lower()}"'
    ]

    config_content = "\n".join(config_lines)

    with open('config.py', 'w') as f:
        f.write(config_content)

    print("\nConfiguration has been saved to config.py!")

if __name__ == "__main__":
    main()
