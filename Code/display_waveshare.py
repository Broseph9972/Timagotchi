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
        
        # Icon cache for sidebar and main menu
        self.icon_cache = {}
        self._load_icons()
    
    def _load_icons(self):
        """Load icons from the Icons folder and cache them."""
        icons_dir = os.path.join(os.path.dirname(__file__), 'Icons')
        icon_files = {
            'home': 'home.png',
            'icon': 'Icon.png',
            'settings': 'settings.png',
            'grades': 'grades.png',
            'textbox': 'textbox.png',
            'speechbubble': 'speechbubble.png'
        }
        
        for key, filename in icon_files.items():
            icon_path = os.path.join(icons_dir, filename)
            try:
                if os.path.exists(icon_path):
                    img = Image.open(icon_path)
                    # Keep RGBA to preserve transparency/alpha channel
                    if img.mode != 'RGBA':
                        img = img.convert('RGBA')
                    self.icon_cache[key] = img
            except Exception as e:
                pass  # Silently skip icons that fail to load
    
    def _get_icon(self, icon_name):
        """Get a cached icon by name."""
        return self.icon_cache.get(icon_name)
    
    def _get_nav_item_icon_name(self, nav_item):
        """Map nav item name to icon name."""
        nav_map = {
            "Main Page": "home",
            "Grades": "grades",
            "Settings": "settings"
        }
        return nav_map.get(nav_item, None)

    def _render(self):
        """Push the PIL image to the LCD."""
        self.disp.LCD_ShowImage(self.image, 0, 0)

    def clear(self, color=(0, 0, 0)):
        self.draw.rectangle((0, 0, self.width, self.height), fill=color)

    # Layout constants
    SIDEBAR_WIDTH = 8  # ultra-narrow gutter for icon placeholders
    PROGRESS_BAR_HEIGHT = 8
    WIFI_BOX_SIZE = 8  # height of wifi indicator bar at sidebar bottom

    def _render_sidebar(self, nav_items, selected_index):
        """Draw the right-side vertical navigation with icons."""
        if not nav_items:
            return
        secondary = self._get_text_secondary_color()
        accent_sel = (255, 255, 0)
        bg = self._get_bg_color()
        # Theme-driven colors
        box_fill = self.theme_manager.get_sidebar_box() if self.theme_manager else (30, 30, 30)
        box_fill_sel = self.theme_manager.get_sidebar_box_selected() if self.theme_manager else (60, 60, 40)
        divider_color = self.theme_manager.get_divider() if self.theme_manager else (80, 80, 80)
        
        # Clear sidebar area
        sidebar_x = self.width - self.SIDEBAR_WIDTH
        self.draw.rectangle((sidebar_x, 0, self.width, self.height), fill=bg)
        
        # Distribute items evenly along sidebar height (leave room for wifi box at bottom)
        usable_height = self.height - self.WIFI_BOX_SIZE - 2
        item_height = usable_height // len(nav_items)
        
        for i, item in enumerate(nav_items):
            y_start = i * item_height
            y_end = (i + 1) * item_height
            y_center = y_start + item_height // 2
            color = accent_sel if i == selected_index else secondary
            fill = box_fill_sel if i == selected_index else box_fill
            
            # Fill box for this item
            self.draw.rectangle((sidebar_x + 1, y_start + 1, self.width - 1, y_end - 1), fill=fill)
            
            # Divider line between items
            if i > 0:
                self.draw.line((sidebar_x, y_start, self.width, y_start), fill=divider_color, width=1)
            
            # Try to display icon for this nav item
            icon_name = self._get_nav_item_icon_name(item)
            icon = self._get_icon(icon_name) if icon_name else None
            
            if icon:
                # Resize icon to fit in sidebar box
                margin = 1
                max_size = self.SIDEBAR_WIDTH - 2 * margin
                icon_resized = icon.copy()
                icon_resized.thumbnail((max_size, item_height - 2 * margin), Image.LANCZOS)
                
                # Center icon in the box
                paste_x = sidebar_x + (self.SIDEBAR_WIDTH - icon_resized.width) // 2
                paste_y = y_start + (item_height - icon_resized.height) // 2
                # Use alpha channel as mask for transparency
                if icon_resized.mode == 'RGBA':
                    self.image.paste(icon_resized, (paste_x, paste_y), icon_resized)
                else:
                    self.image.paste(icon_resized, (paste_x, paste_y))
            else:
                # Fallback: draw placeholder box if icon not found
                inner_margin = 1
                inner_x0 = sidebar_x + inner_margin
                inner_y0 = y_start + inner_margin
                inner_x1 = self.width - inner_margin
                inner_y1 = y_end - inner_margin
                self.draw.rectangle((inner_x0, inner_y0, inner_x1, inner_y1), outline=divider_color)
            
            # Selection indicator: small bar to the left
            if i == selected_index:
                bar_x = sidebar_x - 2
                self.draw.line((bar_x, y_start + 2, bar_x, y_end - 2), fill=accent_sel, width=2)

    def _render_wifi_indicator(self, wifi_connected):
        """Draw a status bar that matches the sidebar width at the bottom."""
        bar_height = self.WIFI_BOX_SIZE
        sidebar_x = self.width - self.SIDEBAR_WIDTH
        y0 = self.height - bar_height
        color = (0, 200, 0) if wifi_connected else (200, 0, 0)
        self.draw.rectangle((sidebar_x, y0, self.width, self.height), fill=color)

    def show_schedule(self, period, period_name, time_remaining, lunch_time, end_time, current_time_str, nav_items=None, selected_index=0, wifi_connected=False):
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

        # Sidebar overlay + WiFi
        self._render_sidebar(nav_items or [], selected_index)
        self._render_wifi_indicator(wifi_connected)
        self._render()

    def show_menu(self, menu_items, selected_index, title="Menu", progress_label="", progress_value=0, nav_items=None, nav_selected_index=0, start_index=0, max_visible=5, wifi_connected=False):
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

        # Sidebar + WiFi
        self._render_sidebar(nav_items or [], nav_selected_index)
        self._render_wifi_indicator(wifi_connected)
        self._render()

    def show_message(self, title, message, color=(255, 255, 255), nav_items=None, nav_selected_index=0, wifi_connected=False):
        self.clear(self._get_bg_color())
        
        content_width = self.width - self.SIDEBAR_WIDTH - 4

        self.draw.text((4, 8), title, font=self.font_medium, fill=color if color else self._get_accent_color())

        y_offset = 28
        for line in message.split("\n"):
            # Truncate long lines
            display_line = line[:18] if len(line) > 18 else line
            self.draw.text((4, y_offset), display_line, font=self.font_tiny, fill=self._get_text_secondary_color())
            y_offset += 12

        # Sidebar + WiFi
        self._render_sidebar(nav_items or [], nav_selected_index)
        self._render_wifi_indicator(wifi_connected)
        self._render()

    def show_clock(self, time_str, date_str, nav_items=None, nav_selected_index=0, wifi_connected=False):
        self.clear(self._get_bg_color())
        
        content_width = self.width - self.SIDEBAR_WIDTH - 4

        # Center clock in content area
        self.draw.text((10, 40), time_str, font=self.font_large, fill=self._get_accent_color())
        self.draw.text((10, 65), date_str, font=self.font_small, fill=self._get_text_secondary_color())

        # Sidebar + WiFi
        self._render_sidebar(nav_items or [], nav_selected_index)
        self._render_wifi_indicator(wifi_connected)
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
        progress_bg = self.theme_manager.get_progress_bg() if self.theme_manager else (40, 40, 40)
        self.draw.rectangle((bar_x, bar_y, bar_x + bar_w, bar_y + bar_h), fill=progress_bg)
        # Fill
        if progress_value > 0:
            fill_w = int((progress_value / 100.0) * bar_w)
            self.draw.rectangle((bar_x, bar_y, bar_x + fill_w, bar_y + bar_h), fill=accent)
        # Label below bar
        self.draw.text((4, bar_h + 2), progress_label, font=self.font_tiny, fill=secondary)

        # === CENTER: Character placeholder + text boxes ===
        center_top = bar_h + 16
        center_bottom = self.height - 24
        center_h = center_bottom - center_top
        
        # Character box (left side) - NO bounding box
        char_w = int(content_width * 0.4)
        char_h = int(center_h * 0.7)
        char_x = 4
        char_y = center_top + 10
        
        # Try to load and display icon (for main page, use Icon.png not home.png)
        page_icon = self._get_icon('icon')
        if page_icon:
            try:
                # Resize icon to fit character box (with margin)
                margin = 2
                max_w = char_w - 2*margin
                max_h = char_h - 2*margin
                icon_resized = page_icon.copy()
                icon_resized.thumbnail((max_w, max_h), Image.LANCZOS)
                # Center in box
                paste_x = char_x + (char_w - icon_resized.width) // 2
                paste_y = char_y + (char_h - icon_resized.height) // 2
                # Use alpha channel as mask for transparency
                if icon_resized.mode == 'RGBA':
                    self.image.paste(icon_resized, (paste_x, paste_y), icon_resized)
                else:
                    self.image.paste(icon_resized, (paste_x, paste_y))
            except Exception as e:
                pass
        
        # Text bubble area (right of character)
        box_x = char_x + char_w + 4
        box_width = content_width - box_x - 4
        box_top = center_top

        # Top: speechbubble.png with class/time info (what the character is saying)
        speechbubble_height = int(center_h * 0.38)
        speechbubble_y = box_top
        speechbubble = self._get_icon('speechbubble')
        if speechbubble:
            try:
                sb_resized = speechbubble.copy()
                sb_resized.thumbnail((box_width, speechbubble_height), Image.LANCZOS)
                paste_x = box_x + (box_width - sb_resized.width) // 2
                if sb_resized.mode == 'RGBA':
                    self.image.paste(sb_resized, (paste_x, speechbubble_y), sb_resized)
                else:
                    self.image.paste(sb_resized, (paste_x, speechbubble_y))
            except Exception:
                pass
        # Draw main text in black on the speech bubble
        if bubble_text:
            self.draw.text((box_x + 6, speechbubble_y + 6), bubble_text[:22], font=self.font_tiny, fill=(0, 0, 0))

        # Bottom: textbox.png as a thought bubble with placeholder text
        thought_height = int(center_h * 0.38)
        thought_y = speechbubble_y + speechbubble_height + 4
        textbox = self._get_icon('textbox')
        if textbox:
            try:
                tb_resized = textbox.copy()
                tb_resized.thumbnail((box_width, thought_height), Image.LANCZOS)
                paste_x = box_x + (box_width - tb_resized.width) // 2
                if tb_resized.mode == 'RGBA':
                    self.image.paste(tb_resized, (paste_x, thought_y), tb_resized)
                else:
                    self.image.paste(tb_resized, (paste_x, thought_y))
            except Exception:
                pass
        # Placeholder thought text in black
        self.draw.text((box_x + 6, thought_y + 6), "placeholder text", font=self.font_tiny, fill=(0, 0, 0))

        # === BOTTOM: Clock only (WiFi is in sidebar area) ===
        # Move up a bit to avoid overlap with summary/wifi
        bottom_y = self.height - (self.WIFI_BOX_SIZE + 18)
        self.draw.text((4, bottom_y - 2), time_str, font=self.font_small, fill=accent)
        self.draw.text((4, bottom_y + 10), date_str, font=self.font_tiny, fill=secondary)

        # === RIGHT SIDEBAR ===
        self._render_sidebar(nav_items or [], selected_index)
        
        # === WIFI indicator box in very bottom right ===
        self._render_wifi_indicator(wifi_connected)
        
        self._render()
    
    def show_grades_menu(self, menu_items, selected_index, title="Grades", nav_items=None, nav_selected_index=0, start_index=0, max_visible=5, wifi_connected=False):
        """Display grades menu with menu items."""
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
        
        # Sidebar + WiFi
        self._render_sidebar(nav_items or [], nav_selected_index)
        self._render_wifi_indicator(wifi_connected)
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
