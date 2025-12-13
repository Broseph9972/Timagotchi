import datetime
import subprocess
import time
import json
import os
import sys
from config import (
    PERIODS, SCHOOL_START, SCHOOL_END, LUNCH_START, LUNCH_END,
    PERIOD_LENGTH, PASSING_TIME, A_DAY_PERIODS, B_DAY_PERIODS,
    freetimedaus, USE_24_HOUR,
    AB_DAY_MODE, MANUAL_AB_DAY, TIME_SYNC_MODE, TIME_SYNC_INTERVAL, abday, PROGRESS_BAR_MODE,
    ADVISORY_START, ADVISORY_PERIOD, advisory, advisorylength, advisorydays
)
from input_handler import InputHandler
from theme_manager import ThemeManager
import json as _json
import requests
from urllib.parse import urljoin

class Menu:
    def __init__(self, display, input_handler):
        self.display = display
        self.input_handler = input_handler
        self.current_screen = "main"
        self.selected_index = 0
        self.running = True
        
        # Initialize theme manager
        self.theme_manager = ThemeManager()
        
        # Right-nav items as per sketch
        self.nav_items = ["Main Page", "Grades", "Settings"]
        self.nav_selected_index = 0
        # Build settings menu items based on config
        self.settings_menu_items = []
        if abday.lower() == "true":
            self.settings_menu_items.append("A/B Day")
        self.settings_menu_items.extend(["WiFi", "Theme", "Progress Bar", "Set Time", "Stopwatch", "Update", "Restart"])
        self.settings_scroll_offset = 0
        self.set_time_menu_items = ["WiFi Sync", "Manual Set"]
        self.theme_menu_items = self.theme_manager.get_theme_names()
        self.adjust_hour = 0
        self.adjust_minute = 0
        self.ab_day_mode = AB_DAY_MODE  # "auto", "a", or "b"
        self.manual_ab_day = MANUAL_AB_DAY  # "a" or "b" when in manual mode
        self.last_sync_time = 0  # Track last WiFi sync time for periodic syncing
        self.sync_on_boot = (TIME_SYNC_MODE == "on_boot")  # Flag to sync once at startup
        self.last_sync_error = None  # Store the last sync error message
        self.available_networks = []  # Store scanned WiFi networks
        self.wifi_scan_index = 0  # Index for selecting networks
        self.progress_bar_modes = ["time_in_class", "time_in_day", "lunch_day"]
        self.progress_bar_mode = PROGRESS_BAR_MODE
        self.progress_bar_mode_index = self.progress_bar_modes.index(self.progress_bar_mode) if self.progress_bar_mode in self.progress_bar_modes else 0
        
        # Preset scheduling state (1=single schedule, 2=two presets that rotate daily)
        self.state_path = os.path.join(os.path.dirname(__file__), 'schedule_state.json')
        self.presets_count = 2  # default to 2 presets
        self.current_preset_index = 0  # 0 = A_DAY_PERIODS, 1 = B_DAY_PERIODS
        self.last_advance_date = None
        self._load_state()
        self._advance_preset_if_new_day()
        # Canvas state
        self.canvas_config_path = os.path.join(os.path.dirname(__file__), 'canvas_config.json')
        self.canvas_cache_path = os.path.join(os.path.dirname(__file__), 'canvas_cache.json')
        # Clear canvas cache on every reboot
        try:
            if os.path.exists(self.canvas_cache_path):
                os.remove(self.canvas_cache_path)
        except Exception:
            pass
        self.current_course_id = None
        self.grades_selected_index = 0
        self.assign_selected_index = 0
        self.assign_scroll_offset = 0
        self.grades_scroll_offset = 0
        # Stopwatch state
        self.stopwatch_running = False
        self.stopwatch_start_ts = 0.0
        self.stopwatch_elapsed = 0.0
    

    
    def is_freetime_day(self):
        today = datetime.datetime.now().strftime('%a').lower()
        return today[0] in freetimedaus.lower().split(',')
    
    def get_current_ab_day(self):
        """Return 'a' or 'b' based on preset index when presets_count==2; otherwise 'a'."""
        if self.presets_count == 2:
            return 'a' if self.current_preset_index == 0 else 'b'
        return 'a'

    def _load_state(self):
        try:
            if os.path.exists(self.state_path):
                with open(self.state_path, 'r') as f:
                    data = json.load(f)
                self.presets_count = int(data.get('presets_count', 2))
                self.current_preset_index = int(data.get('current_preset_index', 0))
                self.last_advance_date = data.get('last_advance_date')
        except Exception:
            pass

    def _save_state(self):
        try:
            data = {
                'presets_count': self.presets_count,
                'current_preset_index': self.current_preset_index,
                'last_advance_date': self.last_advance_date,
            }
            with open(self.state_path, 'w') as f:
                json.dump(data, f)
        except Exception:
            pass

    def _advance_preset_if_new_day(self):
        """Auto-advance preset once per calendar day when presets_count==2."""
        try:
            today_str = datetime.date.today().isoformat()
            if self.presets_count == 2:
                if self.last_advance_date != today_str:
                    # advance
                    self.current_preset_index = (self.current_preset_index + 1) % 2
                    self.last_advance_date = today_str
                    self._save_state()
            else:
                # single schedule; ensure index=0
                if self.current_preset_index != 0:
                    self.current_preset_index = 0
                    self._save_state()
        except Exception:
            pass
    
    def get_current_period(self, current_time):
        lunch_start = datetime.datetime.strptime(LUNCH_START, "%H:%M").time()
        lunch_start = datetime.datetime.combine(datetime.date.today(), lunch_start)
        lunch_end = datetime.datetime.strptime(LUNCH_END, "%H:%M").time()
        lunch_end = datetime.datetime.combine(datetime.date.today(), lunch_end)
        
        if lunch_start <= current_time < lunch_end:
            time_remaining = lunch_end - current_time
            return "LUNCH", time_remaining, True
        
        # Advisory every weekday before period 1 (ignore advisorydays)
        if advisory.lower() == "true":
            if datetime.date.today().weekday() < 5:
                advisory_start = datetime.datetime.strptime(ADVISORY_START, "%H:%M").time()
                advisory_start_dt = datetime.datetime.combine(datetime.date.today(), advisory_start)
                advisory_len = int(advisorylength)
                advisory_end = advisory_start_dt + datetime.timedelta(minutes=advisory_len)
                if advisory_start_dt <= current_time < advisory_end:
                    time_remaining = advisory_end - current_time
                    return "ADVISORY", time_remaining, False
        
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
        wifi_connected = self._get_wifi_connected()
        
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
            self.display.show_message("School Hasn't Started", f"Starts in {time_until_str}\nSchool @ {SCHOOL_START}", (200, 200, 200), self.nav_items, self.nav_selected_index, wifi_connected)
            return
        elif current_time > school_end:
            self.display.show_message("After School", "School day has ended", (200, 200, 200), self.nav_items, self.nav_selected_index, wifi_connected)
            return
        
        period_name = ""
        if period == "ADVISORY":
            period_name = "Advisory"
        elif period == "LUNCH":
            period_name = "Lunch"
        elif period is not None and isinstance(period, int):
            # Determine period name based on presets
            if self.presets_count == 2:
                if self.current_preset_index == 1 and period in B_DAY_PERIODS:
                    period_name = B_DAY_PERIODS[period]
                elif period in A_DAY_PERIODS:
                    period_name = A_DAY_PERIODS[period]
                else:
                    period_name = f"Period {period}"
            else:
                period_name = A_DAY_PERIODS.get(period, f"Period {period}")
        
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
        
        self.display.show_schedule(period, period_name, time_remaining_str, lunch_time_str, end_time_str, current_time_str, self.nav_items, self.nav_selected_index, wifi_connected)
    
    def show_clock_screen(self):
        now = datetime.datetime.now()
        wifi_connected = self._get_wifi_connected()
        if USE_24_HOUR:
            time_str = now.strftime("%H:%M:%S")
        else:
            time_str = now.strftime("%I:%M:%S %p")
        date_str = now.strftime("%A, %B %d")
        self.display.show_clock(time_str, date_str, self.nav_items, self.nav_selected_index, wifi_connected)
    
    def _get_wifi_connected(self):
        """Best-effort check for WiFi connectivity (nmcli); fallback to False."""
        try:
            result = subprocess.run(['nmcli', '-t', '-f', 'STATE', 'g'], capture_output=True, text=True, timeout=2)
            state = result.stdout.strip().lower()
            if 'connected' in state:
                return True
        except Exception:
            pass
        return False

    def _get_schedule_summary(self):
        now = datetime.datetime.now()
        period, time_remaining, is_lunch = self.get_current_period(now)
        if period == "LUNCH":
            return "Lunch"
        if period == "ADVISORY":
            return "Advisory"
        if period is None:
            return "Passing"
        # map to name
        if isinstance(period, int):
            if abday.lower() == "true":
                current_day = self.get_current_ab_day()
                if current_day == "b" and period in B_DAY_PERIODS:
                    name = B_DAY_PERIODS[period]
                else:
                    name = A_DAY_PERIODS.get(period, f"Period {period}")
            else:
                name = A_DAY_PERIODS.get(period, f"Period {period}")
            rem = self.format_timedelta(time_remaining) if time_remaining else ""
            return f"{name} • {rem}"
        return ""

    def show_main_menu(self):
        label, progress = self.get_progress_bar()
        now = datetime.datetime.now()
        time_str = now.strftime("%H:%M") if USE_24_HOUR else now.strftime("%I:%M %p")
        date_str = now.strftime("%a %b %d")
        schedule_summary = self._get_schedule_summary()
        wifi_connected = self._get_wifi_connected()
        bubble_text = schedule_summary or ""  # show period/advisory/passing in bubble
        self.display.show_main_page(label, progress, time_str, date_str, None, wifi_connected, self.nav_items, self.nav_selected_index, bubble_text)
    
    def get_progress_bar(self):
        """Calculate progress bar based on current mode."""
        try:
            now = datetime.datetime.now()

            # Parse times
            school_start_dt = datetime.datetime.combine(
                datetime.date.today(), datetime.datetime.strptime(SCHOOL_START, "%H:%M").time()
            )
            school_end_dt = datetime.datetime.combine(
                datetime.date.today(), datetime.datetime.strptime(SCHOOL_END, "%H:%M").time()
            )
            lunch_start_dt = datetime.datetime.combine(
                datetime.date.today(), datetime.datetime.strptime(LUNCH_START, "%H:%M").time()
            )
            lunch_end_dt = datetime.datetime.combine(
                datetime.date.today(), datetime.datetime.strptime(LUNCH_END, "%H:%M").time()
            )

            # Determine actual end based on last period if available
            actual_school_end = school_end_dt
            if PERIODS:
                last_period = max(PERIODS.keys())
                last_start_dt = datetime.datetime.combine(
                    datetime.date.today(), datetime.datetime.strptime(PERIODS[last_period], "%H:%M").time()
                )
                actual_school_end = last_start_dt + datetime.timedelta(minutes=PERIOD_LENGTH)

            mode = self.progress_bar_modes[self.progress_bar_mode_index]
            if mode == "time_in_class":
                # Progress within current class period
                for p in sorted(PERIODS.keys()):
                    start_dt = datetime.datetime.combine(
                        datetime.date.today(), datetime.datetime.strptime(PERIODS[p], "%H:%M").time()
                    )
                    end_dt = start_dt + datetime.timedelta(minutes=PERIOD_LENGTH)
                    if start_dt <= now < end_dt:
                        elapsed = (now - start_dt).total_seconds()
                        total = (end_dt - start_dt).total_seconds()
                        progress = int((elapsed / total) * 100) if total > 0 else 0
                        return f"Class: {progress}%", progress
                return "Not in class", 0

            if mode == "time_in_day":
                if now < school_start_dt:
                    return "Before school", 0
                if now >= actual_school_end:
                    return "After school", 100
                elapsed = (now - school_start_dt).total_seconds()
                total = (actual_school_end - school_start_dt).total_seconds()
                progress = int((elapsed / total) * 100) if total > 0 else 0
                return f"Day: {progress}%", progress

            if mode == "lunch_day":
                if now < lunch_start_dt:
                    elapsed = (now - school_start_dt).total_seconds()
                    total = (lunch_start_dt - school_start_dt).total_seconds()
                    progress = int((elapsed / total) * 100) if total > 0 else 0
                    return f"Until Lunch: {progress}%", progress
                if now < lunch_end_dt:
                    return "Lunch", 100
                if now >= actual_school_end:
                    return "After school", 100
                elapsed = (now - lunch_end_dt).total_seconds()
                total = (actual_school_end - lunch_end_dt).total_seconds()
                progress = int((elapsed / total) * 100) if total > 0 else 0
                return f"Day Left: {progress}%", progress

            return "Unknown", 0
        except Exception:
            return "Error", 0
    
    def show_settings_menu(self):
        # Adjust scroll window to keep selection visible
        max_visible = 6
        wifi_connected = self._get_wifi_connected()
        if self.selected_index < self.settings_scroll_offset:
            self.settings_scroll_offset = self.selected_index
        elif self.selected_index >= self.settings_scroll_offset + max_visible:
            self.settings_scroll_offset = self.selected_index - max_visible + 1
        self.display.show_menu(self.settings_menu_items, self.selected_index, "Settings", nav_items=self.nav_items, nav_selected_index=self.nav_selected_index, start_index=self.settings_scroll_offset, max_visible=max_visible, wifi_connected=wifi_connected)

    def _show_presets_menu(self):
        msg = f"Presets: {self.presets_count}\nUp/Down: 1 or 2\nSelect: Save"
        wifi_connected = self._get_wifi_connected()
        self.display.show_message("Schedule Presets", msg, (150, 200, 255), self.nav_items, self.nav_selected_index, wifi_connected)

    def _handle_presets_input(self, action):
        if action == 'up':
            self.presets_count = 1
            self._show_presets_menu()
        elif action == 'down':
            self.presets_count = 2
            self._show_presets_menu()
        elif action in ('select', 'right', 'left'):
            if self.presets_count == 1:
                self.current_preset_index = 0
            self._save_state()
            self.current_screen = 'settings'
            self.selected_index = self.settings_menu_items.index("Schedule Presets")
            self.show_settings_menu()
    def _show_set_today_preset(self):
        label = 'A' if self.current_preset_index == 0 else 'B'
        msg = f"Today Preset: {label}\nUp/Down: Toggle\nSelect: Set & Auto-advance daily"
        wifi_connected = self._get_wifi_connected()
        self.display.show_message("Set Today", msg, (150, 255, 200), self.nav_items, self.nav_selected_index, wifi_connected)

    def _handle_set_today_input(self, action):
        if action in ('up', 'down'):
            # Toggle preset
            self.current_preset_index = 0 if self.current_preset_index == 1 else 1
            self._show_set_today_preset()
        elif action in ('select', 'right', 'left'):
            # Set today and return to settings
            self.last_advance_date = datetime.date.today().isoformat()
            self._save_state()
            self.current_screen = 'settings'
            self.selected_index = self.settings_menu_items.index("Set Today Preset")
            self.show_settings_menu()
    
    def scan_wifi_networks(self):
        """Scan for available WiFi networks using nmcli or iwlist."""
        try:
            wifi_connected = self._get_wifi_connected()
            self.display.show_message("WiFi", "Scanning for\nnetworks...", (100, 200, 255), self.nav_items, self.nav_selected_index, wifi_connected)
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
            except Exception:
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
            except Exception:
                pass

            return False
        except Exception as e:
            wifi_connected = self._get_wifi_connected()
            self.display.show_message("Error", f"Scan failed: {str(e)[:30]}", (255, 100, 100), self.nav_items, self.nav_selected_index, wifi_connected)
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
                wifi_connected = self._get_wifi_connected()
                self.display.show_message("WiFi", "No networks found\nor scan failed", (255, 100, 100), self.nav_items, self.nav_selected_index, wifi_connected)
                time.sleep(2)
                return
        
        self.show_wifi_network_list()
    
    def show_wifi_network_list(self):
        """Display current WiFi network for selection"""
        if not self.available_networks:
            wifi_connected = self._get_wifi_connected()
            self.display.show_message("WiFi", "No networks\nfound", (200, 100, 100), self.nav_items, self.nav_selected_index, wifi_connected)
            return
        
        network = self.available_networks[self.wifi_scan_index]
        ssid = network['ssid']
        is_open = network.get('open', False)
        status = "[OPEN]" if is_open else "[SECURED]"
        
        message = f"WiFi Network:\n{ssid}\n{status}\n\nUp/Down: Browse\nSelect: Connect"
        wifi_connected = self._get_wifi_connected()
        self.display.show_message("WiFi", message, (100, 200, 255), self.nav_items, self.nav_selected_index, wifi_connected)
    
    def show_ab_day_menu(self):
        label = 'A' if self.current_preset_index == 0 else 'B'
        message = f"A/B Day: {label}\n\nUp/Down: Toggle\nSelect: Done"
        wifi_connected = self._get_wifi_connected()
        self.display.show_message("A/B Day", message, (200, 150, 255), self.nav_items, self.nav_selected_index, wifi_connected)
    
    def show_set_time_menu(self):
        wifi_connected = self._get_wifi_connected()
        self.display.show_menu(self.set_time_menu_items, self.selected_index, "Set Time", nav_items=self.nav_items, nav_selected_index=self.nav_selected_index, wifi_connected=wifi_connected)
    
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
        wifi_connected = self._get_wifi_connected()
        self.display.show_message("Set Time", message, (255, 200, 100), self.nav_items, self.nav_selected_index, wifi_connected)
    
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
        elif action == 'left':
            self.current_screen = "settings"
            self.selected_index = 0
            self.show_settings_menu()
    
    def handle_ab_day_input(self, action):
        if action in ('up', 'down'):
            # Toggle between A and B
            self.current_preset_index = 0 if self.current_preset_index == 1 else 1
            self.last_advance_date = datetime.date.today().isoformat()
            self._save_state()
            self.show_ab_day_menu()
        elif action in ('select', 'right', 'left'):
            self.current_screen = "settings"
            self.selected_index = 0
            self.show_settings_menu()
    
    def handle_main_menu_input(self, action):
        # Sidebar is only accessible via key1/2/3; ignore up/down for nav
        if action == 'select' or action == 'right':
            selected_item = self.nav_items[self.nav_selected_index]
            if selected_item == "Main Page":
                self.current_screen = "main"
                self.show_main_menu()
            elif selected_item == "Grades":
                self.current_screen = "grades"
                self.show_grades_menu()
            elif selected_item == "Settings":
                self.current_screen = "settings"
                self.selected_index = 0
                self.show_settings_menu()
    
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
            if selected_item == "A/B Day":
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
            elif selected_item == "Set Time":
                self.current_screen = "set_time_menu"
                self.selected_index = 0
                self.show_set_time_menu()
            elif selected_item == "Stopwatch":
                self.current_screen = 'stopwatch'
                self.show_stopwatch()
            elif selected_item == "Update":
                self._run_update()
            elif selected_item == "Restart":
                self.restart_program()
        elif action == 'left':
            self.current_screen = "main"
            self.selected_index = 0
            self.show_main_menu()

    def _format_stopwatch_time(self):
        total = self.stopwatch_elapsed
        if self.stopwatch_running:
            total += time.time() - self.stopwatch_start_ts
        minutes = int(total // 60)
        seconds = int(total % 60)
        tenths = int((total - int(total)) * 10)
        return f"{minutes:02d}:{seconds:02d}.{tenths}"

    def show_stopwatch(self):
        wifi_connected = self._get_wifi_connected()
        status = "Stop" if self.stopwatch_running else "Start"
        elapsed_txt = self._format_stopwatch_time()
        msg = f"{elapsed_txt}\nUp: Reset\nSelect: {status}"
        self.display.show_message("Stopwatch", msg, (150, 200, 255), self.nav_items, self.nav_selected_index, wifi_connected)

    def handle_stopwatch_input(self, action):
        if action == 'up':
            # Reset elapsed time, keep running state unchanged
            self.stopwatch_elapsed = 0.0
            if self.stopwatch_running:
                self.stopwatch_start_ts = time.time()
            self.show_stopwatch()
        elif action in ('select', 'right'):
            # Toggle start/stop
            if self.stopwatch_running:
                self.stopwatch_elapsed += time.time() - self.stopwatch_start_ts
                self.stopwatch_running = False
            else:
                self.stopwatch_start_ts = time.time()
                self.stopwatch_running = True
            self.show_stopwatch()
        elif action == 'left':
            self.current_screen = 'settings'
            self.selected_index = self.settings_menu_items.index("Stopwatch") if "Stopwatch" in self.settings_menu_items else 0
            self.show_settings_menu()
    def _run_update(self):
        """Run a safe git pull (ff-only) from /home/pi/Timagotchi and report status.
        Auto-add remote origin if missing.
        """
        try:
            # Use the Pi repo path explicitly as requested
            repo_dir = "/home/pi/Timagotchi"
            # Verify git is available
            git_check = subprocess.run(['git', '--version'], capture_output=True, text=True, timeout=5)
            if git_check.returncode != 0:
                self.display.show_message("Update", "git not installed", (255, 100, 100), self.nav_items, self.nav_selected_index)
                return

            # Address potential "dubious ownership" on newer Git versions
            try:
                subprocess.run(['git', 'config', '--global', '--add', 'safe.directory', repo_dir], capture_output=True, text=True, timeout=5)
            except Exception:
                pass

            # Ensure remote origin exists; add if missing
            remote = subprocess.run(['git', '-C', repo_dir, 'config', '--get', 'remote.origin.url'], capture_output=True, text=True, timeout=5)
            if remote.returncode != 0 or not remote.stdout.strip():
                origin_url = 'https://github.com/broseph9972/Timagotchi'
                add_remote = subprocess.run(['git', '-C', repo_dir, 'remote', 'add', 'origin', origin_url], capture_output=True, text=True, timeout=10)
                if add_remote.returncode != 0:
                    err_txt = (add_remote.stderr or '').lower()
                    # If origin already exists, proceed; otherwise report
                    if 'already exists' not in err_txt:
                        err = add_remote.stderr.strip()[:80] or "Failed to add origin"
                        self.display.show_message("Update", err, (255, 100, 100), self.nav_items, self.nav_selected_index)
                        return

            # Get current branch (default to main if detached)
            branch = subprocess.run(['git', '-C', repo_dir, 'rev-parse', '--abbrev-ref', 'HEAD'], capture_output=True, text=True, timeout=5)
            current_branch = branch.stdout.strip() or 'main'
            if current_branch in ('HEAD', ''):
                current_branch = 'main'

            # Fetch and fast-forward only
            subprocess.run(['git', '-C', repo_dir, 'fetch', '--all', '--prune'], capture_output=True, text=True, timeout=20)
            result = subprocess.run(['git', '-C', repo_dir, 'pull', '--ff-only', 'origin', current_branch], capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                msg = result.stdout.strip() or "Up to date"
                self.display.show_message("Update", msg[:60], (100, 255, 100), self.nav_items, self.nav_selected_index)
            else:
                err = result.stderr.strip()[:80] or "Pull failed"
                self.display.show_message("Update", err, (255, 100, 100), self.nav_items, self.nav_selected_index)
        except Exception as e:
            self.display.show_message("Update", (str(e) or "error")[:80], (255, 100, 100), self.nav_items, self.nav_selected_index)

    def show_grades_menu(self, fetch=True):
        """Display grades menu. fetch=True to fetch from API, False to redraw cached list."""
        if fetch:
            cfg = self._canvas_load_config()
            if not cfg:
                self.display.show_message("Canvas", "Set URL & API key", (255, 150, 100), self.nav_items, self.nav_selected_index, self._get_wifi_connected())
                return
            self.display.show_message("Canvas", "Loading courses...", (100, 200, 255), self.nav_items, self.nav_selected_index, self._get_wifi_connected())
            courses = self._canvas_fetch_courses(cfg)
            if courses is None:
                self.display.show_message("Canvas", "Fetch failed", (255, 100, 100), self.nav_items, self.nav_selected_index, self._get_wifi_connected())
                return
            if not courses:
                self.display.show_message("Canvas", "No courses", (200, 200, 200), self.nav_items, self.nav_selected_index, self._get_wifi_connected())
                return
            self._courses_list = courses
        
        # Use cached list; adjust scroll if needed
        if not hasattr(self, '_courses_list') or not self._courses_list:
            self.display.show_message("Canvas", "No courses", (200, 200, 200), self.nav_items, self.nav_selected_index, self._get_wifi_connected())
            return
        
        max_visible = 6
        if self.grades_selected_index < self.grades_scroll_offset:
            self.grades_scroll_offset = self.grades_selected_index
        elif self.grades_selected_index >= self.grades_scroll_offset + max_visible:
            self.grades_scroll_offset = self.grades_selected_index - max_visible + 1
        
        items = [f"{c['name'][:10]} {self._format_percent(c['percent'])}" for c in self._courses_list]
        self.display.show_grades_menu(items, self.grades_selected_index, title="Grades", nav_items=self.nav_items, nav_selected_index=self.nav_selected_index, start_index=self.grades_scroll_offset, max_visible=max_visible, wifi_connected=self._get_wifi_connected())
    
    def connect_to_wifi(self, network):
        """Attempt to connect to an open WiFi network"""
        try:
            ssid = network['ssid']
            is_open = network.get('open', False)
            
            if not is_open:
                self.display.show_message("WiFi", "Only open networks\nare supported", (255, 150, 100), self.nav_items, self.nav_selected_index)
                time.sleep(2)
                return False
            
            self.display.show_message("WiFi", f"Connecting to\n{ssid}...", (100, 200, 255), self.nav_items, self.nav_selected_index)
            
            # Try connecting using nmcli
            try:
                result = subprocess.run(
                    ['sudo', 'nmcli', 'device', 'wifi', 'connect', ssid],
                    capture_output=True, text=True, timeout=10
                )
                if result.returncode == 0:
                    self.display.show_message("WiFi", f"Connected to\n{ssid}", (100, 255, 100), self.nav_items, self.nav_selected_index)
                    time.sleep(2)
                    return True
            except:
                pass
            
            # Fallback: try wpa_cli or other methods
            self.display.show_message("WiFi", "Connection\nfailed", (255, 100, 100), self.nav_items, self.nav_selected_index)
            time.sleep(2)
            return False
        except Exception as e:
            self.display.show_message("Error", str(e)[:30], (255, 100, 100), self.nav_items, self.nav_selected_index)
            time.sleep(2)
            return False

    def handle_grades_input(self, action):
        if not hasattr(self, '_courses_list') or not self._courses_list:
            self.show_grades_menu(fetch=True)
            return
        if action == 'up':
            self.grades_selected_index = (self.grades_selected_index - 1) % len(self._courses_list)
            self.show_grades_menu(fetch=False)
        elif action == 'down':
            self.grades_selected_index = (self.grades_selected_index + 1) % len(self._courses_list)
            self.show_grades_menu(fetch=False)
        elif action in ('select', 'right'):
            course = self._courses_list[self.grades_selected_index]
            self.current_course_id = course['id']
            self.current_screen = 'assignments'
            self.assign_selected_index = 0
            self.show_assignments_menu()
        elif action == 'left':
            self.current_screen = 'main'
            self.nav_selected_index = 0  # Set to Main Page
            self.show_main_menu()

    def show_assignments_menu(self, fetch=True):
        """Display assignments menu. fetch=True to fetch from API, False to redraw cached list."""
        if fetch:
            cfg = self._canvas_load_config()
            if not cfg or self.current_course_id is None:
                self.display.show_message("Canvas", "Missing course/config", (255, 100, 100), self.nav_items, self.nav_selected_index, self._get_wifi_connected())
                return
            self.display.show_message("Canvas", "Loading assigns...", (100, 200, 255), self.nav_items, self.nav_selected_index, self._get_wifi_connected())
            assigns = self._canvas_fetch_assignments(cfg, self.current_course_id)
            if assigns is None:
                self.display.show_message("Canvas", "Fetch failed", (255, 100, 100), self.nav_items, self.nav_selected_index, self._get_wifi_connected())
                return
            if not assigns:
                self.display.show_message("Canvas", "No assignments", (200, 200, 200), self.nav_items, self.nav_selected_index, self._get_wifi_connected())
                return
            self._assign_list = assigns
        
        # Use cached list; adjust scroll if needed
        if not hasattr(self, '_assign_list') or not self._assign_list:
            self.display.show_message("Canvas", "No assignments", (200, 200, 200), self.nav_items, self.nav_selected_index, self._get_wifi_connected())
            return
        
        max_visible = 6
        if self.assign_selected_index < self.assign_scroll_offset:
            self.assign_scroll_offset = self.assign_selected_index
        elif self.assign_selected_index >= self.assign_scroll_offset + max_visible:
            self.assign_scroll_offset = self.assign_selected_index - max_visible + 1
        
        items = [self._format_assignment_item(a) for a in self._assign_list]
        course = next((c for c in getattr(self, '_courses_list', []) if c['id'] == self.current_course_id), None)
        course_title = (course['name'] if course else 'Assignments')
        title = f"{course_title[:10]} {self._format_percent(course.get('percent') if course else None)}"
        self.display.show_menu(items, self.assign_selected_index, title=title, nav_items=self.nav_items, nav_selected_index=self.nav_selected_index, start_index=self.assign_scroll_offset, max_visible=max_visible, wifi_connected=self._get_wifi_connected())

    def handle_assignments_input(self, action):
        if not hasattr(self, '_assign_list') or not self._assign_list:
            self.show_assignments_menu(fetch=True)
            return
        if action == 'up':
            self.assign_selected_index = (self.assign_selected_index - 1) % len(self._assign_list)
            self.show_assignments_menu(fetch=False)
        elif action == 'down':
            self.assign_selected_index = (self.assign_selected_index + 1) % len(self._assign_list)
            self.show_assignments_menu(fetch=False)
        elif action in ('select', 'right'):
            a = self._assign_list[self.assign_selected_index]
            msg = f"Score: {self._format_score(a)}\nStatus: {a.get('status','--')}\nDue: {a.get('due','--')}"
            self.display.show_message("Assignment", msg, (150, 200, 255), self.nav_items, self.nav_selected_index, self._get_wifi_connected())
        elif action == 'left':
            self.current_screen = 'grades'
            self.show_grades_menu(fetch=False)

    def _format_percent(self, p):
        try:
            if p is None:
                return "--"
            return f"{int(round(float(p)))}%"
        except Exception:
            return str(p)[:6] if p else "--"

    def _format_assignment_item(self, a):
        name = (a.get('name') or 'Assignment')[:10]
        score = self._format_score(a)
        return f"{name} {score}"

    def _format_score(self, a):
        score = a.get('score')
        points = a.get('points')
        if score is None or points is None:
            entered = a.get('entered')
            return entered[:6] if entered else "--"
        try:
            return f"{int(round(score))}/{int(round(points))}"
        except Exception:
            return f"{score}/{points}"

    def _canvas_load_config(self):
        try:
            if not os.path.exists(self.canvas_config_path):
                return None
            with open(self.canvas_config_path, 'r') as f:
                cfg = _json.load(f)
            base = cfg.get('base_url')
            token = cfg.get('api_token')
            if not base or not token:
                return None
            if not base.startswith('http'):
                base = 'https://' + base
            return {'base_url': base.rstrip('/'), 'api_token': token}
        except Exception:
            return None

    def _canvas_request(self, cfg, path, params=None):
        try:
            s = requests.Session()
            s.headers.update({'Authorization': f"Bearer {cfg['api_token']}", 'Accept': 'application/json'})
            url = urljoin(cfg['base_url'] + '/', 'api/v1/' + path.lstrip('/'))
            results = []
            while url:
                r = s.get(url, params=params, timeout=5)
                if r.status_code == 429:
                    time.sleep(1)
                    r = s.get(url, params=params, timeout=5)
                if r.status_code >= 400:
                    return None
                data = r.json()
                if isinstance(data, list):
                    results.extend(data)
                else:
                    results.append(data)
                # follow Link rel=next
                link = r.headers.get('Link', '')
                next_url = None
                for part in link.split(','):
                    if 'rel="next"' in part:
                        next_url = part[part.find('<')+1:part.find('>')]
                        break
                url = next_url
                params = None
            return results
        except Exception:
            return None

    def _read_cache(self):
        try:
            if os.path.exists(self.canvas_cache_path):
                with open(self.canvas_cache_path, 'r') as f:
                    return _json.load(f)
        except Exception:
            pass
        return {}

    def _write_cache(self, data):
        try:
            with open(self.canvas_cache_path, 'w') as f:
                _json.dump(data, f)
        except Exception:
            pass

    def _canvas_fetch_courses(self, cfg):
        cache = self._read_cache()
        now_ts = time.time()
        c_entry = cache.get('courses')
        if c_entry and now_ts < c_entry.get('expires', 0):
            return c_entry.get('data', [])
        data = self._canvas_request(cfg, 'users/self/courses', params={'include[]':['enrollments','total_scores'],'enrollment_state':'active','per_page':50})
        if data is None:
            return None
        courses = []
        for c in data:
            name = c.get('name') or c.get('course_code') or 'Course'
            percent = None
            grade_text = None
            
            # Try to get score from enrollments first
            for e in c.get('enrollments', []):
                if e.get('computed_current_score') is not None:
                    percent = e['computed_current_score']
                    break
                if e.get('current_score') is not None:
                    percent = e['current_score']
                    break
                if e.get('computed_final_score') is not None:
                    percent = e['computed_final_score']
                    break
                if e.get('final_score') is not None:
                    percent = e['final_score']
                    break
                # Fallback to letter grade
                if grade_text is None:
                    grade_text = e.get('computed_current_grade') or e.get('current_grade') or e.get('computed_final_grade') or e.get('final_grade')
            
            # If no score in enrollments, try course-level grades
            if percent is None:
                g = c.get('grades') or {}
                percent = g.get('current_score') or g.get('final_score')
                if grade_text is None:
                    grade_text = g.get('current_grade') or g.get('final_grade')
            
            courses.append({'id': c.get('id'), 'name': name, 'percent': percent if percent is not None else grade_text})
        cache['courses'] = {'data': courses, 'expires': now_ts + 600}
        self._write_cache(cache)
        return courses

    def _canvas_fetch_assignments(self, cfg, course_id):
        cache = self._read_cache()
        now_ts = time.time()
        a_key = f'assigns_{course_id}'
        a_entry = cache.get(a_key)
        if a_entry and now_ts < a_entry.get('expires', 0):
            return a_entry.get('data', [])
        data = self._canvas_request(cfg, f'courses/{course_id}/assignments', params={'include[]':'submission','per_page':50})
        if data is None:
            return None
        assigns = []
        for a in data:
            sub = a.get('submission') or {}
            assigns.append({
                'id': a.get('id'),
                'name': a.get('name') or 'Assignment',
                'points': a.get('points_possible'),
                'score': sub.get('score'),
                'entered': sub.get('entered_grade'),
                'status': sub.get('workflow_state'),
                'due': a.get('due_at')
            })
        cache[a_key] = {'data': assigns, 'expires': now_ts + 300}
        self._write_cache(cache)
        return assigns
    
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
        wifi_connected = self._get_wifi_connected()
        self.display.show_menu(self.theme_menu_items, self.selected_index, "Theme", nav_items=self.nav_items, nav_selected_index=self.nav_selected_index, wifi_connected=wifi_connected)
    
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
            wifi_connected = self._get_wifi_connected()
            self.display.show_message("Theme Set", f"Changed to\n{selected_theme.title()}", 
                                     self.theme_manager.get_success(), self.nav_items, self.nav_selected_index, wifi_connected)
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
        self.display.show_message("Progress Bar", message, (100, 150, 255), self.nav_items, self.nav_selected_index)
    
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
            self.display.show_message("Restarting", "Program restarting...", (100, 200, 255), self.nav_items, self.nav_selected_index)
            time.sleep(1)
            self.input_handler.cleanup()
            self.running = False
            # Use os.execv to replace current process with new one
            os.execv(sys.executable, [sys.executable] + sys.argv)
        except Exception as e:
            self.display.show_message("Error", f"Restart failed: {str(e)[:30]}", (255, 100, 100), self.nav_items, self.nav_selected_index)
            time.sleep(2)
            self.current_screen = "settings"
            self.selected_index = self.settings_menu_items.index("Restart") if "Restart" in self.settings_menu_items else 2
            self.show_settings_menu()
    
    def sync_time_via_wifi(self):
        """Attempt to sync time via WiFi using timedatectl"""
        try:
            self.display.show_message("Syncing...", "Getting time from\nwifi network...", (100, 200, 100), self.nav_items, self.nav_selected_index)
            
            try:
                # Set timezone first (import from config)
                try:
                    from config import TIMEZONE
                except ImportError:
                    TIMEZONE = "America/New_York"  # Default if not in config
                
                subprocess.run(['sudo', 'timedatectl', 'set-timezone', TIMEZONE], 
                              capture_output=True, text=True, timeout=5, check=False)
                
                # Ensure NTP is enabled
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
                    self.display.show_message("Time Synced", "WiFi sync\nsuccessful!", (100, 255, 100), self.nav_items, self.nav_selected_index)
                else:
                    self.last_sync_error = "NTP not synchronized"
                    self.display.show_message("Sync Failed", "NTP sync pending", (255, 100, 100), self.nav_items, self.nav_selected_index)
                
            except subprocess.TimeoutExpired:
                self.last_sync_error = "Sync timed out"
                self.display.show_message("Sync Failed", "Operation timed out", (255, 100, 100), self.nav_items, self.nav_selected_index)
            except Exception as e:
                self.last_sync_error = str(e)
                self.display.show_message("Sync Failed", str(e)[:40], (255, 100, 100), self.nav_items, self.nav_selected_index)
            
            # Wait for display to be visible
            time.sleep(2)
            # Reset all debounce timers to prevent stale presses
            current_time = time.time()
            for pin in self.input_handler.pins:
                self.input_handler.last_press[pin] = current_time
        except Exception as e:
            self.last_sync_error = str(e)
            self.display.show_message("Error", str(e)[:40], (255, 100, 100), self.nav_items, self.nav_selected_index)
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
                    self.display.show_message("Failed", self.last_sync_error, (255, 100, 100), self.nav_items, self.nav_selected_index)
                else:
                    self.last_sync_error = error_msg if error_msg else "Failed to set time"
                    self.display.show_message("Failed", self.last_sync_error[:40], (255, 100, 100), self.nav_items, self.nav_selected_index)
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
                self.display.show_message("Time Set", f"Set to {display_time}", (100, 255, 100), self.nav_items, self.nav_selected_index)
            
            # Wait for display to be visible
            time.sleep(2)
            # Reset all debounce timers to prevent stale presses
            current_time = time.time()
            for pin in self.input_handler.pins:
                self.input_handler.last_press[pin] = current_time
        except subprocess.TimeoutExpired:
            self.last_sync_error = "Operation timed out"
            self.display.show_message("Failed", "Timeout", (255, 100, 100), self.nav_items, self.nav_selected_index)
            time.sleep(2)
            # Reset debounce timers
            current_time = time.time()
            for pin in self.input_handler.pins:
                self.input_handler.last_press[pin] = current_time
        except Exception as e:
            self.last_sync_error = str(e)
            self.display.show_message("Error", str(e)[:40], (255, 100, 100), self.nav_items, self.nav_selected_index)
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
                # Global key mapping: key1=Main Page, key2=Grades, key3=Settings
                if action in ('key1', 'key2', 'key3'):
                    if action == 'key1':
                        self.current_screen = 'main'
                        self.nav_selected_index = self.nav_items.index('Main Page') if 'Main Page' in self.nav_items else 0
                        self.show_main_menu()
                        continue
                    elif action == 'key2':
                        self.current_screen = 'grades'
                        self.nav_selected_index = self.nav_items.index('Grades') if 'Grades' in self.nav_items else 1
                        self.show_grades_menu()
                        continue
                    elif action == 'key3':
                        self.current_screen = 'settings'
                        self.nav_selected_index = self.nav_items.index('Settings') if 'Settings' in self.nav_items else 2
                        self.selected_index = 0
                        self.show_settings_menu()
                        continue
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
                elif self.current_screen == "grades":
                    self.handle_grades_input(action)
                elif self.current_screen == "assignments":
                    self.handle_assignments_input(action)
                elif self.current_screen == "stopwatch":
                    self.handle_stopwatch_input(action)
            
            current_time = time.time()
            if current_time - last_update > 1.0:
                if self.current_screen == "schedule":
                    self.show_schedule_screen()
                elif self.current_screen == "clock":
                    self.show_clock_screen()
                elif self.current_screen == "main":
                    self.show_main_menu()
                elif self.current_screen == "stopwatch":
                    self.show_stopwatch()
                last_update = current_time
            
            # Handle periodic time sync if enabled
            if TIME_SYNC_MODE == "periodic":
                sync_interval = TIME_SYNC_INTERVAL * 3600  # Convert hours to seconds
                if current_time - self.last_sync_time > sync_interval:
                    self.sync_time_via_wifi()
                    self.last_sync_time = current_time
            
            time.sleep(0.05)
        
        self.input_handler.cleanup()
