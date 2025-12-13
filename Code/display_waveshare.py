import os
import sys
import importlib.util
from PIL import Image, ImageDraw, ImageFont
import time


def _load_lcd_driver():
    base_dir = os.path.dirname(__file__)
    legacy_dir = os.path.join(base_dir, "old code")

    candidates = []
    if os.path.isdir(legacy_dir):
        candidates.append(
            (
                os.path.join(legacy_dir, "config.py"),
                os.path.join(legacy_dir, "LCD_1in44.py"),
                None,
            )
        )

    spec_pkg = importlib.util.find_spec("LCD_1in44")
    if spec_pkg and spec_pkg.origin:
        driver_dir = os.path.dirname(spec_pkg.origin)
        candidates.append((os.path.join(driver_dir, "config.py"), spec_pkg.origin, spec_pkg))

    load_errors = []
    for cfg_path, lcd_path, spec in candidates:
        if not (os.path.exists(cfg_path) and os.path.exists(lcd_path)):
            continue

        orig_config = sys.modules.get("config")
        try:
            spec_cfg = importlib.util.spec_from_file_location("_lcd_hat_config", cfg_path)
            lcd_hat_config = importlib.util.module_from_spec(spec_cfg)
            spec_cfg.loader.exec_module(lcd_hat_config)
            sys.modules["config"] = lcd_hat_config

            spec_lcd = spec or importlib.util.spec_from_file_location("LCD_1in44", lcd_path)
            if spec_lcd is None or spec_lcd.loader is None:
                load_errors.append(f"Missing loader for {lcd_path}")
                continue
            lcd_module = importlib.util.module_from_spec(spec_lcd)
            sys.modules["LCD_1in44"] = lcd_module
            spec_lcd.loader.exec_module(lcd_module)
            return lcd_module
        except Exception as exc:
            load_errors.append(f"{lcd_path}: {exc}")
        finally:
            if orig_config is not None:
                sys.modules["config"] = orig_config
            else:
                sys.modules.pop("config", None)

    error_detail = "; ".join(load_errors) if load_errors else "driver files not found"
    raise FileNotFoundError(
        "Could not load Waveshare LCD driver (LCD_1in44). "
        "Re-run install.sh to reinstall the driver or restore the legacy 'old code' folder. "
        f"Details: {error_detail}"
    )


LCD_1in44 = _load_lcd_driver()

