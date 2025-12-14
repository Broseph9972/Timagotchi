"""
Real Doom wrapper - tries to use PyDoom if available, falls back to raycaster.
"""

import os
import subprocess
import sys

# Try to import PyDoom
PYDOOM_AVAILABLE = False
try:
    import pydoom
    PYDOOM_AVAILABLE = True
except ImportError:
    pass

def find_wad():
    """Find doom1.wad in common locations."""
    paths = [
        os.path.join(os.path.dirname(__file__), "doom1.wad"),
        os.path.join(os.path.dirname(__file__), "doom.wad"),
        os.path.expanduser("~/timagotchi/roms/doom1.wad"),
        os.path.expanduser("~/timagotchi/roms/doom.wad"),
    ]
    for path in paths:
        if os.path.exists(path):
            return path
    return None


def install_pydoom():
    """Attempt to install PyDoom from GitHub."""
    print("Installing PyDoom...")
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "git+https://github.com/Pink-Silver/PyDoom.git"],
            check=True
        )
        return True
    except:
        return False


def run_pydoom_game(display, input_handler):
    """Run actual PyDoom (returns key press to exit)."""
    wad = find_wad()
    if not wad:
        display.show_message("PyDoom", "doom1.wad not found", (255, 100, 100), [], 0, False)
        return 'key1'
    
    # PyDoom runs in its own window, not on our display
    # This is a limitation - we'd need to pipe its output
    # For now, show that we tried
    display.show_message("PyDoom", "Starting...", (100, 200, 255), [], 0, False)
    
    try:
        # Try running PyDoom with the WAD
        subprocess.run(["python3", "-c", f"import pydoom; pydoom.run('{wad}')"])
        return 'key1'
    except Exception as e:
        display.show_message("PyDoom", f"Failed: {str(e)[:40]}", (255, 100, 100), [], 0, False)
        return 'key1'


def run_doom(display, input_handler):
    """
    Try to run real Doom (PyDoom), fall back to raycaster.
    Returns the exit key pressed ('key1', 'key2', 'key3') or None.
    """
    if PYDOOM_AVAILABLE:
        return run_pydoom_game(display, input_handler)
    else:
        # Fall back to raycaster
        try:
            from doom_raycaster import run_raycaster
            return run_raycaster(display, input_handler)
        except ImportError:
            display.show_message("Doom", "No Doom engine available", (255, 100, 100), [], 0, False)
            return 'key1'
