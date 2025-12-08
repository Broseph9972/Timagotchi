import datetime
import subprocess
import time
from config import (
    PERIODS, SCHOOL_START, SCHOOL_END, LUNCH_START, LUNCH_END,
    PERIOD_LENGTH, PASSING_TIME, A_DAY_PERIODS, B_DAY_PERIODS,
    ADVISORY_START, advisory, advisorydays, advisorylength, freetimedaus, USE_24_HOUR,
    AB_DAY_MODE, MANUAL_AB_DAY, TIME_SYNC_MODE, TIME_SYNC_INTERVAL
)
from input_handler import InputHandler

class Menu:
    def __init__(self, display, input_handler):
        self.display = display
        self.input_handler = input_handler
        self.current_screen = "main"
        self.selected_index = 0
        self.running = True
        
        self.main_menu_items = ["Schedule", "Clock", "Settings", "Set Time"]
        self.settings_menu_items = ["A/B Day", "WiFi", "Back"]
        self.adjust_hour = 0
        self.adjust_minute = 0
        self.ab_day_mode = AB_DAY_MODE  # "auto", "a", or "b"
        self.manual_ab_day = MANUAL_AB_DAY  # "a" or "b" when in manual mode
        self.key3_press_time = None  # Track when Key3 is pressed
        self.last_sync_time = 0  # Track last WiFi sync time for periodic syncing
        self.sync_on_boot = (TIME_SYNC_MODE == "on_boot")  # Flag to sync once at startup
    
    def is_advisory_day(self):
        today = datetime.datetime.now().strftime('%a').lower()
        return advisory.lower() == "true" and today[0] in advisorydays.lower().split(',')
    
    def is_freetime_day(self):
        today = datetime.datetime.now().strftime('%a').lower()
        return today[0] in freetimedaus.lower().split(',')
    
    def get_current_period(self, current_time):
        advisory_start = datetime.datetime.strptime(ADVISORY_START, "%H:%M").time()
        advisory_start = datetime.datetime.combine(datetime.date.today(), advisory_start)
        advisory_end = advisory_start + datetime.timedelta(minutes=int(advisorylength))
        
        if advisory_start <= current_time < advisory_end:
            if self.is_advisory_day():
                time_remaining = advisory_end - current_time
                return "ADVISORY", time_remaining, False
            elif self.is_freetime_day():
                time_remaining = advisory_end - current_time
                return "FREETIME", time_remaining, False
        
        lunch_start = datetime.datetime.strptime(LUNCH_START, "%H:%M").time()
        lunch_start = datetime.datetime.combine(datetime.date.today(), lunch_start)
        lunch_end = datetime.datetime.strptime(LUNCH_END, "%H:%M").time()
        lunch_end = datetime.datetime.combine(datetime.date.today(), lunch_end)
        
        if lunch_start <= current_time < lunch_end:
            time_remaining = lunch_end - current_time
            return "LUNCH", time_remaining, True
        
        for period in range(1, 9):
            if period not in PERIODS:
                continue
            period_start_time = datetime.datetime.strptime(PERIODS[period], "%H:%M").time()
            period_start = datetime.datetime.combine(datetime.date.today(), period_start_time)
            period_end = period_start + datetime.timedelta(minutes=PERIOD_LENGTH)
            
            if period_start <= current_time < period_end:
                time_remaining = period_end - current_time
                hours = time_remaining.seconds // 3600
                minutes = (time_remaining.seconds % 3600) // 60
                formatted_time = datetime.timedelta(hours=hours, minutes=minutes)
                return period, formatted_time, False
                
        return None, None, False
    
    def get_time_until(self, target_time, current_time):
        target = datetime.datetime.strptime(target_time, "%H:%M").time()
        target = datetime.datetime.combine(datetime.date.today(), target)
        if target < current_time:
            return None
        return target - current_time
    
    def format_timedelta(self, td):
        if td is None:
            return "N/A"
        total_seconds = int(td.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        if hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"
    
    def show_schedule_screen(self):
        current_time = datetime.datetime.now()
        period, time_remaining, is_lunch = self.get_current_period(current_time)
        
        school_start = datetime.datetime.strptime(SCHOOL_START, "%H:%M").time()
        school_start = datetime.datetime.combine(datetime.date.today(), school_start)
        school_end = datetime.datetime.strptime(SCHOOL_END, "%H:%M").time()
        school_end = datetime.datetime.combine(datetime.date.today(), school_end)
        
        if USE_24_HOUR:
            current_time_str = current_time.strftime("%H:%M")
        else:
            current_time_str = current_time.strftime("%I:%M %p")
        
        if current_time < school_start:
            time_until_start = self.get_time_until(SCHOOL_START, current_time)
            time_until_str = self.format_timedelta(time_until_start)
            self.display.show_message("School Hasn't Started", f"Starts in {time_until_str}\nSchool @ {SCHOOL_START}", (200, 200, 200))
            return
        elif current_time > school_end:
            self.display.show_message("After School", "School day has ended", (200, 200, 200))
            return
        
        period_name = ""
        if period is not None and isinstance(period, int):
            if period in A_DAY_PERIODS:
                period_name = A_DAY_PERIODS[period]
            else:
                period_name = f"Period {period}"
        
        lunch_time_str = None
        lunch_start_dt = datetime.datetime.strptime(LUNCH_START, "%H:%M").time()
        lunch_start_dt = datetime.datetime.combine(datetime.date.today(), lunch_start_dt)
        if current_time < lunch_start_dt:
            time_until_lunch = self.get_time_until(LUNCH_START, current_time)
            lunch_time_str = self.format_timedelta(time_until_lunch)
        
        end_time_str = None
        if current_time < school_end:
            time_until_end = self.get_time_until(SCHOOL_END, current_time)
            end_time_str = self.format_timedelta(time_until_end)
        
        time_remaining_str = self.format_timedelta(time_remaining) if time_remaining else None
        
        self.display.show_schedule(period, period_name, time_remaining_str, lunch_time_str, end_time_str, current_time_str)
    
    def show_clock_screen(self):
        now = datetime.datetime.now()
        if USE_24_HOUR:
            time_str = now.strftime("%H:%M:%S")
        else:
            time_str = now.strftime("%I:%M:%S %p")
        date_str = now.strftime("%A, %B %d")
        self.display.show_clock(time_str, date_str)
    
    def show_main_menu(self):
        self.display.show_menu(self.main_menu_items, self.selected_index, "Main Menu")
    
    def show_settings_menu(self):
        self.display.show_menu(self.settings_menu_items, self.selected_index, "Settings")
    
    def show_wifi_menu(self):
        self.display.show_message("WiFi", "Connecting to\nconfigured networks...", (100, 200, 255))
    
    def show_ab_day_menu(self):
        if self.ab_day_mode == "auto":
            message = "A/B Day: Auto\n\nUp/Down: Change\nSelect: Confirm"
        else:
            current = self.manual_ab_day.upper()
            message = f"A/B Day: {current}\n\nUp/Down: Toggle\nSelect: Confirm"
        self.display.show_message("A/B Day", message, (200, 150, 255))
    
    def show_set_time_screen(self):
        hour_str = f"{self.adjust_hour:02d}"
        minute_str = f"{self.adjust_minute:02d}"
        message = f"Set Time:\n{hour_str}:{minute_str}\n\nKey1: Hour+\nKey2: Min+\nKey3: Sync"
        self.display.show_message("Set Time", message, (255, 200, 100))
    
    def handle_set_time_input(self, action):
        if action == 'key1':  # Increase hour
            self.key3_press_time = None  # Reset hold timer
            self.adjust_hour = (self.adjust_hour + 1) % 24
            self.show_set_time_screen()
        elif action == 'key2':  # Increase minute
            self.key3_press_time = None  # Reset hold timer
            self.adjust_minute = (self.adjust_minute + 1) % 60
            self.show_set_time_screen()
        elif action == 'key3':
            # Start tracking Key3 press for hold detection
            if self.key3_press_time is None:
                self.key3_press_time = time.time()
        elif action == 'left' or action == 'select':
            # Exit without saving
            self.key3_press_time = None
            self.current_screen = "main"
            self.selected_index = 0
            self.show_main_menu()
    
    def handle_ab_day_input(self, action):
        if action == 'up':
            if self.ab_day_mode == "auto":
                self.ab_day_mode = "manual"
                self.manual_ab_day = "b"
            else:
                self.manual_ab_day = "b" if self.manual_ab_day == "a" else "a"
            self.show_ab_day_menu()
        elif action == 'down':
            if self.ab_day_mode == "auto":
                self.ab_day_mode = "manual"
                self.manual_ab_day = "a"
            else:
                self.manual_ab_day = "b" if self.manual_ab_day == "a" else "a"
            self.show_ab_day_menu()
        elif action == 'select' or action == 'right':
            self.current_screen = "settings"
            self.selected_index = 0
            self.show_settings_menu()
        elif action == 'left' or action == 'key1':
            self.current_screen = "settings"
            self.selected_index = 0
            self.show_settings_menu()
    
    def handle_main_menu_input(self, action):
        if action == 'up':
            self.selected_index = (self.selected_index - 1) % len(self.main_menu_items)
            self.show_main_menu()
        elif action == 'down':
            self.selected_index = (self.selected_index + 1) % len(self.main_menu_items)
            self.show_main_menu()
        elif action == 'select' or action == 'right':
            selected_item = self.main_menu_items[self.selected_index]
            if selected_item == "Schedule":
                self.current_screen = "schedule"
                self.show_schedule_screen()
            elif selected_item == "Clock":
                self.current_screen = "clock"
                self.show_clock_screen()
            elif selected_item == "Settings":
                self.current_screen = "settings"
                self.selected_index = 0
                self.show_settings_menu()
            elif selected_item == "Set Time":
                self.current_screen = "set_time"
                now = datetime.datetime.now()
                self.adjust_hour = now.hour
                self.adjust_minute = now.minute
                self.show_set_time_screen()
    
    def handle_schedule_input(self, action):
        if action == 'left' or action == 'key1':
            self.current_screen = "main"
            self.selected_index = 0
            self.show_main_menu()
    
    def handle_clock_input(self, action):
        if action == 'left' or action == 'key1':
            self.current_screen = "main"
            self.selected_index = 0
            self.show_main_menu()
    
    def handle_settings_input(self, action):
        if action == 'up':
            self.selected_index = (self.selected_index - 1) % len(self.settings_menu_items)
            self.show_settings_menu()
        elif action == 'down':
            self.selected_index = (self.selected_index + 1) % len(self.settings_menu_items)
            self.show_settings_menu()
        elif action == 'select' or action == 'right':
            selected_item = self.settings_menu_items[self.selected_index]
            if selected_item == "Back":
                self.current_screen = "main"
                self.selected_index = 0
                self.show_main_menu()
            elif selected_item == "A/B Day":
                self.current_screen = "ab_day"
                self.show_ab_day_menu()
            elif selected_item == "WiFi":
                self.current_screen = "wifi"
                self.show_wifi_menu()
        elif action == 'left' or action == 'key1':
            self.current_screen = "main"
            self.selected_index = 0
            self.show_main_menu()
    
    def handle_wifi_input(self, action):
        if action == 'left' or action == 'key1':
            self.current_screen = "settings"
            self.selected_index = 1  # Reset to WiFi option
            self.show_settings_menu()
    
    def sync_time_via_wifi(self):
        """Attempt to sync time via WiFi using ntpdate or timedatectl"""
        try:
            self.display.show_message("Syncing...", "Getting time from\nwifi network...", (100, 200, 100))
            
            # Try ntpdate first
            try:
                subprocess.run(['sudo', 'ntpdate', '-s', 'time.nist.gov'], check=False, timeout=10)
                self.display.show_message("Time Synced", "WiFi sync\nsuccessful!", (100, 255, 100))
            except Exception:
                # Try timedatectl with ntp
                try:
                    subprocess.run(['sudo', 'timedatectl', 'set-ntp', 'true'], check=False, timeout=10)
                    time.sleep(2)
                    subprocess.run(['sudo', 'timedatectl', 'set-time', datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')], check=False)
                    self.display.show_message("Time Synced", "WiFi sync\nsuccessful!", (100, 255, 100))
                except Exception:
                    self.display.show_message("Sync Failed", "Unable to sync\ntime via WiFi", (255, 100, 100))
            
            time.sleep(2)
            self.current_screen = "set_time"
            self.show_set_time_screen()
        except Exception as e:
            self.display.show_message("Error", str(e), (255, 100, 100))
            time.sleep(2)
            self.current_screen = "set_time"
            self.show_set_time_screen()
    
    def run(self):
        import time
        
        # Handle time sync on boot if enabled
        if self.sync_on_boot:
            self.sync_time_via_wifi()
            self.sync_on_boot = False  # Only sync once at startup
        
        self.show_main_menu()
        
        last_update = time.time()
        
        while self.running:
            action = self.input_handler.get_input()
            
            if action:
                if self.current_screen == "main":
                    self.handle_main_menu_input(action)
                elif self.current_screen == "schedule":
                    self.handle_schedule_input(action)
                elif self.current_screen == "clock":
                    self.handle_clock_input(action)
                elif self.current_screen == "settings":
                    self.handle_settings_input(action)
                elif self.current_screen == "ab_day":
                    self.handle_ab_day_input(action)
                elif self.current_screen == "wifi":
                    self.handle_wifi_input(action)
                elif self.current_screen == "set_time":
                    self.handle_set_time_input(action)
            
            current_time = time.time()
            if current_time - last_update > 1.0:
                if self.current_screen == "schedule":
                    self.show_schedule_screen()
                elif self.current_screen == "clock":
                    self.show_clock_screen()
                last_update = current_time
            
            # Check if Key3 is being held in set_time screen
            if self.current_screen == "set_time" and self.key3_press_time is not None:
                if time.time() - self.key3_press_time >= 2.0:
                    self.key3_press_time = None  # Reset to prevent multiple triggers
                    self.sync_time_via_wifi()
            
            # Handle periodic time sync if enabled
            if TIME_SYNC_MODE == "periodic":
                sync_interval = TIME_SYNC_INTERVAL * 3600  # Convert hours to seconds
                if current_time - self.last_sync_time > sync_interval:
                    self.sync_time_via_wifi()
                    self.last_sync_time = current_time
            
            time.sleep(0.05)
        
        self.input_handler.cleanup()