class WaveshareDisplay:
    def __init__(self, theme_manager=None):
        # Initialize the Waveshare LCD
        self.disp = LCD_1in44.LCD()
        scan_dir = LCD_1in44.SCAN_DIR_DFT
        self.disp.LCD_Init(scan_dir)
        self.disp.LCD_Clear()

        self.width = self.disp.width
        self.height = self.disp.height
        
        # Store theme manager reference
        self.theme_manager = theme_manager

        self.image = Image.new('RGB', (self.width, self.height), color=(0, 0, 0))
        self.draw = ImageDraw.Draw(self.image)

        try:
            self.font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
            self.font_medium = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
            self.font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
            self.font_tiny = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 10)
        except:
            self.font_large = ImageFont.load_default()
            self.font_medium = ImageFont.load_default()
            self.font_small = ImageFont.load_default()
            self.font_tiny = ImageFont.load_default()

    def _render(self):
        """Push the PIL image to the LCD."""
        self.disp.LCD_ShowImage(self.image, 0, 0)

    def clear(self, color=(0, 0, 0)):
        self.draw.rectangle((0, 0, self.width, self.height), fill=color)

    def _render_sidebar(self, nav_items, selected_index):
        """Overlay the right vertical sidebar on top of current content."""
        if not nav_items:
            return
        secondary = self._get_text_secondary_color()
        accent_sel = (255, 255, 0)
        gutter = 40
        nav_x = self.width - gutter
        nav_y = 4
        # Draw vertical labels rotated 90 degrees, aligned to right gutter
        for i, item in enumerate(nav_items):
            y = nav_y + i * 40  # more spacing for rotated text
            # Create a small image for text, rotate -90 degrees
            tmp = Image.new('RGBA', (100, 20), (0, 0, 0, 0))
            dtmp = ImageDraw.Draw(tmp)
            color = accent_sel if i == selected_index else secondary
            dtmp.text((0, 0), item, font=self.font_tiny, fill=color)
            rot = tmp.rotate(90, expand=True)
            self.image.paste(rot, (nav_x, y), rot)
            if i == selected_index:
                # simple highlight bar next to text
                self.draw.rectangle((nav_x - 4, y, nav_x - 2, y + rot.size[1]), outline=accent_sel)

    def show_schedule(self, period, period_name, time_remaining, lunch_time, end_time, current_time_str, nav_items=None, selected_index=0):
        self.clear(self._get_bg_color())
        
        y_offset = 2
        self.draw.text((2, y_offset), current_time_str, font=self.font_medium, fill=self._get_accent_color())
        y_offset += 18

        if period == "LUNCH":
            self.draw.text((2, y_offset), "LUNCH", font=self.font_large, fill=(255, 200, 0))
        elif period == "ADVISORY":
            self.draw.text((2, y_offset), "ADVISORY", font=self.font_large, fill=(0, 255, 150))
        elif period == "FREETIME":
            self.draw.text((2, y_offset), "FREE TIME", font=self.font_medium, fill=(150, 255, 150))
        elif period is not None:
            self.draw.text((2, y_offset), f"Period {period}", font=self.font_large, fill=self._get_text_primary_color())
            y_offset += 20
            self.draw.text((2, y_offset), period_name, font=self.font_small, fill=self._get_text_secondary_color())
        else:
            self.draw.text((2, y_offset), "Passing", font=self.font_large, fill=self._get_text_secondary_color())

        y_offset += 25

        if time_remaining:
            self.draw.text((2, y_offset), f"Left: {time_remaining}", font=self.font_small, fill=(100, 255, 100))
            y_offset += 16

        if lunch_time:
            self.draw.text((2, y_offset), f"Lunch: {lunch_time}", font=self.font_small, fill=(255, 200, 100))
            y_offset += 16

        if end_time:
            self.draw.text((2, y_offset), f"Ends: {end_time}", font=self.font_small, fill=(255, 100, 100))

        # Sidebar overlay
        self._render_sidebar(nav_items or [], selected_index)
        self._render()

    def show_menu(self, menu_items, selected_index, title="Menu", progress_label="", progress_value=0, nav_items=None, nav_selected_index=0, start_index=0, max_visible=6):
        self.clear(self._get_bg_color())
        
        # Get colors from theme
        title_color = self._get_accent_color()
        selected_color = (255, 255, 0)  # Yellow highlight for selection
        unselected_color = self._get_text_secondary_color()
        
        y_offset = 2
        self.draw.text((2, y_offset), title, font=self.font_large, fill=title_color)
        y_offset += 22

        visible_items = menu_items[start_index:start_index + max_visible]
        for i, item in enumerate(visible_items):
            absolute_index = start_index + i
            if absolute_index == selected_index:
                self.draw.rectangle((1, y_offset - 1, self.width - 1, y_offset + 15), outline=selected_color, width=1)
                self.draw.text((4, y_offset), f"> {item}", font=self.font_small, fill=selected_color)
            else:
                self.draw.text((4, y_offset), f"  {item}", font=self.font_small, fill=unselected_color)
            y_offset += 18

        # Scroll indicators
        if start_index > 0:
            self.draw.text((self.width - 50, 22), "↑", font=self.font_small, fill=unselected_color)
        if start_index + max_visible < len(menu_items):
            self.draw.text((self.width - 50, y_offset - 2), "↓", font=self.font_small, fill=unselected_color)

        # Draw progress bar at the bottom if progress_label is provided
        if progress_label:
            # Progress bar background
            bar_y = self.height - 12
            bar_x_start = 2
            bar_width = self.width - 4
            bar_height = 10
            
            # Draw bar background
            self.draw.rectangle((bar_x_start, bar_y, bar_x_start + bar_width, bar_y + bar_height), 
                               fill=(50, 50, 50), outline=(100, 100, 100))
            
            # Draw filled portion based on progress
            if progress_value > 0:
                fill_width = int((progress_value / 100.0) * bar_width)
                self.draw.rectangle((bar_x_start, bar_y, bar_x_start + fill_width, bar_y + bar_height), 
                                   fill=self._get_accent_color())
            
            # Draw progress text
            text_color = self._get_text_secondary_color()
            self.draw.text((bar_x_start + 2, bar_y + 0), progress_label, font=self.font_tiny, fill=text_color)

        # Sidebar overlay
        self._render_sidebar(nav_items or [], nav_selected_index)
        self._render()

    def show_message(self, title, message, color=(255, 255, 255), nav_items=None, nav_selected_index=0):
        self.clear(self._get_bg_color())

        self.draw.text((2, 20), title, font=self.font_large, fill=color if color else self._get_accent_color())

        y_offset = 40
        for line in message.split("\n"):
            self.draw.text((2, y_offset), line, font=self.font_tiny, fill=self._get_text_secondary_color())
            y_offset += 14

        # Sidebar overlay
        self._render_sidebar(nav_items or [], nav_selected_index)
        self._render()

    def show_clock(self, time_str, date_str, nav_items=None, nav_selected_index=0):
        self.clear(self._get_bg_color())

        self.draw.text((5, 45), time_str, font=self.font_medium, fill=self._get_accent_color())
        self.draw.text((5, 70), date_str, font=self.font_tiny, fill=self._get_text_secondary_color())

        # Sidebar overlay
        self._render_sidebar(nav_items or [], nav_selected_index)
        self._render()
    
    def show_main_page(self, progress_label, progress_value, time_str, date_str, schedule_summary, wifi_connected, nav_items, selected_index, bubble_text=""):
        """Render the main page per sketch: top progress, center art+speech bubble, right vertical nav, bottom wifi indicator and clock."""
        self.clear(self._get_bg_color())

        # Top bar: progress label and bar
        title_color = self._get_text_primary_color()
        accent = self._get_accent_color()
        secondary = self._get_text_secondary_color()

        # Progress bar spans full width until the right sidebar gutter
        bar_y = 18
        bar_x_start = 4
        bar_width = self.width - 8 - 40  # leave room for right nav gutter
        bar_height = 10
        self.draw.rectangle((bar_x_start, bar_y, bar_x_start + bar_width, bar_y + bar_height), fill=(50, 50, 50), outline=(100, 100, 100))
        if progress_value > 0:
            fill_width = int((progress_value / 100.0) * bar_width)
            self.draw.rectangle((bar_x_start, bar_y, bar_x_start + fill_width, bar_y + bar_height), fill=accent)
        self.draw.text((bar_x_start + 2, bar_y - 12), progress_label, font=self.font_tiny, fill=secondary)

        # Sidebar (drawn after main content as overlay)
        nav_x = self.width - 40
        nav_y = 4

        # Center: character placeholder and speech bubble
        center_x0 = 6
        center_y0 = 34
        center_w = nav_x - 12
        center_h = self.height - 56
        self.draw.rectangle((center_x0, center_y0 + 24, center_x0 + int(center_w * 0.45), center_y0 + 24 + int(center_h * 0.5)), outline=secondary)
        # speech bubble as rounded rectangle
        bubble_x0 = center_x0 + int(center_w * 0.5)
        bubble_y0 = center_y0
        bubble_w = int(center_w * 0.45)
        bubble_h = int(center_h * 0.35)
        self.draw.rectangle((bubble_x0, bubble_y0, bubble_x0 + bubble_w, bubble_y0 + bubble_h), outline=accent)
        if bubble_text:
            self.draw.text((bubble_x0 + 4, bubble_y0 + 4), bubble_text, font=self.font_tiny, fill=secondary)

        # Schedule summary under bubble
        if schedule_summary:
            self.draw.text((center_x0, center_y0 + center_h - 12), schedule_summary, font=self.font_tiny, fill=secondary)

        # Bottom: clock and Wi-Fi indicator
        clock_y = self.height - 18
        self.draw.text((6, clock_y), time_str, font=self.font_tiny, fill=accent)
        self.draw.text((6, clock_y + 10), date_str, font=self.font_tiny, fill=secondary)
        wifi_color = (100, 255, 100) if wifi_connected else (255, 100, 100)
        wifi_text = "WiFi" if wifi_connected else "No WiFi"
        self.draw.text((self.width - 46, self.height - 18), wifi_text, font=self.font_tiny, fill=wifi_color)

        # Sidebar overlay
        self._render_sidebar(nav_items or [], selected_index)
        self._render()
    
    # Theme color helper methods
    def _get_bg_color(self):
        """Get background color from theme"""
        if self.theme_manager:
            return self.theme_manager.get_background()
        return (0, 0, 0)
    
    def _get_text_primary_color(self):
        """Get primary text color from theme"""
        if self.theme_manager:
            return self.theme_manager.get_text_primary()
        return (255, 255, 255)
    
    def _get_text_secondary_color(self):
        """Get secondary text color from theme"""
        if self.theme_manager:
            return self.theme_manager.get_text_secondary()
        return (200, 200, 200)
    
    def _get_accent_color(self):
        """Get accent color from theme"""
        if self.theme_manager:
            return self.theme_manager.get_text_accent()
        return (100, 200, 255)
