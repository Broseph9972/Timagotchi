import json

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

def get_period_names(day_label, num_periods=6, previous_periods=None):
    """
    Get period names for a day preset.
    
    Args:
        day_label: Label for the day (e.g., "A day", "B day", "C day")
        num_periods: Number of periods
        previous_periods: Dict of period names from previous day to optionally copy from
    """
    periods = {}
    print(f"\nEnter {day_label} period names:")
    print("(Press Enter to skip, or 'c' to copy from previous day preset)" if previous_periods else "(Press Enter to skip):")
    
    for i in range(1, num_periods + 1):
        prompt = f"{day_label} period {i} name"
        if previous_periods and i in previous_periods:
            prompt += f" (previous: '{previous_periods[i]}')"
        prompt += ": "
        
        name = input(prompt).strip()
        
        if name.lower() == 'c' and previous_periods and i in previous_periods:
            # Copy from previous day
            periods[i] = previous_periods[i]
            print(f"  → Copied: {periods[i]}")
        elif name:
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

    # Advisory/Homeroom configuration
    has_advisory = input("\nDoes your school have advisory/homeroom? (y/n): ").lower() == 'y'
    if has_advisory:
        advisory_start = get_time_input("Advisory/homeroom start time", use_24h)
        advisory_length = input("Advisory/homeroom length (minutes): ")
        print("\nWhich days have advisory/homeroom?")
        print("Enter days as comma-separated abbreviations: m,t,w,th,f")
        print("Or enter 'all' for every weekday")
        advisory_days = input("Advisory days (e.g., m,t or all): ").strip().lower()
        if advisory_days == 'all':
            advisory_days = 'm,t,w,th,f'
    else:
        advisory_start = school_start
        advisory_length = "0"
        advisory_days = ""

    # Get number of regular class periods
    num_periods = int(input("\nHow many regular class periods are there (not including lunch/advisory)? "))
    
    # Lunch configuration
    has_lunch = input("\nDoes your schedule include lunch? (y/n): ").lower() == 'y'
    if has_lunch:
        lunch_start = get_time_input("Lunch start time", use_24h)
        lunch_end = get_time_input("Lunch end time", use_24h)
        lunch_start_time = datetime.strptime(lunch_start, "%H:%M")
        lunch_end_time = datetime.strptime(lunch_end, "%H:%M")
        lunch_length = str(int((lunch_end_time - lunch_start_time).seconds / 60))
        lunch_after_period = int(input("Which period does lunch come after? "))
    else:
        lunch_start = school_start
        lunch_end = school_start
        lunch_start_time = datetime.strptime(lunch_start, "%H:%M")
        lunch_end_time = datetime.strptime(lunch_end, "%H:%M")
        lunch_length = "0"
        lunch_after_period = 0

    print("\nCalculating period start times...")
    periods = {}

    # Calculate time difference between start and end of school day
    school_start_time = datetime.strptime(school_start, "%H:%M")
    school_end_time = datetime.strptime(school_end, "%H:%M")

    # Build complete schedule with advisory (if present) as first "period"
    # Then regular periods 1-N with lunch inserted at correct position
    current_time = school_start_time
    period_len = int(period_length)
    pass_min = int(passing_time)

    # Add advisory as special period "advisory" if enabled
    if has_advisory:
        periods['advisory'] = advisory_start
        # After advisory, add passing time before period 1
        advisory_end = datetime.strptime(advisory_start, "%H:%M") + timedelta(minutes=int(advisory_length))
        current_time = advisory_end + timedelta(minutes=pass_min)
    
    # Add regular numbered periods
    for i in range(1, num_periods + 1):
        periods[i] = current_time.strftime("%H:%M")

        # Class ends after period length
        class_end = current_time + timedelta(minutes=period_len)

        # Next period normally starts after class end + passing time
        next_start = class_end + timedelta(minutes=pass_min)

        # If this is the period after which lunch should occur, insert lunch
        if has_lunch and i == lunch_after_period:
            # Add lunch as special period "lunch"
            periods['lunch'] = lunch_end_time.strftime("%H:%M")  # Store end of lunch as "start" for next class calc
            # Next class starts after lunch + passing time
            next_start = lunch_end_time + timedelta(minutes=pass_min)

        current_time = next_start

    has_ab = input("\nDoes your school use rotating day presets? (y/n): ").lower() == 'y'
    day_presets = {}
    ab_day_mode = "auto"
    manual_ab_day = "a"
    
    if has_ab:
        # Ask how many day presets
        print("\n" + "="*50)
        print("Day Preset Configuration")
        print("="*50)
        print("Examples: 2 presets (A/B days), 3 presets (A/B/C days), etc.")
        
        num_presets_str = input("How many day presets? (default: 2): ").strip()
        try:
            num_presets = int(num_presets_str)
            if num_presets < 1:
                num_presets = 2
        except ValueError:
            num_presets = 2
        
        # Generate preset names/labels
        preset_labels = []
        if num_presets == 2:
            preset_labels = ["A day", "B day"]
        elif num_presets == 3:
            preset_labels = ["A day", "B day", "C day"]
        else:
            for i in range(num_presets):
                preset_labels.append(chr(65 + i) + " day")  # A day, B day, C day, etc.
        
        # Get period names for each preset
        previous_periods = None
        for idx, label in enumerate(preset_labels):
            day_presets[idx] = get_period_names(label, num_periods, previous_periods)
            previous_periods = day_presets[idx]
        
        # Day Preset Mode Configuration
        print("\n" + "="*50)
        print("Day Preset Mode Configuration")
        print("="*50)
        print("Choose rotation mode:")
        print("1. Auto (rotates based on calendar)")
        print("2. Manual (you set current preset)")
        mode_choice = input("Select mode (1 or 2, default: 1): ").strip()
        ab_day_mode = "auto" if mode_choice != "2" else "manual"
        
        if ab_day_mode == "manual":
            print(f"\nAvailable presets: {', '.join(preset_labels)}")
            manual_ab_day = input(f"Set current preset (1-{num_presets}, default: 1): ").strip()
            try:
                preset_idx = int(manual_ab_day) - 1
                if preset_idx < 0 or preset_idx >= num_presets:
                    manual_ab_day = "0"
                else:
                    manual_ab_day = str(preset_idx)
            except ValueError:
                manual_ab_day = "0"
        else:
            manual_ab_day = "0"  # First preset by default

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
        "# Advisory/Homeroom configuration",
        f'ADVISORY_START = "{advisory_start}"',
        f'advisory = "{str(has_advisory).lower()}"',
        f'advisorylength = "{advisory_length}"',
        f'advisorydays = "{advisory_days}"',
        "",
        "# Lunch configuration",
        f'has_lunch = "{str(has_lunch).lower()}"',
        f'LUNCH_START = "{lunch_start}"',
        f'LUNCH_END = "{lunch_end}"',
        f'lunchlength = "{lunch_length}"',
        "",
        "# Period start times",
        "# Special periods: 'advisory' (homeroom), 'lunch'",
        "# Regular periods: 1, 2, 3, etc.",
        "PERIODS = {",
    ]
    
    # Add periods with proper formatting
    period_items = []
    for k, v in sorted(periods.items(), key=lambda x: (isinstance(x[0], str), x[0])):
        if isinstance(k, str):
            period_items.append(f'    "{k}": "{v}"')
        else:
            period_items.append(f'    {k}: "{v}"')
    
    config_lines.append(",\n".join(period_items))
    config_lines.extend([
        "}",
        "",
        "# Period names - Day presets",
        "# DAY_PRESETS is a dictionary where each key is the preset name and value is the periods dict",
        "# Only regular periods (1, 2, 3, etc.) need names - advisory/lunch are auto-labeled",
        "DAY_PRESETS = {",
    ])
    
    # Add each day preset
    if has_ab:
        for idx, label in enumerate(preset_labels):
            preset_key = chr(65 + idx)  # A, B, C, etc.
            config_lines.append(f'    "{preset_key}": {day_presets[idx]},')
    
    config_lines.extend([
        "}",
        "",
        "# Legacy support (for backward compatibility)",
        "# A_DAY_PERIODS and B_DAY_PERIODS are deprecated; use DAY_PRESETS instead",
    ])
    
    # Add legacy A_DAY_PERIODS and B_DAY_PERIODS if they exist
    if has_ab and len(day_presets) >= 1:
        config_lines.append(f"A_DAY_PERIODS = {day_presets[0]}")
    else:
        config_lines.append("A_DAY_PERIODS = {}")
    
    if has_ab and len(day_presets) >= 2:
        config_lines.append(f"B_DAY_PERIODS = {day_presets[1]}")
    else:
        config_lines.append("B_DAY_PERIODS = {}")
    
    config_lines.extend([
        "",
        "# Period lengths (in minutes)",
        f"PERIOD_LENGTH = {period_length}",
        f"PASSING_TIME = {passing_time}",
        "",
        "# Additional settings",
        f'abday = "{str(has_ab).lower()}"',
        f'NUM_DAY_PRESETS = {num_presets if has_ab else 1}  # Number of rotating day presets',
        "# Manual day preset selection (\"auto\" for rotation, or 0-based index like \"0\", \"1\", \"2\")",
        f'AB_DAY_MODE = "{ab_day_mode}"  # "auto" or "manual"',
        f'MANUAL_AB_DAY = "{manual_ab_day}"   # Current preset when in manual mode (0-based index)',
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
        "",
        "# Canvas LMS Integration (Optional)",
        "# Leave base_url and api_token empty if not using Canvas",
        'CANVAS_ENABLED = False',
        'CANVAS_BASE_URL = ""  # e.g., https://yourschool.instructure.com',
        'CANVAS_API_TOKEN = ""  # Get from Account > Settings > New Access Token',
    ])

    config_content = "\n".join(config_lines)

    with open('config.py', 'w') as f:
        f.write(config_content)

    print("\nConfiguration has been saved to config.py!")
    
    # Ask for Canvas configuration
    print("\n" + "="*50)
    print("Canvas LMS Integration (Optional)")
    print("="*50)
    use_canvas = input("\nDo you use Canvas LMS? (y/n): ").lower() == 'y'
    
    if use_canvas:
        canvas_url = input("Canvas base URL (e.g., https://yourschool.instructure.com): ").strip()
        canvas_token = input("Canvas API token (from Account > Settings > New Access Token): ").strip()
        
        if canvas_url and canvas_token:
            canvas_config = {
                "base_url": canvas_url,
                "api_token": canvas_token
            }
            
            try:
                with open('canvas_config.json', 'w') as f:
                    json.dump(canvas_config, f, indent=2)
                print("Canvas configuration saved to canvas_config.json")
            except Exception as e:
                print(f"Error saving Canvas config: {e}")
        else:
            print("Canvas configuration skipped.")
    else:
        print("Canvas configuration skipped.")

if __name__ == "__main__":
    main()
