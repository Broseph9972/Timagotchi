"""
Real Doom on Waveshare 128x128 LCD.
Runs Chocolate Doom in a virtual X display and captures/scales frames to the LCD.
Press KEY1, KEY2, or KEY3 to exit and return to menu.

Requirements (install via apt):
  sudo apt install chocolate-doom xvfb xdotool python3-mss
  
You also need a doom.wad file (shareware or full) in ~/timagotchi/roms/
"""

import os
import subprocess
import time
import threading

try:
    import mss
    HAS_MSS = True
except ImportError:
    HAS_MSS = False

from PIL import Image

# Path to DOOM WAD file
# Check same directory as this script first
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DOOM_WAD_PATHS = [
    os.path.join(_SCRIPT_DIR, "doom1.wad"),
    os.path.join(_SCRIPT_DIR, "doom.wad"),
    os.path.join(_SCRIPT_DIR, "DOOM1.WAD"),
    os.path.join(_SCRIPT_DIR, "DOOM.WAD"),
    os.path.expanduser("~/timagotchi/roms/doom.wad"),
    os.path.expanduser("~/timagotchi/roms/doom1.wad"),
    "/usr/share/games/doom/doom1.wad",
    "/usr/share/doom/doom1.wad",
]

# Virtual display settings
VIRTUAL_DISPLAY = ":99"
DOOM_WIDTH = 320
DOOM_HEIGHT = 200


def find_doom_wad():
    """Find a DOOM WAD file."""
    for path in DOOM_WAD_PATHS:
        if os.path.exists(path):
            return path
    return None


