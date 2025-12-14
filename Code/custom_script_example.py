"""
Example custom script for Timagotchi.
This template shows how to create scripts that run on the 128x128 Waveshare display.

To use:
1. Rename this file to custom_script.py
2. Implement your logic in the run() function
3. Use display.draw to draw on the screen
4. Use display._render() to push changes to the LCD
5. Use input_handler.get_input() to read button presses
6. Return 'key1', 'key2', or 'key3' to navigate when exiting

Button mappings:
- 'up', 'down', 'left', 'right': D-pad
- 'select': Center button  
- 'key1': Top-right button (usually goes to Main Page)
- 'key2': Middle-right button (usually goes to Grades)
- 'key3': Bottom-right button (usually goes to Settings)
"""

import time


def run(display, input_handler):
    """
    Main entry point for custom scripts.
    
    Args:
        display: WaveshareDisplay instance with:
            - display.width, display.height (128x128)
            - display.draw: PIL ImageDraw object
            - display.image: PIL Image object  
            - display.font_tiny, font_small, font_medium, font_large
            - display.clear(color): Clear screen with color tuple
            - display._render(): Push image to LCD
            
        input_handler: InputHandler instance with:
            - input_handler.get_input(): Returns action string or None
            
    Returns:
        'key1', 'key2', 'key3' to navigate on exit, or None
    """
    running = True
    counter = 0
    
    while running:
        # Clear the screen
        display.clear((20, 30, 40))
        
        # Draw some text
        display.draw.text((10, 10), "Custom Script", font=display.font_medium, fill=(255, 255, 255))
        display.draw.text((10, 30), f"Counter: {counter}", font=display.font_small, fill=(100, 255, 100))
        
        # Draw a bouncing box
        box_x = 10 + (counter % 100)
        box_y = 60 + ((counter // 2) % 30)
        display.draw.rectangle((box_x, box_y, box_x + 20, box_y + 20), fill=(255, 100, 100), outline=(255, 255, 255))
        
        # Draw instructions
        display.draw.text((5, 110), "KEY1/2/3 to exit", font=display.font_tiny, fill=(150, 150, 150))
        
        # Push to display
        display._render()
        
        # Check for input
        action = input_handler.get_input()
        
        if action in ('key1', 'key2', 'key3'):
            return action  # Exit and navigate
        elif action == 'up':
            counter += 10
        elif action == 'down':
            counter -= 10
        elif action == 'select':
            counter = 0
        
        counter += 1
        time.sleep(0.05)  # ~20 FPS
    
    return 'key1'  # Default: go to main page
