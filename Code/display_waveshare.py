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

    # Layout constants
    SIDEBAR_WIDTH = 18  # narrow gutter for rotated text
    PROGRESS_BAR_HEIGHT = 8

    def _render_sidebar(self, nav_items, selected_index):
        """Draw the right-side vertical navigation with 90° rotated labels."""
        if not nav_items:
            return
        secondary = self._get_text_secondary_color()
        accent_sel = (255, 255, 0)
        bg = self._get_bg_color()
        
        # Clear sidebar area
        sidebar_x = self.width - self.SIDEBAR_WIDTH
        self.draw.rectangle((sidebar_x, 0, self.width, self.height), fill=bg)
        
        # Distribute items evenly along sidebar height
        item_height = self.height // len(nav_items)
        
        for i, item in enumerate(nav_items):
            y_center = i * item_height + item_height // 2
            color = accent_sel if i == selected_index else secondary
            
            # Create temp image for rotated text
            tmp = Image.new('RGBA', (80, 14), (0, 0, 0, 0))
            dtmp = ImageDraw.Draw(tmp)
            dtmp.text((0, 0), item, font=self.font_tiny, fill=color)
            # Crop to actual text size
            bbox = tmp.getbbox()
            if bbox:
                tmp = tmp.crop(bbox)
            rot = tmp.rotate(90, expand=True)
            
            # Center rotated text vertically in its slot
            paste_x = sidebar_x + (self.SIDEBAR_WIDTH - rot.width) // 2
            paste_y = y_center - rot.height // 2
            self.image.paste(rot, (paste_x, max(0, paste_y)), rot)
            
            # Selection indicator: small bar to the left
            if i == selected_index:
                bar_x = sidebar_x - 2
                self.draw.line((bar_x, i * item_height + 4, bar_x, (i + 1) * item_height - 4), fill=accent_sel, width=2)

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

    def show_menu(self, menu_items, selected_index, title="Menu", progress_label="", progress_value=0, nav_items=None, nav_selected_index=0, start_index=0, max_visible=5):
        self.clear(self._get_bg_color())
        
        # Get colors from theme
        title_color = self._get_accent_color()
        selected_color = (255, 255, 0)
        unselected_color = self._get_text_secondary_color()
        
        # Content area (left of sidebar)
        content_width = self.width - self.SIDEBAR_WIDTH - 4
        
        y_offset = 4
        self.draw.text((4, y_offset), title, font=self.font_medium, fill=title_color)
        y_offset += 18

        visible_items = menu_items[start_index:start_index + max_visible]
        for i, item in enumerate(visible_items):
            absolute_index = start_index + i
            # Truncate item if too long
            display_item = item[:14] if len(item) > 14 else item
            if absolute_index == selected_index:
                self.draw.rectangle((2, y_offset - 1, content_width, y_offset + 13), outline=selected_color, width=1)
                self.draw.text((6, y_offset), f">{display_item}", font=self.font_small, fill=selected_color)
            else:
                self.draw.text((6, y_offset), f" {display_item}", font=self.font_small, fill=unselected_color)
            y_offset += 16

        # Scroll indicators (only when needed)
        if start_index > 0:
            self.draw.text((content_width - 10, 18), "^", font=self.font_tiny, fill=unselected_color)
        if start_index + max_visible < len(menu_items):
            self.draw.text((content_width - 10, y_offset - 4), "v", font=self.font_tiny, fill=unselected_color)

        # Sidebar
        self._render_sidebar(nav_items or [], nav_selected_index)
        self._render()

    def show_message(self, title, message, color=(255, 255, 255), nav_items=None, nav_selected_index=0):
        self.clear(self._get_bg_color())
        
        content_width = self.width - self.SIDEBAR_WIDTH - 4

        self.draw.text((4, 8), title, font=self.font_medium, fill=color if color else self._get_accent_color())

        y_offset = 28
        for line in message.split("\n"):
            # Truncate long lines
            display_line = line[:18] if len(line) > 18 else line
            self.draw.text((4, y_offset), display_line, font=self.font_tiny, fill=self._get_text_secondary_color())
            y_offset += 12

        # Sidebar
        self._render_sidebar(nav_items or [], nav_selected_index)
        self._render()

    def show_clock(self, time_str, date_str, nav_items=None, nav_selected_index=0):
        self.clear(self._get_bg_color())
        
        content_width = self.width - self.SIDEBAR_WIDTH - 4

        # Center clock in content area
        self.draw.text((10, 40), time_str, font=self.font_large, fill=self._get_accent_color())
        self.draw.text((10, 65), date_str, font=self.font_small, fill=self._get_text_secondary_color())

        # Sidebar
        self._render_sidebar(nav_items or [], nav_selected_index)
        self._render()
    
    def show_main_page(self, progress_label, progress_value, time_str, date_str, schedule_summary, wifi_connected, nav_items, selected_index, bubble_text=""):
        """Render the main page per sketch: progress bar at very top spanning to sidebar, center character+speech bubble, right sidebar, bottom clock and wifi."""
        self.clear(self._get_bg_color())

        accent = self._get_accent_color()
        secondary = self._get_text_secondary_color()
        primary = self._get_text_primary_color()
        
        content_width = self.width - self.SIDEBAR_WIDTH

        # === TOP: Progress bar from corner to sidebar ===
        bar_x = 0
        bar_y = 0
        bar_w = content_width
        bar_h = self.PROGRESS_BAR_HEIGHT
        # Background
        self.draw.rectangle((bar_x, bar_y, bar_x + bar_w, bar_y + bar_h), fill=(40, 40, 40))
        # Fill
        if progress_value > 0:
            fill_w = int((progress_value / 100.0) * bar_w)
            self.draw.rectangle((bar_x, bar_y, bar_x + fill_w, bar_y + bar_h), fill=accent)
        # Label below bar
        self.draw.text((4, bar_h + 2), progress_label, font=self.font_tiny, fill=secondary)

        # === CENTER: Character placeholder + speech bubble ===
        center_top = bar_h + 16
        center_bottom = self.height - 24
        center_h = center_bottom - center_top
        
        # Character box (left side)
        char_w = int(content_width * 0.4)
        char_h = int(center_h * 0.7)
        char_x = 4
        char_y = center_top + 10
        self.draw.rectangle((char_x, char_y, char_x + char_w, char_y + char_h), outline=secondary)
        # Placeholder text
        self.draw.text((char_x + 4, char_y + char_h // 2 - 5), "Art", font=self.font_tiny, fill=secondary)
        
        # Speech bubble (right of character)
        bubble_x = char_x + char_w + 4
        bubble_y = center_top
        bubble_w = content_width - bubble_x - 4
        bubble_h = int(center_h * 0.4)
        self.draw.rectangle((bubble_x, bubble_y, bubble_x + bubble_w, bubble_y + bubble_h), outline=accent)
        if bubble_text:
            self.draw.text((bubble_x + 3, bubble_y + 3), bubble_text[:10], font=self.font_tiny, fill=primary)

        # Schedule summary below character area
        if schedule_summary:
            self.draw.text((4, center_bottom - 2), schedule_summary[:20], font=self.font_tiny, fill=secondary)

        # === BOTTOM: Clock and WiFi ===
        bottom_y = self.height - 20
        self.draw.text((4, bottom_y), time_str, font=self.font_small, fill=accent)
        self.draw.text((4, bottom_y + 12), date_str, font=self.font_tiny, fill=secondary)
        
        wifi_color = (100, 255, 100) if wifi_connected else (255, 80, 80)
        wifi_text = "WiFi" if wifi_connected else "NoWiFi"
        self.draw.text((content_width - 36, bottom_y + 4), wifi_text, font=self.font_tiny, fill=wifi_color)

        # === RIGHT SIDEBAR ===
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