def find_chocolate_doom():
    """Find chocolate-doom executable."""
    candidates = [
        "chocolate-doom",
        "/usr/games/chocolate-doom",
        "/usr/local/bin/chocolate-doom",
    ]
    for cmd in candidates:
        try:
            result = subprocess.run(["which", cmd], capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip()
        except:
            pass
    return None


class RealDoom:
    """Runs actual Chocolate Doom and displays on Waveshare LCD."""
    
    def __init__(self, display, input_handler):
        self.display = display
        self.input_handler = input_handler
        self.running = False
        self.doom_process = None
        self.xvfb_process = None
        self.capture_thread = None
        self.current_frame = None
        self.frame_lock = threading.Lock()
        
    def start(self):
        """Start Doom and the display loop."""
        # Check dependencies
        if not HAS_MSS:
            self._show_error("Missing mss module\nsudo pip3 install mss")
            return 'key1'
        
        doom_exe = find_chocolate_doom()
        if not doom_exe:
            self._show_error("chocolate-doom not found\nsudo apt install\nchocolate-doom")
            return 'key1'
        
        wad_path = find_doom_wad()
        if not wad_path:
            self._show_error("doom.wad not found\nPlace in:\n~/timagotchi/roms/")
            return 'key1'
        
        # Check for xvfb
        try:
            subprocess.run(["which", "Xvfb"], capture_output=True, check=True)
        except:
            self._show_error("Xvfb not found\nsudo apt install xvfb")
            return 'key1'
        
        # Check for xdotool
        try:
            subprocess.run(["which", "xdotool"], capture_output=True, check=True)
        except:
            self._show_error("xdotool not found\nsudo apt install xdotool")
            return 'key1'
        
        self._show_status("Starting Doom...")
        
        try:
            # Start virtual X display
            self.xvfb_process = subprocess.Popen(
                ["Xvfb", VIRTUAL_DISPLAY, "-screen", "0", f"{DOOM_WIDTH}x{DOOM_HEIGHT}x24"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            time.sleep(0.5)
            
            # Set DISPLAY environment
            env = os.environ.copy()
            env["DISPLAY"] = VIRTUAL_DISPLAY
            
            # Start Chocolate Doom
            self.doom_process = subprocess.Popen(
                [
                    doom_exe,
                    "-iwad", wad_path,
                    "-width", str(DOOM_WIDTH),
                    "-height", str(DOOM_HEIGHT),
                    "-window",
                    "-nogui",
                    "-nomouse",
                ],
                env=env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            time.sleep(1.5)  # Give Doom time to start
            
            # Check if Doom started
            if self.doom_process.poll() is not None:
                self._show_error("Doom failed to start\nCheck WAD file")
                self._cleanup()
                return 'key1'
            
            self._show_status("Doom running!")
            time.sleep(0.5)
            
            # Start capture thread
            self.running = True
            self.capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
            self.capture_thread.start()
            
            # Main input/display loop
            exit_key = self._main_loop()
            
            return exit_key
            
        except Exception as e:
            self._show_error(f"Error: {str(e)[:40]}")
            time.sleep(2)
            return 'key1'
        finally:
            self._cleanup()
    
    def _capture_loop(self):
        """Background thread that captures frames from Doom."""
        os.environ["DISPLAY"] = VIRTUAL_DISPLAY
        
        with mss.mss(display=VIRTUAL_DISPLAY) as sct:
            monitor = {"top": 0, "left": 0, "width": DOOM_WIDTH, "height": DOOM_HEIGHT}
            
            while self.running:
                try:
                    # Capture screen
                    screenshot = sct.grab(monitor)
                    
                    # Convert to PIL Image
                    img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
                    
                    # Scale to display size (maintain aspect ratio)
                    # Doom is 320x200, display is 128x128
                    # Scale to 128x80 and center vertically
                    scaled = img.resize((128, 80), Image.NEAREST)
                    
                    with self.frame_lock:
                        self.current_frame = scaled
                    
                except Exception:
                    pass
                
                time.sleep(0.033)  # ~30 FPS capture
    
    def _main_loop(self):
        """Main loop handling input and display."""
        last_render = 0
        render_interval = 0.05  # 20 FPS to display
        
        while self.running:
            # Check for exit keys
            action = self.input_handler.get_input()
            
            if action in ('key1', 'key2', 'key3'):
                self.running = False
                return action
            
            # Send input to Doom via xdotool
            self._handle_input(action)
            
            # Render frame to display
            current_time = time.time()
            if current_time - last_render > render_interval:
                self._render_frame()
                last_render = current_time
            
            time.sleep(0.016)  # ~60 Hz input polling
        
        return 'key1'
    
    def _handle_input(self, action):
        """Send keyboard input to Doom via xdotool."""
        env = os.environ.copy()
        env["DISPLAY"] = VIRTUAL_DISPLAY
        
        # Map GPIO buttons to Doom keys
        key_map = {
            'up': 'Up',        # Move forward
            'down': 'Down',    # Move backward  
            'left': 'Left',    # Turn left
            'right': 'Right',  # Turn right
            'select': 'ctrl',  # Fire
        }
        
        if action and action in key_map:
            try:
                subprocess.Popen(
                    ["xdotool", "key", "--delay", "50", key_map[action]],
                    env=env,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            except:
                pass
    
    def _render_frame(self):
        """Render captured frame to the Waveshare display."""
        self.display.clear((0, 0, 0))
        
        with self.frame_lock:
            frame = self.current_frame
        
        if frame:
            # Center the 128x80 frame vertically on 128x128 display
            y_offset = (128 - 80) // 2
            self.display.image.paste(frame, (0, y_offset))
        else:
            # No frame yet - show loading
            self.display.draw.text(
                (30, 55), "Loading...",
                font=self.display.font_medium,
                fill=(255, 100, 100)
            )
        
        # Draw title bar
        self.display.draw.rectangle((0, 0, 128, 10), fill=(40, 0, 0))
        self.display.draw.text((2, 0), "DOOM", font=self.display.font_tiny, fill=(255, 100, 100))
        self.display.draw.text((90, 0), "K1-3:Exit", font=self.display.font_tiny, fill=(150, 150, 150))
        
        self.display._render()
    
    def _show_status(self, message):
        """Show a status message."""
        self.display.clear((20, 0, 0))
        self.display.draw.text((10, 50), "DOOM", font=self.display.font_large, fill=(255, 50, 50))
        self.display.draw.text((10, 75), message, font=self.display.font_small, fill=(200, 200, 200))
        self.display._render()
    
    def _show_error(self, message):
        """Show an error message."""
        self.display.clear((40, 0, 0))
        self.display.draw.text((10, 20), "DOOM Error", font=self.display.font_medium, fill=(255, 100, 100))
        
        # Multi-line message
        y = 45
        for line in message.split('\n'):
            self.display.draw.text((10, y), line, font=self.display.font_small, fill=(255, 255, 255))
            y += 14
        
        self.display.draw.text((10, 110), "Press any key", font=self.display.font_tiny, fill=(150, 150, 150))
        self.display._render()
        
        # Wait for any key
        while True:
            action = self.input_handler.get_input()
            if action:
                break
            time.sleep(0.1)
    
    def _cleanup(self):
        """Clean up processes."""
        self.running = False
        
        if self.doom_process:
            try:
                self.doom_process.terminate()
                self.doom_process.wait(timeout=2)
            except:
                try:
                    self.doom_process.kill()
                except:
                    pass
        
        if self.xvfb_process:
            try:
                self.xvfb_process.terminate()
                self.xvfb_process.wait(timeout=2)
            except:
                try:
                    self.xvfb_process.kill()
                except:
                    pass


def run_doom(display, input_handler):
    """
    Run real Doom on the Waveshare display.
    Returns the exit key pressed ('key1', 'key2', 'key3') or None.
    """
    game = RealDoom(display, input_handler)
    return game.start()
