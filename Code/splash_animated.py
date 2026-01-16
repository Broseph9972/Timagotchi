#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Animated splash screen for Timagotchi boot
Displays loading GIF until main application is ready
"""
import os
import sys
import importlib.util
from PIL import Image
import time

def _load_lcd_driver():
    """Load the Waveshare LCD driver (copied from display_waveshare.py)"""
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

    raise FileNotFoundError("Could not load Waveshare LCD driver (LCD_1in44)")

def load_gif_frames(gif_path):
    """Load all frames from animated GIF"""
    try:
        gif = Image.open(gif_path)
        frames = []
        durations = []
        
        try:
            while True:
                # Get frame duration in milliseconds
                duration = gif.info.get('duration', 100)
                durations.append(duration / 1000.0)  # Convert to seconds
                
                # Convert frame to RGB
                frame = gif.convert('RGB')
                frames.append(frame)
                
                gif.seek(gif.tell() + 1)
        except EOFError:
            pass  # End of GIF
        
        return frames, durations
    except Exception as e:
        print(f"Error loading GIF: {e}")
        return [], []

def create_centered_frame(gif_frame, canvas_size=(128, 128), bg_color=(255, 255, 255)):
    """
    Create a canvas with white background and center the GIF frame
    """
    canvas = Image.new('RGB', canvas_size, bg_color)
    
    # Calculate position to center the frame
    x = (canvas_size[0] - gif_frame.width) // 2
    y = (canvas_size[1] - gif_frame.height) // 2
    
    # Paste frame onto canvas
    canvas.paste(gif_frame, (x, y))
    
    return canvas

def run_splash():
    """Main splash screen loop"""
    try:
        LCD_1in44 = _load_lcd_driver()
        
        # Initialize display
        disp = LCD_1in44.LCD()
        scan_dir = LCD_1in44.SCAN_DIR_DFT
        disp.LCD_Init(scan_dir)
        disp.LCD_Clear()
        
        # Load GIF from Pics folder
        base_dir = os.path.dirname(os.path.dirname(__file__))  # Go up to Timagotchi root
        gif_path = os.path.join(base_dir, 'Pics', 'pwnagotchi.gif')
        
        if not os.path.exists(gif_path):
            print(f"GIF not found at {gif_path}")
            sys.exit(1)
        
        print(f"Loading GIF from {gif_path}")
        frames, durations = load_gif_frames(gif_path)
        
        if not frames:
            print("Failed to load GIF frames")
            sys.exit(1)
        
        print(f"Loaded {len(frames)} frames")
        
        # Signal file to check for ready signal
        ready_file = '/tmp/timagotchi_ready'
        
        # Animate until ready signal or timeout (15 seconds)
        start_time = time.time()
        frame_index = 0
        loop_count = 0
        
        while True:
            # Check for ready signal
            if os.path.exists(ready_file):
                print("Ready signal detected, exiting splash")
                disp.LCD_Clear()
                break
            
            # Timeout fallback (15 seconds)
            if time.time() - start_time > 15:
                print("Splash timeout, exiting")
                disp.LCD_Clear()
                break
            
            # Get current frame
            frame = frames[frame_index]
            duration = durations[frame_index]
            
            # Center frame on white background
            display_frame = create_centered_frame(frame, (128, 128), (255, 255, 255))
            
            # Display frame
            disp.LCD_ShowImage(display_frame, 0, 0)
            
            # Wait for frame duration
            time.sleep(max(duration, 0.08))  # Min 80ms between frames
            
            # Move to next frame
            frame_index = (frame_index + 1) % len(frames)
            if frame_index == 0:
                loop_count += 1
        
        print(f"Splash completed after {loop_count} loops")
        
    except Exception as e:
        print(f"Splash error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    run_splash()
