# Pi Schedule Display

A school schedule display system for Raspberry Pi Zero WH with Waveshare 1.44" LCD HAT.

## Overview

This project ports a school schedule display from a Raspberry Pi Pico W to a Raspberry Pi Zero WH equipped with the Waveshare 1.44" LCD HAT. It renders a colorful class schedule, clock, and a RetroArch-powered games menu on the ST7735S display while the HAT’s joystick and extra buttons keep navigation tactile.

## Features

- **Schedule View**: Shows current period, class name, time remaining, lunch countdown, and end of day.
- **Clock View**: Digital clock with date and optional 12/24-hour display.
- **Menu System**: Main, schedule, clock, settings, and games screens with joystick navigation.
- **RetroArch Games Menu**: Launch curated games (e.g., Tetris and Doom) directly through RetroArch.
- **Joystick & Buttons**: Full 5-way joystick plus three extra buttons for shortcuts/back navigation.
- **Systemd-Friendly**: Service file included for clean auto-start and restart after RetroPie exits.

## Target Hardware

- **Board**: Raspberry Pi Zero WH (compatible with other Pi models)
- **Display**: Waveshare 1.44" LCD HAT (ST7735S controller, 128x128 pixels, SPI interface, 5-way joystick + 3 buttons)
- **Operating System**: Raspberry Pi OS (tested on Bookworm)

## Project Structure

### Core Files
- `main.py` – Application entry point with menu integration.
- `display_waveshare.py` – ST7735S display driver and drawing helpers.
- `input_handler.py` – Joystick and button handling (RPi.GPIO or lgpio backend).
- `menu.py` – Menu logic, RetroArch game launcher, and on-screen views.
- `display.py` – Legacy SSD1306 OLED code (kept for reference).
- `rtc.py` – Legacy DS3231 RTC helper (not used on Pi builds).

### Configuration & Utilities
- `config.py` – Schedule definition (editable manually or via the helper script).
- `configure_schedule.py` – Interactive schedule configurator.
- `schedule-display.service` – systemd unit for auto-start/restart.
- `install.sh` / `start.sh` – Setup and launch helpers.
- `old code/` – Vendor-supplied LCD driver snapshot used as a fallback loader.

## Dependencies

### Python Packages
- `st7735>=0.2.0` – ST7735S display driver (128x128 LCD).
- `pillow>=10.0.0` – Image rendering and fonts.
- `numpy>=1.24.0` – Numerical helpers for drawing.
- `spidev>=3.6` – SPI communication.
- `rpi-lgpio>=0.4` – GPIO access on Raspberry Pi OS Bookworm.
- `lgpio>=0.2.2.0` – Low-level GPIO interface used when RPi.GPIO is unavailable.

### System Requirements
- SPI interface enabled (`sudo raspi-config` → Interfacing Options → SPI).
- GPIO access (run as `sudo` or add your user to the `gpio` group).
- DejaVu fonts installed (`ttf-dejavu`) for clean typography.
- RetroArch installed (`sudo apt install retroarch libretro`) for the Games menu.

## Installation

### Automated Installation (Recommended)

```bash
chmod +x install.sh
./install.sh
```

> **Windows tip:** If you cloned or edited these files on Windows, run `dos2unix install.sh start.sh` before executing them so Bash doesn’t choke on CRLF line endings.

This will:
- Check if SPI is enabled
- Install system dependencies
- Install Python packages
- Add your user to the GPIO group

**Important**: After installation, log out and log back in (or reboot) for GPIO permissions to take effect.

### Manual Installation

#### 1. Enable SPI Interface

```bash
sudo raspi-config
```

Navigate to: **Interfacing Options → SPI → Yes**, then reboot.

#### 2. Install Dependencies

```bash
sudo apt-get update
sudo apt-get install python3-pip python3-pil python3-numpy
pip3 install -r requirements.txt
```

#### 3. Configure GPIO Permissions

```bash
sudo usermod -aG gpio $USER
```

Log out and log back in for this to take effect.

#### 4. Configure Your Schedule

Edit `config.py` to set your school schedule, or run:

```bash
python3 configure_schedule.py
```

## Usage

### Run Manually

```bash
sudo python3 main.py
```

Note: `sudo` is required for GPIO access.

### Controls

#### Joystick
- **Up/Down**: Move through menu items.
- **Left**: Go back to the previous screen.
- **Right/Press**: Select the highlighted item.

#### Buttons
- **Key1**: Quick back to the main menu.
- **Key2**: Reserved for future features.
- **Key3**: Reserved for future features.

_All joystick directions and buttons are active-low with pull-ups enabled._

### Menu Options

1. **Schedule**: View current class schedule
2. **Clock**: View current time and date
3. **Settings**: Configure preferences
4. **Games**: Open the curated RetroArch launcher (Tetris, Doom)
5. **Exit**: Close the application

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

## Development Notes

- **Color Display (128x128)**: Uses color cues for period types (lunch, advisory, passing) and optimized fonts for the tight resolution.
- **Real-Time Updates**: Schedule and clock refresh every second with 50 ms input polling and 200 ms debounce for responsive controls.
- **RetroArch Friendly**: Cleans up GPIO before launching RetroArch games and relies on systemd to restart the display after you exit a game.

## Future Enhancements

- A/B day toggle in the settings menu.
- Custom color themes.
- Network time synchronization.
- Weather display and additional widgets.
- Multiple schedule profiles.
- Timer/stopwatch mode and progress bar visual.

## Auto-Start on Boot

To automatically start the schedule display when the Pi boots:

### Option 1: systemd service (recommended)

Copy the included service file and enable it:

```bash
sudo cp schedule-display.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable schedule-display.service
sudo systemctl start schedule-display.service
```

Check status:
```bash
sudo systemctl status schedule-display.service
```

View logs:
```bash
sudo journalctl -u schedule-display.service -f
```

**Note**: Edit the service file if your project is not in `/home/pi/schedule-display`.

### Option 2: rc.local

Add to `/etc/rc.local` (before `exit 0`):

```bash
cd /home/pi/schedule-display && sudo python3 main.py &
```

## RetroArch Games Menu

### Prerequisites

- RetroArch and the needed libretro cores (e.g., `prboom_libretro.so`, `fceumm_libretro.so`).
- ROMs placed under `/home/pi/roms` (or override via the `GAME_ROM_DIR` env var).
- Cores in `/usr/lib/libretro` (or override via `RETROARCH_CORE_DIR`).

### Usage

1. Copy the curated ROMs (Doom, Tetris) into your ROM directory.
2. Launch `sudo python3 main.py` (or use the systemd service).
3. Navigate to **Games** and select either Tetris or Doom—the app will clean up GPIO, launch RetroArch with the appropriate core, and return you to the menu when the game exits.

### How It Works

- The menu delegates to `games_config.py`, which builds `retroarch -L <core> <rom>` calls for approved games.
- Input is re-initialized after each game so the schedule display continues responding.

## Troubleshooting

### Blank Screen
- Verify SPI is enabled: `ls /dev/spi*` (should show `/dev/spidev0.0` and `/dev/spidev0.1`)
- Make sure you're running with `sudo`
- Check connections on the HAT

### GPIO Errors
- Make sure you have `rpi-lgpio` installed (not old `RPi.GPIO`)
- Add your user to gpio group: `sudo usermod -aG gpio $USER` then reboot
- If you edited scripts on Windows, run `dos2unix *.sh` to avoid stray CRLF characters before launching.

### RetroPie Not Launching
- Make sure EmulationStation is installed: `which emulationstation`
- Install RetroPie: https://retropie.org.uk/docs/Manual-Installation/

## License

MIT
