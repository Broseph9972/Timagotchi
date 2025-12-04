import datetime
import subprocess
import time
from config import (
    PERIODS, SCHOOL_START, SCHOOL_END, LUNCH_START, LUNCH_END,
    PERIOD_LENGTH, PASSING_TIME, A_DAY_PERIODS, B_DAY_PERIODS,
    ADVISORY_START, advisory, advisorydays, advisorylength, freetimedaus, USE_24_HOUR
)
from input_handler import InputHandler
from games_config import GAMES, get_game_command

class Menu:
    def __init__(self, display, input_handler):
        self.display = display
        self.input_handler = input_handler
        self.current_screen = "main"
        self.selected_index = 0
        self.game_selected_index = 0
        self.running = True
        
        self.main_menu_items = ["Schedule", "Clock", "Settings", "Games", "Exit"]
        self.settings_menu_items = ["A/B Day: Auto", "Back"]
        self.game_menu_items = list(GAMES.keys()) + ["Back"]
    
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
            self.display.show_message("Before School", f"School starts at\n{SCHOOL_START}", (200, 200, 200))
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
    
    def show_games_menu(self):
        self.display.show_menu(self.game_menu_items, self.game_selected_index, "Games")
    
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
            elif selected_item == "Games":
                self.current_screen = "games"
                self.game_selected_index = 0
                self.show_games_menu()
    
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
            if self.settings_menu_items[self.selected_index] == "Back":
                self.current_screen = "main"
                self.selected_index = 0
                self.show_main_menu()
        elif action == 'left' or action == 'key1':
            self.current_screen = "main"
            self.selected_index = 0
            self.show_main_menu()
    
    def handle_game_input(self, action):
        if action == 'up':
            self.game_selected_index = (self.game_selected_index - 1) % len(self.game_menu_items)
            self.show_games_menu()
        elif action == 'down':
            self.game_selected_index = (self.game_selected_index + 1) % len(self.game_menu_items)
            self.show_games_menu()
        elif action == 'select' or action == 'right':
            selected_item = self.game_menu_items[self.game_selected_index]
            if selected_item == "Back":
                self.current_screen = "main"
                self.selected_index = 0
                self.show_main_menu()
            else:
                self.launch_game(selected_item)
        elif action == 'left' or action == 'key1':
            self.current_screen = "main"
            self.selected_index = 0
            self.show_main_menu()
    
    def launch_game(self, game_name):
        try:
            command = get_game_command(game_name)
        except Exception as exc:
            self.display.show_message("Error", str(exc), (255, 100, 100))
            time.sleep(2)
            self.show_games_menu()
            return

        self.display.show_message("Launching", f"Starting {game_name}", (100, 255, 100))
        try:
            self.input_handler.cleanup()
        except Exception:
            pass

        try:
            subprocess.run(command, check=False)
        except FileNotFoundError:
            self.display.show_message("Error", "RetroArch is not installed", (255, 100, 100))
            time.sleep(2)
        finally:
            try:
                self.input_handler = InputHandler()
            except Exception as exc:
                self.display.show_message("Error", f"Input handler failed: {exc}", (255, 100, 100))
                time.sleep(2)

        self.current_screen = "games"
        self.game_selected_index = 0
        self.show_games_menu()
    
    def run(self):
        import time
        
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
                elif self.current_screen == "games":
                    self.handle_game_input(action)
            
            current_time = time.time()
            if current_time - last_update > 1.0:
                if self.current_screen == "schedule":
                    self.show_schedule_screen()
                elif self.current_screen == "clock":
                    self.show_clock_screen()
                last_update = current_time
            
            time.sleep(0.05)
        
        self.input_handler.cleanup()
