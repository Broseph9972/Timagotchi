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
    
    # Sidebar and UI element colors
    def get_sidebar_box(self):
        # Default to menu highlight if not defined
        return self.get_color('sidebar_box', self.get_menu_highlight())
    
    def get_sidebar_box_selected(self):
        # Slightly brighter default based on menu highlight
        mh = self.get_menu_highlight()
        default_sel = (min(mh[0] + 40, 255), min(mh[1] + 40, 255), min(mh[2] + 40, 255))
        return self.get_color('sidebar_box_selected', default_sel)
    
    def get_divider(self):
        # Subtle divider line color
        return self.get_color('divider', (80, 80, 80))
    
    def get_progress_bg(self):
        return self.get_color('progress_bg', (40, 40, 40))
    
    def get_success(self):
        return self.get_color('success', (100, 255, 100))
    
    def get_error(self):
        return self.get_color('error', (255, 100, 100))
    
    def get_warning(self):
        return self.get_color('warning', (255, 200, 100))
    
    def get_sidebar_indicator(self):
        # Color for the selection indicator line in the sidebar
        return self.get_color('sidebar_indicator', (255, 255, 0))
    
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
                "sidebar_box": [220, 220, 220],
                "sidebar_box_selected": [240, 240, 240],
                "divider": [150, 150, 150],
                "progress_bg": [220, 220, 220],
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
                "sidebar_box": [30, 30, 30],
                "sidebar_box_selected": [60, 60, 40],
                "divider": [80, 80, 80],
                "progress_bg": [40, 40, 40],
                "success": [100, 255, 100],
                "error": [255, 100, 100],
                "warning": [255, 200, 100]
            },
            "ocean": {
                "name": "Ocean",
                "background": [5, 35, 60],
                "text_primary": [200, 220, 255],
                "text_secondary": [150, 180, 220],
                "text_accent": [100, 200, 255],
                "menu_highlight": [30, 80, 140],
                "sidebar_box": [20, 50, 90],
                "sidebar_box_selected": [40, 90, 150],
                "divider": [60, 110, 170],
                "progress_bg": [25, 60, 110],
                "success": [100, 255, 150],
                "error": [255, 120, 100],
                "warning": [255, 200, 80]
            },
            "forest": {
                "name": "Forest",
                "background": [20, 45, 20],
                "text_primary": [220, 255, 200],
                "text_secondary": [180, 220, 160],
                "text_accent": [150, 255, 150],
                "menu_highlight": [50, 100, 50],
                "sidebar_box": [30, 70, 30],
                "sidebar_box_selected": [60, 120, 50],
                "divider": [80, 140, 80],
                "progress_bg": [35, 80, 35],
                "success": [150, 255, 100],
                "error": [255, 100, 100],
                "warning": [255, 200, 100]
            },
            "sunset": {
                "name": "Sunset",
                "background": [60, 30, 20],
                "text_primary": [255, 220, 180],
                "text_secondary": [240, 180, 140],
                "text_accent": [255, 180, 100],
                "menu_highlight": [100, 50, 40],
                "sidebar_box": [80, 40, 35],
                "sidebar_box_selected": [120, 70, 50],
                "divider": [140, 80, 60],
                "progress_bg": [90, 45, 35],
                "success": [200, 255, 150],
                "error": [255, 100, 80],
                "warning": [255, 200, 80]
            },
            "cyberpunk": {
                "name": "Cyberpunk",
                "background": [10, 10, 30],
                "text_primary": [0, 255, 255],
                "text_secondary": [100, 255, 200],
                "text_accent": [255, 0, 255],
                "menu_highlight": [0, 100, 100],
                "sidebar_box": [20, 20, 60],
                "sidebar_box_selected": [40, 40, 90],
                "divider": [80, 80, 160],
                "progress_bg": [30, 30, 80],
                "success": [0, 255, 100],
                "error": [255, 0, 100],
                "warning": [255, 200, 0]
            }
        }
