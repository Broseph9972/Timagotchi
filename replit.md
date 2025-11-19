# Pi Schedule Display Project

## Overview
This project ports a school schedule display from a Raspberry Pi Pico W to a Raspberry Pi Zero WH with a Waveshare 1.44" LCD HAT. It displays class schedules with a navigable menu system and includes RetroPie integration.

## Target Hardware
- **Board**: Raspberry Pi Zero WH (compatible with all Pi models)
- **Display**: Waveshare 1.44" LCD HAT
  - Controller: ST7735S
  - Resolution: 128x128 pixels
  - Interface: SPI
  - Features: 5-way joystick + 3 buttons
- **OS**: Raspberry Pi OS (Bookworm or later)

## Project Structure

### Core Files
- `main.py` - Application entry point with menu system integration
- `display_waveshare.py` - Display driver for ST7735S LCD (128x128)
- `input_handler.py` - Joystick and button input handling
- `menu.py` - Menu system with schedule, clock, settings, and RetroPie launcher
- `config.py` - School schedule configuration

### Configuration Files
- `configure_schedule.py` - Interactive schedule configuration tool
- `pyproject.toml` - Python dependencies

### Legacy Files (Pico W)
- `rtc.py` - Old DS3231 RTC code (not used on Pi)
- `display.py` - Old SSD1306 OLED code (not used)

## Features

### 1. Schedule View
- Shows current period number and name
- Displays time remaining in current period
- Countdown to lunch
- Countdown to end of school day
- Supports advisory/freetime periods
- A/B day schedule support

### 2. Menu System
- Main Menu with joystick navigation
- Schedule screen (live updates every second)
- Clock screen (digital time + date)
- Settings screen (future expansion)
- RetroPie launcher

### 3. RetroPie Integration
- Menu option to launch EmulationStation
- Clean exit from schedule app
- Can auto-restart after RetroPie exits (via systemd)

## Dependencies

### Python Packages
- `st7735>=0.2.0` - ST7735S display driver (128x128 LCD)
- `pillow>=10.0.0` - Image processing and fonts
- `numpy>=1.24.0` - Numerical operations
- `spidev>=3.6` - SPI communication
- `rpi-lgpio>=0.4` - GPIO library (Bookworm-compatible, RPi.GPIO drop-in replacement)
- `lgpio>=0.2.2.0` - Low-level GPIO library for Raspberry Pi OS Bookworm

### System Requirements
- SPI interface enabled
- GPIO access (requires sudo or gpio group membership)
- DejaVu fonts (for nice display text)

## Controls

### Joystick
- **Up**: Move menu selection up
- **Down**: Move menu selection down
- **Left**: Go back to main menu
- **Right**: Select item (same as press)
- **Press**: Select item

### Buttons
- **Key1**: Back to main menu
- **Key2**: Reserved
- **Key3**: Reserved

## GPIO Pin Mapping (Waveshare 1.44" LCD HAT)

### Display (ST7735S)
- SPI Port: 0
- CS: GPIO 8 (CE0)
- DC: GPIO 25
- RST: GPIO 27
- Backlight: GPIO 24

### Joystick & Buttons
- Up: GPIO 6
- Down: GPIO 19
- Left: GPIO 5
- Right: GPIO 26
- Press: GPIO 13
- Key1: GPIO 21
- Key2: GPIO 20
- Key3: GPIO 16

Note: All buttons are active-low with pull-up resistors enabled.

## Development Notes

### Color Display (128x128)
The Waveshare 1.44" LCD HAT uses a compact color LCD:
- Different colors for different period types (lunch, advisory, regular)
- Color-coded time warnings
- Better visual hierarchy than monochrome OLED
- Smaller fonts optimized for 128x128 resolution

### Real-Time Updates
- Schedule and clock screens update every second
- Menu navigation is responsive (50ms polling)
- Debounce on buttons (200ms)

### RetroPie Compatibility
- Requires FBCP (framebuffer copy) setup to mirror HDMI to LCD
- Schedule app draws directly to LCD (no FBCP needed)
- Launches EmulationStation via subprocess when selected from menu
- Cleans up GPIO before launching
- App exits, then FBCP mirrors EmulationStation to LCD
- Can be configured to auto-restart after RetroPie exits
- See FBCP_RETROPIE_SETUP.md for detailed configuration

## Installation on Pi

### Quick Start
1. Clone/copy project to Pi
2. Enable SPI: `sudo raspi-config` → Interfacing → SPI
3. Install dependencies: `pip install -r requirements.txt`
4. Run: `sudo python3 main.py`

### Auto-Start Service
Create systemd service to run on boot and restart after RetroPie exits.

## Future Enhancements
- A/B day toggle in settings menu
- Custom color themes
- Network time sync
- Weather display
- Multiple schedule profiles
- Timer/stopwatch mode
- PROGRESS BAR
