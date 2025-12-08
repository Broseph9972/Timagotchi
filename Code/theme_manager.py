import json
import os

class ThemeManager:
    def __init__(self, themes_file='themes.json'):
        self.themes_file = themes_file
        self.themes = {}
        self.current_theme_name = "dark"
        self.current_theme = {}
        self.load_themes()
    
    def load_themes(self):
        """Load themes from JSON file"""
        try:
            if os.path.exists(self.themes_file):
                with open(self.themes_file, 'r') as f:
                    data = json.load(f)
                    self.themes = data.get('themes', {})
                    self.current_theme_name = data.get('current_theme', 'dark')
            else:
                # Create default themes if file doesn't exist
                self.themes = self._get_default_themes()
                self.current_theme_name = 'dark'
                self.save_themes()
            
            # Set current theme
            if self.current_theme_name in self.themes:
                self.current_theme = self.themes[self.current_theme_name]
            else:
                self.current_theme = self.themes.get('dark', {})
                self.current_theme_name = 'dark'
        except Exception as e:
            print(f"Error loading themes: {e}")
            self.themes = self._get_default_themes()
            self.current_theme = self.themes['dark']
            self.current_theme_name = 'dark'
    
    def save_themes(self):
        """Save current theme selection to JSON file"""
        try:
            data = {
                'themes': self.themes,
                'current_theme': self.current_theme_name
            }
            with open(self.themes_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving themes: {e}")
    
    def set_theme(self, theme_name):
        """Set the current theme"""
        if theme_name in self.themes:
            self.current_theme_name = theme_name
            self.current_theme = self.themes[theme_name]
            self.save_themes()
            return True
        return False
    
    def get_theme_names(self):
        """Get list of available theme names"""
        return list(self.themes.keys())
    
    def get_color(self, color_key, default=(255, 255, 255)):
        """Get a color from current theme"""
        return tuple(self.current_theme.get(color_key, default))
    
    def get_background(self):
        return self.get_color('background', (0, 0, 0))
    
    def get_text_primary(self):
        return self.get_color('text_primary', (255, 255, 255))
    
    def get_text_secondary(self):
        return self.get_color('text_secondary', (200, 200, 200))
    
    def get_text_accent(self):
        return self.get_color('text_accent', (100, 150, 255))
    
    def get_menu_highlight(self):
        return self.get_color('menu_highlight', (100, 100, 100))
    
    def get_success(self):
        return self.get_color('success', (100, 255, 100))
    
    def get_error(self):
        return self.get_color('error', (255, 100, 100))
    
    def get_warning(self):
        return self.get_color('warning', (255, 200, 100))
    
    def _get_default_themes(self):
        """Return default themes"""
        return {
            "light": {
                "name": "Light",
                "background": [255, 255, 255],
                "text_primary": [0, 0, 0],
                "text_secondary": [80, 80, 80],
                "text_accent": [100, 150, 255],
                "menu_highlight": [200, 200, 200],
                "success": [100, 255, 100],
                "error": [255, 100, 100],
                "warning": [255, 200, 100]
            },
            "dark": {
                "name": "Dark",
                "background": [20, 20, 20],
                "text_primary": [255, 255, 255],
                "text_secondary": [180, 180, 180],
                "text_accent": [100, 200, 255],
                "menu_highlight": [60, 60, 60],
                "success": [100, 255, 100],
                "error": [255, 100, 100],
                "warning": [255, 200, 100]
            }
        }
