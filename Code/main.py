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
    
    # Check if config.py exists - if not, run configuration portal
    config_path = os.path.join(os.path.dirname(__file__), 'config.py')
    if not os.path.exists(config_path):
        print("No configuration found. Starting Configuration Portal...")
        
        # Initialize minimal display for pairing
        theme_manager = ThemeManager()
        display = WaveshareDisplay(theme_manager)
        input_handler = InputHandler()
        
        # Run configuration portal
        from config_portal import run_configuration_portal
        success = run_configuration_portal(display, input_handler)
        
        if not success:
            print("Configuration cancelled or failed.")
            print("You can run configure_schedule.py manually to set up.")
            display.clear()
            sys.exit(1)
        
        # Configuration successful - restart to load new config
        print("Configuration complete. Restarting...")
        display.clear()
        os.execv(sys.executable, ['python3'] + sys.argv)
    
    # Initialize theme manager first
    theme_manager = ThemeManager()
    
    # Pass theme manager to display
    display = WaveshareDisplay(theme_manager)
    print("Display initialized")
    
    input_handler = InputHandler()
    print("Input handler initialized")
    
    menu = Menu(display, input_handler)
    print("Menu system ready")
    
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
