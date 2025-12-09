import datetime
import subprocess
import time
import json
import os
import sys
from config import (
    PERIODS, SCHOOL_START, SCHOOL_END, LUNCH_START, LUNCH_END,
    PERIOD_LENGTH, PASSING_TIME, A_DAY_PERIODS, B_DAY_PERIODS,
    ADVISORY_START, advisory, advisorydays, advisorylength, freetimedaus, USE_24_HOUR,
    AB_DAY_MODE, MANUAL_AB_DAY, TIME_SYNC_MODE, TIME_SYNC_INTERVAL, abday, PROGRESS_BAR_MODE
)
from input_handler import InputHandler
from theme_manager import ThemeManager

class Menu:
    def __init__(self, display, input_handler):
        self.display = display
        self.input_handler = input_handler
        self.current_screen = "main"
        self.selected_index = 0
        self.running = True
        
        # Initialize theme manager
        self.theme_manager = ThemeManager()
        
        self.main_menu_items = ["Schedule", "Clock", "Settings", "Set Time"]
        # Build settings menu items based on config
        self.settings_menu_items = []
        if abday.lower() == "true":
            self.settings_menu_items.append("A/B Day")
        self.settings_menu_items.extend(["WiFi", "Theme", "Progress Bar", "Restart", "Back"])
        self.set_time_menu_items = ["WiFi Sync", "Manual Set", "Back"]
        self.theme_menu_items = self.theme_manager.get_theme_names()
        self.adjust_hour = 0
        self.adjust_minute = 0
        self.ab_day_mode = AB_DAY_MODE  # "auto", "a", or "b"
        self.manual_ab_day = MANUAL_AB_DAY  # "a" or "b" when in manual mode
        self.key3_press_time = None  # Track when Key3 is pressed
        self.last_sync_time = 0  # Track last WiFi sync time for periodic syncing
        self.sync_on_boot = (TIME_SYNC_MODE == "on_boot")  # Flag to sync once at startup
        self.last_sync_error = None  # Store the last sync error message
        self.available_networks = []  # Store scanned WiFi networks
        self.wifi_scan_index = 0  # Index for selecting networks
        self.progress_bar_modes = ["time_in_class", "time_in_day", "lunch_day"]
        self.progress_bar_mode = PROGRESS_BAR_MODE
        self.progress_bar_mode_index = self.progress_bar_modes.index(self.progress_bar_mode) if self.progress_bar_mode in self.progress_bar_modes else 0
    
    def is_advisory_day(self):
        today = datetime.datetime.now().strftime('%a').lower()
        return advisory.lower() == "true" and today[0] in advisorydays.lower().split(',')
    
    def is_freetime_day(self):
        today = datetime.datetime.now().strftime('%a').lower()
        return today[0] in freetimedaus.lower().split(',')
    
    def get_current_ab_day(self):
        """Get current A/B day based on mode"""
        if abday.lower() != "true":
            return "a"  # Default to A if A/B days are disabled
        
        if self.ab_day_mode == "auto":
            # Auto mode: alternate daily starting with A on Monday
            today = datetime.datetime.now()
            days_since_monday = today.weekday()  # 0 = Monday, 6 = Sunday
            # At start of week (Monday), we're on day 0 (A day)
            # Every day, we switch. So: Mon=A, Tue=B, Wed=A, Thu=B, Fri=A
            return "a" if days_since_monday % 2 == 0 else "b"
        else:
            # Manual mode
            return self.manual_ab_day.lower()
    
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
            # Determine which period set to use (A or B day)
            if abday.lower() == "true":
                current_day = self.get_current_ab_day()
                if current_day == "b" and period in B_DAY_PERIODS:
                    period_name = B_DAY_PERIODS[period]
                elif period in A_DAY_PERIODS:
                    period_name = A_DAY_PERIODS[period]
                else:
                    period_name = f"Period {period}"
            else:
                # A/B days disabled, use A_DAY_PERIODS as default
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
        label, progress = self.get_progress_bar()
        self.display.show_menu(self.main_menu_items, self.selected_index, "Main Menu", label, progress)
    
    def get_progress_bar(self):
        """Calculate progress bar based on current mode"""
        try:
            now = datetime.datetime.now()
            
            # Parse times
            school_start = datetime.datetime.strptime(SCHOOL_START, "%H:%M").time()
            school_start_dt = datetime.datetime.combine(datetime.date.today(), school_start)
            school_end = datetime.datetime.strptime(SCHOOL_END, "%H:%M").time()
            school_end_dt = datetime.datetime.combine(datetime.date.today(), school_end)
            lunch_start = datetime.datetime.strptime(LUNCH_START, "%H:%M").time()
            lunch_start_dt = datetime.datetime.combine(datetime.date.today(), lunch_start)
            lunch_end = datetime.datetime.strptime(LUNCH_END, "%H:%M").time()
            lunch_end_dt = datetime.datetime.combine(datetime.date.today(), lunch_end)
            
            # Calculate actual school end time from 6th period end (or latest period)
            actual_school_end = school_end_dt  # Fallback to configured end time
            if 6 in PERIODS:
                period_6_start = datetime.datetime.strptime(PERIODS[6], "%H:%M").time()
                period_6_start_dt = datetime.datetime.combine(datetime.date.today(), period_6_start)
                actual_school_end = period_6_start_dt + datetime.timedelta(minutes=PERIOD_LENGTH)
            else:
                # Find the last period and use that
                if PERIODS:
                    last_period = max(PERIODS.keys())
                    last_period_start = datetime.datetime.strptime(PERIODS[last_period], "%H:%M").time()
                    last_period_start_dt = datetime.datetime.combine(datetime.date.today(), last_period_start)
                    actual_school_end = last_period_start_dt + datetime.timedelta(minutes=PERIOD_LENGTH)
            
            if self.progress_bar_mode == "time_in_class":
                # Progress within current class period
                for period in range(1, 7):
                    if period not in PERIODS:
                        continue
                    period_start = datetime.datetime.strptime(PERIODS[period], "%H:%M").time()
                    period_start_dt = datetime.datetime.combine(datetime.date.today(), period_start)
                    period_end_dt = period_start_dt + datetime.timedelta(minutes=PERIOD_LENGTH)
                    
                    if period_start_dt <= now < period_end_dt:
                        elapsed = (now - period_start_dt).total_seconds()
                        total = PERIOD_LENGTH * 60
                        progress = int((elapsed / total) * 100) if total > 0 else 0
                        return f"Class: {progress}%", progress
                
                # Not in class
                return "Not in class", 0
            
            elif self.progress_bar_mode == "time_in_day":
                # Progress through school day (using actual end time from last period)
                if now < school_start_dt:
                    return "Before school", 0
                elif now >= actual_school_end:
                    return "After school", 100
                else:
                    elapsed = (now - school_start_dt).total_seconds()
                    total = (actual_school_end - school_start_dt).total_seconds()
                    progress = int((elapsed / total) * 100) if total > 0 else 0
                    return f"Day: {progress}%", progress
            
            elif self.progress_bar_mode == "lunch_day":
                # Progress until lunch, then after lunch shows time left in day
                if now < lunch_start_dt:
                    # Before lunch: show progress to lunch
                    elapsed = (now - school_start_dt).total_seconds()
                    total = (lunch_start_dt - school_start_dt).total_seconds()
                    progress = int((elapsed / total) * 100) if total > 0 else 0
                    return f"Until Lunch: {progress}%", progress
                elif now < lunch_end_dt:
                    # During lunch
                    return "Lunch", 100
                elif now >= actual_school_end:
                    # After school
                    return "After school", 100
                else:
                    # After lunch: show time left in day
                    elapsed = (now - lunch_end_dt).total_seconds()
                    total = (actual_school_end - lunch_end_dt).total_seconds()
                    progress = int((elapsed / total) * 100) if total > 0 else 0
                    return f"Day Left: {progress}%", progress
            
            return "Unknown", 0
        except Exception as e:
            # If there's any error in calculation, return safe defaults
            return "Error", 0
    
    def show_settings_menu(self):
        self.display.show_menu(self.settings_menu_items, self.selected_index, "Settings")
    
    def scan_wifi_networks(self):
        """Scan for available WiFi networks using nmcli or iwlist"""
        try:
            self.display.show_message("WiFi", "Scanning for\nnetworks...", (100, 200, 255))
            
            # Try using nmcli (NetworkManager)
            try:
                result = subprocess.run(
                    ['sudo', 'nmcli', 'device', 'wifi', 'list'],
                    capture_output=True, text=True, timeout=10
                )
                if result.returncode == 0:
                    networks = self._parse_nmcli_output(result.stdout)
                    if networks:
                        self.available_networks = networks
                        self.wifi_scan_index = 0
                        return True
            except:
                pass
            
            # Fallback: try iwlist (older systems)
            try:
                result = subprocess.run(
                    ['sudo', 'iwlist', 'wlan0', 'scan'],
                    capture_output=True, text=True, timeout=10
                )
                if result.returncode == 0:
                    networks = self._parse_iwlist_output(result.stdout)
                    if networks:
                        self.available_networks = networks
                        self.wifi_scan_index = 0
                        return True
            except:
                pass
            
            return False
        except Exception as e:
            self.display.show_message("Error", f"Scan failed: {str(e)[:30]}", (255, 100, 100))
            time.sleep(2)
            return False
    
    def _parse_nmcli_output(self, output):
        """Parse nmcli wifi list output"""
        networks = []
        lines = output.strip().split('\n')[1:]  # Skip header
        for line in lines:
            if line.strip():
                # Format: SSID BSSID RSSI CHANNEL SECURITY
                parts = line.split()
                if len(parts) >= 5:
                    ssid = parts[0]
                    security = ' '.join(parts[4:]) if len(parts) > 4 else ""
                    is_open = "--" in security or security.strip() == ""
                    networks.append({"ssid": ssid, "security": security, "open": is_open})
        return networks
    
    def _parse_iwlist_output(self, output):
        """Parse iwlist scan output"""
        networks = []
        current_network = {}
        
        for line in output.split('\n'):
            if 'ESSID' in line and '"' in line:
                # Extract SSID
                ssid = line.split('"')[1]
                current_network['ssid'] = ssid
            elif 'Encryption key:off' in line:
                current_network['open'] = True
                current_network['security'] = "Open"
            elif 'Encryption key:on' in line:
                current_network['open'] = False
            
            if current_network.get('ssid'):
                is_duplicate = any(n['ssid'] == current_network['ssid'] for n in networks)
                if not is_duplicate:
                    networks.append(current_network)
                    current_network = {}
        
        return networks
    
    def show_wifi_menu(self):
        """Show WiFi network selection menu"""
        if not self.available_networks:
            if not self.scan_wifi_networks():
                self.display.show_message("WiFi", "No networks found\nor scan failed", (255, 100, 100))
                time.sleep(2)
                return
        
        self.show_wifi_network_list()
    
    def show_wifi_network_list(self):
        """Display current WiFi network for selection"""
        if not self.available_networks:
            self.display.show_message("WiFi", "No networks\nfound", (200, 100, 100))
            return
        
        network = self.available_networks[self.wifi_scan_index]
        ssid = network['ssid']
        is_open = network.get('open', False)
        status = "[OPEN]" if is_open else "[SECURED]"
        
        message = f"WiFi Network:\n{ssid}\n{status}\n\nUp/Down: Browse\nSelect: Connect"
        self.display.show_message("WiFi", message, (100, 200, 255))
    
    def show_ab_day_menu(self):
        if self.ab_day_mode == "auto":
            message = "A/B Day: Auto\n\nUp/Down: Change\nSelect: Confirm"
        else:
            current = self.manual_ab_day.upper()
            message = f"A/B Day: {current}\n\nUp/Down: Toggle\nSelect: Confirm"
        self.display.show_message("A/B Day", message, (200, 150, 255))
    
    def show_set_time_menu(self):
        self.display.show_menu(self.set_time_menu_items, self.selected_index, "Set Time")
    
    def show_set_time_screen(self):
        if USE_24_HOUR:
            hour_str = f"{self.adjust_hour:02d}"
            minute_str = f"{self.adjust_minute:02d}"
            message = f"Set Time:\n{hour_str}:{minute_str}\n\nKey1: Hour+\nKey2: Min+\nKey3: Done"
        else:
            # Convert to 12-hour format for display
            display_hour = self.adjust_hour % 12
            if display_hour == 0:
                display_hour = 12
            am_pm = "AM" if self.adjust_hour < 12 else "PM"
            hour_str = f"{display_hour:02d}"
            minute_str = f"{self.adjust_minute:02d}"
            message = f"Set Time:\n{hour_str}:{minute_str} {am_pm}\n\nKey1: Hour+\nKey2: Min+\nKey3: Done"
        self.display.show_message("Set Time", message, (255, 200, 100))
    
    def handle_set_time_input(self, action):
        if action == 'key1':  # Increase hour
            self.adjust_hour = (self.adjust_hour + 1) % 24
            self.show_set_time_screen()
        elif action == 'key2':  # Increase minute
            self.adjust_minute = (self.adjust_minute + 1) % 60
            self.show_set_time_screen()
        elif action == 'key3':  # Apply and done
            self.apply_manual_time()
            self.current_screen = "set_time_menu"
            self.selected_index = 0
            self.show_set_time_menu()
        elif action == 'select' or action == 'left':  # Cancel and go back
            self.current_screen = "set_time_menu"
            self.selected_index = 0
            self.show_set_time_menu()
    
    def handle_set_time_menu_input(self, action):
        if action == 'up':
            self.selected_index = (self.selected_index - 1) % len(self.set_time_menu_items)
            self.show_set_time_menu()
        elif action == 'down':
            self.selected_index = (self.selected_index + 1) % len(self.set_time_menu_items)
            self.show_set_time_menu()
        elif action == 'select' or action == 'right':
            selected_item = self.set_time_menu_items[self.selected_index]
            if selected_item == "WiFi Sync":
                self.sync_time_via_wifi()
                self.current_screen = "set_time_menu"
                self.selected_index = 0
                self.show_set_time_menu()
            elif selected_item == "Manual Set":
                self.current_screen = "set_time"
                now = datetime.datetime.now()
                self.adjust_hour = now.hour
                self.adjust_minute = now.minute
                self.show_set_time_screen()
            elif selected_item == "Back":
                self.current_screen = "main"
                self.selected_index = 0
                self.show_main_menu()
        elif action == 'left':
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
        elif action == 'left':
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
                self.current_screen = "set_time_menu"
                self.selected_index = 0
                self.show_set_time_menu()
    
    def handle_schedule_input(self, action):
        if action == 'left':
            self.current_screen = "main"
            self.selected_index = 0
            self.show_main_menu()
    
    def handle_clock_input(self, action):
        if action == 'left':
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
            elif selected_item == "Theme":
                self.current_screen = "theme"
                self.selected_index = 0
                self.show_theme_menu()
            elif selected_item == "Progress Bar":
                self.current_screen = "progress_bar"
                self.show_progress_bar_menu()
            elif selected_item == "Restart":
                self.restart_program()
        elif action == 'left':
            self.current_screen = "main"
            self.selected_index = 0
            self.show_main_menu()
    
    def connect_to_wifi(self, network):
        """Attempt to connect to an open WiFi network"""
        try:
            ssid = network['ssid']
            is_open = network.get('open', False)
            
            if not is_open:
                self.display.show_message("WiFi", "Only open networks\nare supported", (255, 150, 100))
                time.sleep(2)
                return False
            
            self.display.show_message("WiFi", f"Connecting to\n{ssid}...", (100, 200, 255))
            
            # Try connecting using nmcli
            try:
                result = subprocess.run(
                    ['sudo', 'nmcli', 'device', 'wifi', 'connect', ssid],
                    capture_output=True, text=True, timeout=10
                )
                if result.returncode == 0:
                    self.display.show_message("WiFi", f"Connected to\n{ssid}", (100, 255, 100))
                    time.sleep(2)
                    return True
            except:
                pass
            
            # Fallback: try wpa_cli or other methods
            self.display.show_message("WiFi", "Connection\nfailed", (255, 100, 100))
            time.sleep(2)
            return False
        except Exception as e:
            self.display.show_message("Error", str(e)[:30], (255, 100, 100))
            time.sleep(2)
            return False
    
    def handle_wifi_input(self, action):
        if action == 'up':
            if self.available_networks:
                self.wifi_scan_index = (self.wifi_scan_index - 1) % len(self.available_networks)
                self.show_wifi_network_list()
        elif action == 'down':
            if self.available_networks:
                self.wifi_scan_index = (self.wifi_scan_index + 1) % len(self.available_networks)
                self.show_wifi_network_list()
        elif action == 'select' or action == 'right':
            if self.available_networks:
                network = self.available_networks[self.wifi_scan_index]
                self.connect_to_wifi(network)
                self.show_wifi_network_list()
        elif action == 'left':
            self.current_screen = "settings"
            self.selected_index = self.settings_menu_items.index("WiFi") if "WiFi" in self.settings_menu_items else 1
            self.show_settings_menu()
    
    def show_theme_menu(self):
        self.display.show_menu(self.theme_menu_items, self.selected_index, "Theme")
    
    def handle_theme_input(self, action):
        if action == 'up':
            self.selected_index = (self.selected_index - 1) % len(self.theme_menu_items)
            self.show_theme_menu()
        elif action == 'down':
            self.selected_index = (self.selected_index + 1) % len(self.theme_menu_items)
            self.show_theme_menu()
        elif action == 'select' or action == 'right':
            selected_theme = self.theme_menu_items[self.selected_index]
            self.theme_manager.set_theme(selected_theme)
            self.display.show_message("Theme Set", f"Changed to\n{selected_theme.title()}", 
                                     self.theme_manager.get_success())
            time.sleep(1)
            self.current_screen = "settings"
            # Find the Theme option index
            self.selected_index = self.settings_menu_items.index("Theme") if "Theme" in self.settings_menu_items else 2
            self.show_settings_menu()
        elif action == 'left':
            self.current_screen = "settings"
            self.selected_index = self.settings_menu_items.index("Theme") if "Theme" in self.settings_menu_items else 2
            self.show_settings_menu()
    
    def show_progress_bar_menu(self):
        """Display progress bar mode selection"""
        current_mode = self.progress_bar_modes[self.progress_bar_mode_index]
        if current_mode == "time_in_class":
            mode_display = "In Class"
        elif current_mode == "time_in_day":
            mode_display = "In Day"
        elif current_mode == "lunch_day":
            mode_display = "Lunch/Day"
        else:
            mode_display = current_mode.replace("_", " ").title()
        message = f"Progress Bar:\n{mode_display}\n\nUp/Down: Change\nSelect: Confirm"
        self.display.show_message("Progress Bar", message, (100, 150, 255))
    
    def handle_progress_bar_input(self, action):
        if action == 'up':
            self.progress_bar_mode_index = (self.progress_bar_mode_index - 1) % len(self.progress_bar_modes)
            self.progress_bar_mode = self.progress_bar_modes[self.progress_bar_mode_index]
            self.show_progress_bar_menu()
        elif action == 'down':
            self.progress_bar_mode_index = (self.progress_bar_mode_index + 1) % len(self.progress_bar_modes)
            self.progress_bar_mode = self.progress_bar_modes[self.progress_bar_mode_index]
            self.show_progress_bar_menu()
        elif action == 'select' or action == 'right':
            self.current_screen = "settings"
            self.selected_index = self.settings_menu_items.index("Progress Bar") if "Progress Bar" in self.settings_menu_items else 3
            self.show_settings_menu()
        elif action == 'left':
            self.current_screen = "settings"
            self.selected_index = self.settings_menu_items.index("Progress Bar") if "Progress Bar" in self.settings_menu_items else 3
            self.show_settings_menu()
    
    def restart_program(self):
        """Restart the Timagotchi program"""
        try:
            self.display.show_message("Restarting", "Program restarting...", (100, 200, 255))
            time.sleep(1)
            self.input_handler.cleanup()
            self.running = False
            # Use os.execv to replace current process with new one
            os.execv(sys.executable, [sys.executable] + sys.argv)
        except Exception as e:
            self.display.show_message("Error", f"Restart failed: {str(e)[:30]}", (255, 100, 100))
            time.sleep(2)
            self.current_screen = "settings"
            self.selected_index = self.settings_menu_items.index("Restart") if "Restart" in self.settings_menu_items else 2
            self.show_settings_menu()
    
    def sync_time_via_wifi(self):
        """Attempt to sync time via WiFi using timedatectl"""
        try:
            self.display.show_message("Syncing...", "Getting time from\nwifi network...", (100, 200, 100))
            
            try:
                # Ensure NTP is enabled first
                subprocess.run(['sudo', 'timedatectl', 'set-ntp', 'on'], 
                              capture_output=True, text=True, timeout=5, check=False)
                time.sleep(1)
                
                # Wait for NTP to sync (give it a moment)
                time.sleep(3)
                
                # Get the current synced time
                result = subprocess.run(['timedatectl', 'show', '-p', 'NTPSynchronized'],
                                      capture_output=True, text=True, timeout=5)
                
                if "yes" in result.stdout.lower():
                    self.last_sync_error = None
                    self.display.show_message("Time Synced", "WiFi sync\nsuccessful!", (100, 255, 100))
                else:
                    self.last_sync_error = "NTP not synchronized"
                    self.display.show_message("Sync Failed", "NTP sync pending", (255, 100, 100))
                
            except subprocess.TimeoutExpired:
                self.last_sync_error = "Sync timed out"
                self.display.show_message("Sync Failed", "Operation timed out", (255, 100, 100))
            except Exception as e:
                self.last_sync_error = str(e)
                self.display.show_message("Sync Failed", str(e)[:40], (255, 100, 100))
            
            # Wait for display to be visible
            time.sleep(2)
            # Reset all debounce timers to prevent stale presses
            current_time = time.time()
            for pin in self.input_handler.pins:
                self.input_handler.last_press[pin] = current_time
        except Exception as e:
            self.last_sync_error = str(e)
            self.display.show_message("Error", str(e)[:40], (255, 100, 100))
            time.sleep(2)
            # Reset debounce timers
            current_time = time.time()
            for pin in self.input_handler.pins:
                self.input_handler.last_press[pin] = current_time
                time.sleep(0.05)
    
    def apply_manual_time(self):
        """Apply the manually set time"""
        try:
            # Check if NTP is still enabled
            ntp_check = subprocess.run(['timedatectl', 'show', '-p', 'NTP'],
                                      capture_output=True, text=True, timeout=5)
            ntp_enabled = "yes" in ntp_check.stdout.lower()
            
            if ntp_enabled:
                # Try to disable NTP first
                subprocess.run(['sudo', 'timedatectl', 'set-ntp', 'off'], 
                              capture_output=True, text=True, timeout=5, check=False)
                time.sleep(1)
            
            # Format time as HH:MM:SS (always in 24-hour for system)
            time_str = f"{self.adjust_hour:02d}:{self.adjust_minute:02d}:00"
            
            result = subprocess.run(['sudo', 'timedatectl', 'set-time', time_str],
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode != 0:
                error_msg = result.stderr.strip()
                if "ntp" in error_msg.lower() or "synchronized" in error_msg.lower():
                    self.last_sync_error = "Run: sudo timedatectl\nset-ntp false"
                    self.display.show_message("Failed", self.last_sync_error, (255, 100, 100))
                else:
                    self.last_sync_error = error_msg if error_msg else "Failed to set time"
                    self.display.show_message("Failed", self.last_sync_error[:40], (255, 100, 100))
            else:
                self.last_sync_error = None
                # Display time in the configured format
                if USE_24_HOUR:
                    display_time = time_str
                else:
                    display_hour = self.adjust_hour % 12
                    if display_hour == 0:
                        display_hour = 12
                    am_pm = "AM" if self.adjust_hour < 12 else "PM"
                    display_time = f"{display_hour:02d}:{self.adjust_minute:02d} {am_pm}"
                self.display.show_message("Time Set", f"Set to {display_time}", (100, 255, 100))
            
            # Wait for display to be visible
            time.sleep(2)
            # Reset all debounce timers to prevent stale presses
            current_time = time.time()
            for pin in self.input_handler.pins:
                self.input_handler.last_press[pin] = current_time
        except subprocess.TimeoutExpired:
            self.last_sync_error = "Operation timed out"
            self.display.show_message("Failed", "Timeout", (255, 100, 100))
            time.sleep(2)
            # Reset debounce timers
            current_time = time.time()
            for pin in self.input_handler.pins:
                self.input_handler.last_press[pin] = current_time
        except Exception as e:
            self.last_sync_error = str(e)
            self.display.show_message("Error", str(e)[:40], (255, 100, 100))
            time.sleep(2)
            # Reset debounce timers
            current_time = time.time()
            for pin in self.input_handler.pins:
                self.input_handler.last_press[pin] = current_time
    
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
                elif self.current_screen == "theme":
                    self.handle_theme_input(action)
                elif self.current_screen == "progress_bar":
                    self.handle_progress_bar_input(action)
                elif self.current_screen == "set_time_menu":
                    self.handle_set_time_menu_input(action)
                elif self.current_screen == "set_time":
                    self.handle_set_time_input(action)
            
            current_time = time.time()
            if current_time - last_update > 1.0:
                if self.current_screen == "schedule":
                    self.show_schedule_screen()
                elif self.current_screen == "clock":
                    self.show_clock_screen()
                elif self.current_screen == "main":
                    self.show_main_menu()
                last_update = current_time
            
            # Check if Key3 is being held in set_time screen
            if self.current_screen == "set_time" and self.key3_press_time is not None:
                if time.time() - self.key3_press_time >= 3.0:
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
