"""
Configuration Portal Client for Timagotchi
Handles pairing code generation, display, and configuration download
"""

import requests
import time
import json
import os
from datetime import datetime

# Backend API URL - change this to your deployed URL
API_BASE_URL = os.environ.get('TIMAGOTCHI_API_URL', 'https://timagotchi-config.herokuapp.com')

class ConfigPortal:
    def __init__(self, display, input_handler):
        self.display = display
        self.input_handler = input_handler
        self.code = None
        self.polling = False
        
    def request_pairing_code(self):
        """Request a new pairing code from the backend"""
        try:
            response = requests.post(f"{API_BASE_URL}/api/generate-code", timeout=10)
            response.raise_for_status()
            data = response.json()
            self.code = data['code']
            return self.code
        except Exception as e:
            print(f"Error requesting pairing code: {e}")
            return None
    
    def display_pairing_screen(self):
        """Display the pairing code on screen"""
        if not self.code:
            self.code = self.request_pairing_code()
            
        if not self.code:
            # Failed to get code - show error
            self.display.clear((0, 0, 0))
            self.display.draw.text((10, 40), "Connection Error", 
                                 font=self.display.font_medium, 
                                 fill=(255, 100, 100))
            self.display.draw.text((10, 60), "Check internet", 
                                 font=self.display.font_small, 
                                 fill=(200, 200, 200))
            self.display.draw.text((10, 80), "Run configure_", 
                                 font=self.display.font_small, 
                                 fill=(200, 200, 200))
            self.display.draw.text((10, 95), "schedule.py", 
                                 font=self.display.font_small, 
                                 fill=(200, 200, 200))
            self.display._render()
            return False
        
        # Display code
        self.display.clear((0, 0, 0))
        
        # Title
        self.display.draw.text((10, 10), "Configuration", 
                             font=self.display.font_medium, 
                             fill=(100, 150, 255))
        self.display.draw.text((10, 30), "Portal", 
                             font=self.display.font_medium, 
                             fill=(100, 150, 255))
        
        # Instructions
        self.display.draw.text((10, 55), "Visit:", 
                             font=self.display.font_small, 
                             fill=(200, 200, 200))
        
        # Parse URL to show domain only
        domain = API_BASE_URL.replace('https://', '').replace('http://', '').split('/')[0]
        # Truncate if too long
        if len(domain) > 20:
            domain = domain[:17] + "..."
        
        self.display.draw.text((10, 70), domain, 
                             font=self.display.font_small, 
                             fill=(255, 255, 255))
        
        # Code display
        self.display.draw.rectangle((5, 88, 123, 108), fill=(30, 30, 50))
        self.display.draw.text((64, 98), self.code, 
                             font=self.display.font_large, 
                             fill=(100, 255, 100),
                             anchor="mm")
        
        # Status
        self.display.draw.text((10, 115), "Waiting...", 
                             font=self.display.font_small, 
                             fill=(150, 150, 150))
        
        self.display._render()
        return True
    
    def poll_for_config(self, timeout=300):
        """
        Poll the backend for configuration
        Returns config dict if successful, None if timeout/error
        """
        if not self.code:
            return None
        
        start_time = time.time()
        self.polling = True
        dots = 0
        
        while self.polling and (time.time() - start_time < timeout):
            try:
                response = requests.get(f"{API_BASE_URL}/api/config/{self.code}", timeout=5)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('status') == 'ready':
                        self.polling = False
                        return data.get('config')
                elif response.status_code == 404:
                    # Code expired or invalid
                    self.polling = False
                    return None
                
            except Exception as e:
                print(f"Poll error: {e}")
            
            # Update waiting animation
            dots = (dots + 1) % 4
            status_text = "Waiting" + "." * dots + " " * (3 - dots)
            
            self.display.draw.rectangle((10, 115, 118, 125), fill=(0, 0, 0))
            self.display.draw.text((10, 115), status_text, 
                                 font=self.display.font_small, 
                                 fill=(150, 150, 150))
            self.display._render()
            
            # Check for manual cancel (any button press)
            action = self.input_handler.get_input()
            if action:
                self.polling = False
                return None
            
            # Poll every 3 seconds
            time.sleep(3)
        
        self.polling = False
        return None
    
    def write_config_files(self, config):
        """
        Write configuration to appropriate files
        Returns True if successful, False otherwise
        """
        try:
            code_dir = os.path.dirname(__file__)
            
            # Write config.py
            config_py_path = os.path.join(code_dir, 'config.py')
            self._write_config_py(config_py_path, config)
            
            # Write canvas_config.json if Canvas is enabled
            if config.get('canvas') and config['canvas'].get('enabled'):
                canvas_path = os.path.join(code_dir, 'canvas_config.json')
                canvas_config = {
                    'base_url': config['canvas']['base_url'],
                    'api_token': config['canvas']['api_token']
                }
                with open(canvas_path, 'w') as f:
                    json.dump(canvas_config, f, indent=2)
            
            # Update themes.json with selected theme
            themes_path = os.path.join(code_dir, 'themes.json')
            if os.path.exists(themes_path):
                with open(themes_path, 'r') as f:
                    themes = json.load(f)
                themes['current_theme'] = config['customization']['theme']
                with open(themes_path, 'w') as f:
                    json.dump(themes, f, indent=2)
            
            # Update Phrases.json if custom phrases provided
            if config['customization'].get('phrases'):
                phrases_path = os.path.join(code_dir, 'Phrases.json')
                phrases = {}
                if os.path.exists(phrases_path):
                    with open(phrases_path, 'r') as f:
                        phrases = json.load(f)
                
                # Update specific phrase categories
                if config['customization']['phrases'].get('passing'):
                    phrases['passing'] = config['customization']['phrases']['passing']
                if config['customization']['phrases'].get('lunch'):
                    phrases['lunch'] = config['customization']['phrases']['lunch']
                
                with open(phrases_path, 'w') as f:
                    json.dump(phrases, f, indent=2)
            
            return True
            
        except Exception as e:
            print(f"Error writing config files: {e}")
            return False
    
    def _write_config_py(self, path, config):
        """Generate and write config.py file"""
        schedule = config['schedule']
        system = config['system']
        
        # Calculate period times
        periods = self._calculate_periods(schedule)
        
        lines = [
            "# Timagotchi Schedule Configuration",
            f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "# School Hours",
            f'SCHOOL_START = "{schedule["school_start"]}"',
            f'SCHOOL_END = "{schedule["school_end"]}"',
            f'USE_24_HOUR = {system["use_24_hour"]}',
            "",
            "# Period Timing",
            f"PERIOD_LENGTH = {schedule['period_length']}",
            f"PASSING_TIME = {schedule['passing_time']}",
            "",
            "# Period Start Times",
            f"PERIODS = {periods}",
            ""
        ]
        
        # Advisory configuration
        if schedule.get('has_advisory'):
            lines.extend([
                "# Advisory Period",
                f'advisory = "true"',
                f'ADVISORY_START = "{schedule.get("advisory_start", "09:20")}"',
                f'ADVISORY_PERIOD = 0',
                f'advisorylength = "{schedule.get("advisory_length", 36)}"',
                f'advisorydays = "{schedule.get("advisory_days", "m,t")}"',
                f'freetimedaus = "w,th,f"',
                ""
            ])
        else:
            lines.extend([
                'advisory = "false"',
                'ADVISORY_PERIOD = 0',
                'advisorylength = "0"',
                'advisorydays = ""',
                ""
            ])
        
        # Lunch configuration
        if schedule.get('has_lunch'):
            lines.extend([
                "# Lunch Period",
                f'LUNCH_START = "{schedule.get("lunch_start", "12:00")}"',
                f'LUNCH_END = "{schedule.get("lunch_end", "12:30")}"',
                ""
            ])
        else:
            lines.extend([
                'LUNCH_START = ""',
                'LUNCH_END = ""',
                ""
            ])
        
        # A/B Day configuration
        if schedule.get('use_ab_day'):
            lines.extend([
                "# A/B Day Scheduling",
                f'abday = "true"',
                f'AB_DAY_MODE = "{schedule.get("ab_day_mode", "auto")}"',
                'MANUAL_AB_DAY = "a"',
                "",
                "# Period Names",
                "A_DAY_PERIODS = {1: 'Period 1', 2: 'Period 2', 3: 'Period 3', 4: 'Period 4', 5: 'Period 5', 6: 'Period 6'}",
                "B_DAY_PERIODS = {1: 'Period 1', 2: 'Period 2', 3: 'Period 3', 4: 'Period 4', 5: 'Period 5', 6: 'Period 6'}",
                ""
            ])
        else:
            lines.extend([
                f'abday = "false"',
                'AB_DAY_MODE = "auto"',
                ""
            ])
        
        # WiFi networks
        wifi_str = '[\n'
        for ssid, password in system.get('wifi_networks', []):
            wifi_str += f'    ("{ssid}", "{password}"),\n'
        wifi_str += ']'
        
        lines.extend([
            "# WiFi Networks",
            f"WIFI_NETWORKS = {wifi_str}",
            ""
        ])
        
        # Time sync
        lines.extend([
            "# Time Synchronization",
            f'TIME_SYNC_MODE = "{system.get("time_sync_mode", "disabled")}"',
            'TIME_SYNC_INTERVAL = 6',
            f'TIMEZONE = "{system.get("timezone", "America/New_York")}"',
            "",
            "# Progress Bar",
            'PROGRESS_BAR_MODE = "time_in_class"',
            ""
        ])
        
        with open(path, 'w') as f:
            f.write('\n'.join(lines))
    
    def _calculate_periods(self, schedule):
        """Calculate period start times based on schedule configuration"""
        periods = {}
        
        # Parse school start time
        start_hour, start_min = map(int, schedule['school_start'].split(':'))
        current_minutes = start_hour * 60 + start_min
        
        # Add advisory if applicable
        if schedule.get('has_advisory'):
            adv_hour, adv_min = map(int, schedule.get('advisory_start', '09:20').split(':'))
            adv_minutes = adv_hour * 60 + adv_min
            current_minutes = adv_minutes + schedule.get('advisory_length', 36) + schedule['passing_time']
        
        # Calculate each period
        for i in range(1, schedule['num_periods'] + 1):
            hour = current_minutes // 60
            minute = current_minutes % 60
            periods[i] = f"{hour:02d}:{minute:02d}"
            current_minutes += schedule['period_length'] + schedule['passing_time']
        
        return periods
    
    def show_success(self):
        """Display success message"""
        self.display.clear((0, 0, 0))
        
        self.display.draw.text((64, 50), "Success!", 
                             font=self.display.font_large, 
                             fill=(100, 255, 100),
                             anchor="mm")
        
        self.display.draw.text((64, 75), "Configuration", 
                             font=self.display.font_small, 
                             fill=(200, 200, 200),
                             anchor="mm")
        
        self.display.draw.text((64, 90), "Saved!", 
                             font=self.display.font_small, 
                             fill=(200, 200, 200),
                             anchor="mm")
        
        self.display.draw.text((64, 110), "Restarting...", 
                             font=self.display.font_small, 
                             fill=(150, 150, 150),
                             anchor="mm")
        
        self.display._render()
        time.sleep(3)
    
    def show_error(self, message="Configuration failed"):
        """Display error message"""
        self.display.clear((0, 0, 0))
        
        self.display.draw.text((64, 60), "Error", 
                             font=self.display.font_large, 
                             fill=(255, 100, 100),
                             anchor="mm")
        
        # Word wrap message
        words = message.split()
        lines = []
        current_line = ""
        
        for word in words:
            test_line = current_line + " " + word if current_line else word
            # Rough character limit for small font
            if len(test_line) <= 18:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        
        if current_line:
            lines.append(current_line)
        
        y = 85
        for line in lines[:2]:  # Max 2 lines
            self.display.draw.text((64, y), line, 
                                 font=self.display.font_small, 
                                 fill=(200, 200, 200),
                                 anchor="mm")
            y += 15
        
        self.display._render()
        time.sleep(5)


def run_configuration_portal(display, input_handler):
    """
    Main entry point for configuration portal
    Returns True if configuration successful, False otherwise
    """
    portal = ConfigPortal(display, input_handler)
    
    # Display pairing screen
    if not portal.display_pairing_screen():
        return False
    
    # Poll for configuration
    config = portal.poll_for_config(timeout=300)  # 5 minute timeout
    
    if not config:
        portal.show_error("Timeout or cancelled")
        return False
    
    # Write configuration files
    if portal.write_config_files(config):
        portal.show_success()
        return True
    else:
        portal.show_error("Failed to save files")
        return False
