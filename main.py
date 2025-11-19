#!/usr/bin/env python3
import sys
import time

try:
    from display_waveshare import WaveshareDisplay
    from input_handler import InputHandler
    from menu import Menu
    
    print("Starting Pi Schedule Display...")
    
    display = WaveshareDisplay()
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
