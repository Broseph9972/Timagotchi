# Demonstrates: Multi-level error handling for fonts, icons, and application startup
import os
import sys
import traceback
from PIL import Image, ImageFont
from font_manager import FontManager
def _load_icons(self):
    icons_dir = os.path.join(os.path.dirname(__file__), 'Icons')
    icon_files = {
        'home': 'home.png',
        'icon': 'Icon.png',
        'settings': 'settings.png',
        'grades': 'grades.png',
        'textbox': 'textbox.png',
        'speechbubble': 'speechbubble.png',
        'thoughtbubble': 'Thoughtbubble.png'
    }
    for key, filename in icon_files.items():
        icon_path = os.path.join(icons_dir, filename)
        try:
            if os.path.exists(icon_path):
                img = Image.open(icon_path)
                if img.mode != 'RGBA':
                    img = img.convert('RGBA')
                self.icon_cache[key] = img
        except Exception:
            pass
def _load_fonts(self):
    try:
        regular_path = self.font_manager.get_font_path('regular')
        bold_path = self.font_manager.get_font_path('bold')
        self.font_large = ImageFont.truetype(bold_path, 16)
        self.font_medium = ImageFont.truetype(regular_path, 14)
        self.font_small = ImageFont.truetype(regular_path, 12)
        self.font_tiny = ImageFont.truetype(regular_path, 10)
        self.font_micro = ImageFont.truetype(regular_path, 8)
    except Exception as e:
        print(f"Error loading custom fonts: {e}")
        try:
            bold_ttf = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
            regular_ttf = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
            self.font_large = bold_ttf
            self.font_medium = regular_ttf
            self.font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
            self.font_tiny = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 10)
            self.font_micro = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 8)
        except:
            default_font = ImageFont.load_default()
            self.font_large = default_font
            self.font_medium = default_font
            self.font_small = default_font
            self.font_tiny = default_font
            self.font_micro = default_font
try:
    from display_waveshare import WaveshareDisplay
    from input_handler import InputHandler
    from menu import Menu
    from theme_manager import ThemeManager
    theme_manager = ThemeManager()
    display = WaveshareDisplay(theme_manager)
    input_handler = InputHandler()
    menu = Menu(display, input_handler)
    menu.start_boot_git_maintenance_background()
    try:
        ready_file = '/tmp/timagotchi_ready'
        with open(ready_file, 'w') as f:
            f.write('1')
    except Exception as e:
        print(f"Warning: Could not write ready signal: {e}")
    menu.run()
    display.clear()
except KeyboardInterrupt:
    sys.exit(0)
except Exception as e:
    print(f"Error: {e}")
    traceback.print_exc()
    sys.exit(1)
