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
API_BASE_URL = os.environ.get('TIMAGOTCHI_API_URL', 'https://timagotchi.onrender.com')

class ConfigPortal:
    def __init__(self, display, input_handler):
        self.display = display
        self.input_handler = input_handler
        self.code = None
        self.polling = False
        # Reuse HTTP session to reduce TLS handshakes and CPU spikes
        try:
            self.session = requests.Session()
        except Exception:
            self.session = requests
        
    def request_pairing_code(self):
        """Request a new pairing code from the backend"""
        try:
            # Add startup delay to avoid power spike
            print("Connecting to configuration service...")
            time.sleep(2)
            
            # Use shorter timeout on first attempt to prevent Pi brownout
            response = self.session.post(f"{API_BASE_URL}/api/generate-code", timeout=5)
            response.raise_for_status()
            data = response.json()
            self.code = data['code']
            return self.code
        except requests.exceptions.Timeout:
            print("Request timed out. Check WiFi signal strength.")
            return None
        except requests.exceptions.ConnectionError:
            print("Connection error. WiFi may be unavailable.")
            return None
        except Exception as e:
            print(f"Error requesting pairing code: {e}")
            return None
    
    def display_pairing_screen(self):
        """Display the pairing code on screen"""
        try:
            if not self.code:
                # Show connecting message first
                self.display.clear((0, 0, 0))
                self.display.draw.text((10, 40), "Connecting...", 
                                     font=self.display.font_medium, 
                                     fill=(100, 200, 255))
                self.display.draw.text((10, 65), "Please wait", 
                                     font=self.display.font_small, 
                                     fill=(200, 200, 200))
                self.display.draw.text((10, 85), "(do not power off)", 
                                     font=self.display.font_small, 
                                     fill=(150, 150, 150))
                self.display._render()
                
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
            
        except Exception as e:
            print(f"Display error in pairing screen: {e}")
            import traceback
            traceback.print_exc()
            return False
    
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
        update_count = 0
        
        while self.polling and (time.time() - start_time < timeout):
            try:
                response = self.session.get(f"{API_BASE_URL}/api/config/{self.code}", timeout=3)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('status') == 'ready':
                        self.polling = False
                        return data.get('config')
                elif response.status_code == 404:
                    # Code expired or invalid
                    self.polling = False
                    return None
                
            except requests.exceptions.Timeout:
                print("Request timeout, will retry")
            except requests.exceptions.RequestException as e:
                print(f"Network error: {e}")
            except Exception as e:
                print(f"Poll error: {e}")
            
            # Update waiting animation only every 2 iterations (6 seconds) to reduce display load
            update_count += 1
            if update_count % 2 == 0:
                try:
                    dots = (dots + 1) % 4
                    status_text = "Waiting" + "." * dots + " " * (3 - dots)
                    
                    self.display.draw.rectangle((10, 115, 118, 125), fill=(0, 0, 0))
                    self.display.draw.text((10, 115), status_text, 
                                         font=self.display.font_small, 
                                         fill=(150, 150, 150))
                    self.display._render()
                except Exception as e:
                    print(f"Display error: {e}")
            
            # Check for manual cancel (any button press)
            try:
                action = self.input_handler.get_input()
                if action:
                    self.polling = False
                    return None
            except Exception as e:
                print(f"Input error: {e}")
            
            # Poll every 3 seconds with small yield for system
            time.sleep(2.5)
            time.sleep(0.5)  # Split sleep for better system responsiveness
        
        self.polling = False
        return None
    
    def write_config_files(self, config):
        """
        Write configuration to config.json (unified config file)
        Returns True if successful, False otherwise
        """
        try:
            code_dir = os.path.dirname(__file__)
            
            # Build config.json structure
            config_json = self._build_config_json(config)
            
            # Write config.json
            config_path = os.path.join(code_dir, 'config.json')
            with open(config_path, 'w') as f:
                json.dump(config_json, f, indent=2)
            
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
                    try:
                        with open(phrases_path, 'r') as f:
                            phrases = json.load(f)
                    except json.JSONDecodeError:
                        print("Warning: Could not read existing Phrases.json, creating new")
                        phrases = {}
                
                # Update specific phrase categories
                if config['customization']['phrases'].get('passing'):
                    phrases['passing'] = config['customization']['phrases']['passing']
                if config['customization']['phrases'].get('lunch'):
                    phrases['lunch'] = config['customization']['phrases']['lunch']
                
                # Handle per-period phrases
                if config['customization']['phrases'].get('periods'):
                    period_phrases = config['customization']['phrases']['periods']
                    for period_key, phrase_list in period_phrases.items():
                        if phrase_list:  # Only add if not empty
                            phrases[period_key] = phrase_list
                
                with open(phrases_path, 'w') as f:
                    json.dump(phrases, f, indent=2)
            
            return True
            
        except Exception as e:
            print(f"Error writing config files: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _build_config_json(self, config):
        """Build the unified config.json structure"""
        schedule = config['schedule']
        system = config['system']
        customization = config.get('customization', {})
        canvas = config.get('canvas', {})
        
        # Calculate period times
        periods = self._calculate_periods(schedule)
        
        # Get period names
        period_names = schedule.get('period_names', [])
        num_periods = schedule.get('num_periods', 6)
        
        if not period_names or len(period_names) < num_periods:
            period_names = [f'Period {i}' for i in range(1, num_periods + 1)]
        
        # Build period name dictionaries
        a_day_dict = {str(i+1): name for i, name in enumerate(period_names[:num_periods])}
        b_day_dict = {str(i+1): name for i, name in enumerate(period_names[:num_periods])}
        
        # Handle different schedule patterns
        daily_pattern = schedule.get('daily_pattern', 'same')
        if daily_pattern == 'alternating' and len(period_names) >= num_periods * 2:
            a_day_dict = {str(i+1): period_names[i] for i in range(num_periods)}
            b_day_dict = {str(i+1): period_names[i+num_periods] for i in range(num_periods)}
        
        # Convert period times to string keys
        periods_dict = {str(k): v for k, v in periods.items()}
        
        config_json = {
            "school": {
                "start": schedule["school_start"],
                "end": schedule["school_end"],
                "timezone": system.get("timezone", "America/New_York")
            },
            "schedule": {
                "periods": num_periods,
                "period_length": schedule['period_length'],
                "passing_time": schedule['passing_time'],
                "period_times": periods_dict,
                "period_names_a": a_day_dict,
                "period_names_b": b_day_dict,
                "ab_day": {
                    "enabled": schedule.get('use_ab_day', False),
                    "mode": schedule.get('ab_day_mode', 'auto')
                },
                "advisory": {
                    "enabled": schedule.get('has_advisory', False),
                    "start": schedule.get('advisory_start', '09:20'),
                    "length": schedule.get('advisory_length', 36),
                    "days": schedule.get('advisory_days', '')
                },
                "lunch": {
                    "enabled": schedule.get('has_lunch', False),
                    "start": schedule.get('lunch_start', ''),
                    "end": schedule.get('lunch_end', '')
                }
            },
            "display": {
                "time_format": "24h" if system.get("use_24_hour", False) else "12h",
                "progress_bar_mode": customization.get("progress_bar_mode", "time_in_class"),
                "theme": customization.get("theme", "dark")
            },
            "system": {
                "time_sync": system.get("time_sync_mode", "disabled"),
                "time_sync_interval": 6,
                "wifi_networks": system.get("wifi_networks", [])
            },
            "canvas": {
                "enabled": canvas.get('enabled', False),
                "base_url": canvas.get('base_url', ''),
                "api_token": canvas.get('api_token', '')
            }
        }
        
        return config_json
    
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
    original_bl = None
    portal = None
    try:
        # Dim backlight to reduce power while portal runs
        try:
            if hasattr(display, "get_backlight"):
                original_bl = display.get_backlight()
            if hasattr(display, "dim_for_portal"):
                display.dim_for_portal()
        except Exception:
            original_bl = None

        portal = ConfigPortal(display, input_handler)
        
        # Display pairing screen
        if not portal.display_pairing_screen():
            return False
        
        # Poll for configuration with reduced timeout (3 minutes instead of 5)
        config = portal.poll_for_config(timeout=180)
        
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
            
    except KeyboardInterrupt:
        print("\nConfiguration cancelled by user")
        return False
    except Exception as e:
        print(f"Configuration portal error: {e}")
        try:
            if portal is not None:
                portal.show_error(f"Error: {str(e)[:30]}")
        except:
            pass
        return False
    finally:
        # Restore backlight to original level if we dimmed it
        try:
            if original_bl is not None and hasattr(display, "set_backlight"):
                display.set_backlight(original_bl)
        except Exception:
            pass
