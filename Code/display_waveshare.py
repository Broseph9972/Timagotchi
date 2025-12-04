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
    def __init__(self):
        # Initialize the Waveshare LCD
        self.disp = LCD_1in44.LCD()
        scan_dir = LCD_1in44.SCAN_DIR_DFT
        self.disp.LCD_Init(scan_dir)
        self.disp.LCD_Clear()

        self.width = self.disp.width
        self.height = self.disp.height

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

    def show_schedule(self, period, period_name, time_remaining, lunch_time, end_time, current_time_str):
        self.clear()
        
        y_offset = 2
        self.draw.text((2, y_offset), current_time_str, font=self.font_medium, fill=(100, 200, 255))
        y_offset += 18

        if period == "LUNCH":
            self.draw.text((2, y_offset), "LUNCH", font=self.font_large, fill=(255, 200, 0))
        elif period == "ADVISORY":
            self.draw.text((2, y_offset), "ADVISORY", font=self.font_large, fill=(0, 255, 150))
        elif period == "FREETIME":
            self.draw.text((2, y_offset), "FREE TIME", font=self.font_medium, fill=(150, 255, 150))
        elif period is not None:
            self.draw.text((2, y_offset), f"Period {period}", font=self.font_large, fill=(255, 255, 255))
            y_offset += 20
            self.draw.text((2, y_offset), period_name, font=self.font_small, fill=(200, 200, 200))
        else:
            self.draw.text((2, y_offset), "Passing", font=self.font_large, fill=(200, 200, 200))

        y_offset += 25

        if time_remaining:
            self.draw.text((2, y_offset), f"Left: {time_remaining}", font=self.font_small, fill=(100, 255, 100))
            y_offset += 16

        if lunch_time:
            self.draw.text((2, y_offset), f"Lunch: {lunch_time}", font=self.font_small, fill=(255, 200, 100))
            y_offset += 16

        if end_time:
            self.draw.text((2, y_offset), f"Ends: {end_time}", font=self.font_small, fill=(255, 100, 100))

        self._render()

    def show_menu(self, menu_items, selected_index, title="Menu"):
        self.clear()
        
        y_offset = 2
        self.draw.text((2, y_offset), title, font=self.font_large, fill=(100, 200, 255))
        y_offset += 22

        for i, item in enumerate(menu_items):
            if i == selected_index:
                self.draw.rectangle((1, y_offset - 1, self.width - 1, y_offset + 15), outline=(255, 255, 0), width=1)
                self.draw.text((4, y_offset), f"> {item}", font=self.font_small, fill=(255, 255, 0))
            else:
                self.draw.text((4, y_offset), f"  {item}", font=self.font_small, fill=(200, 200, 200))
            y_offset += 18

        self._render()

    def show_message(self, title, message, color=(255, 255, 255)):
        self.clear()

        self.draw.text((2, 40), title, font=self.font_large, fill=color)

        y_offset = 65
        for line in message.split("\n"):
            self.draw.text((2, y_offset), line, font=self.font_tiny, fill=(200, 200, 200))
            y_offset += 14

        self._render()

    def show_clock(self, time_str, date_str):
        self.clear()

        self.draw.text((5, 45), time_str, font=self.font_medium, fill=(100, 200, 255))
        self.draw.text((5, 70), date_str, font=self.font_tiny, fill=(200, 200, 200))

        self._render()
