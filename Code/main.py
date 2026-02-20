#!/usr/bin/env python3
import sys
import time
import os

try:
    from display_waveshare import WaveshareDisplay
    from input_handler import InputHandler
    from menu import Menu
    from theme_manager import ThemeManager
    
    print("Starting Pi Schedule Display...")
    
    # Initialize theme manager first
    theme_manager = ThemeManager()
    
    # Pass theme manager to display
    display = WaveshareDisplay(theme_manager)
    print("Display initialized")
    
    input_handler = InputHandler()
    print("Input handler initialized")
    
    menu = Menu(display, input_handler)
    print("Menu system ready")
    
    # Check for updates on boot (non-blocking, silent check)
    print("Checking for updates...")
    if menu.check_updates_on_boot():
        print("Updates found and applied. Restarting...")
        display.clear()
        os.execv(sys.executable, [sys.executable] + sys.argv)
    
    # Signal splash screen that we're ready
    # This allows the animated splash to exit gracefully
    try:
        ready_file = '/tmp/timagotchi_ready'
        with open(ready_file, 'w') as f:
            f.write('1')
        print("Sent ready signal to splash screen")
    except Exception as e:
        print(f"Warning: Could not write ready signal: {e}")
    
    menu.run()
    
    print("Exiting...")
    display.clear()
    
except KeyboardInterrupt:
    print("\nExiting on keyboard interrupt...")
    sys.exit(0)
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
