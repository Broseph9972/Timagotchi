# Timagotchi
![Pic of it working](https://github.com/Broseph9972/Timagotchi/blob/8dd138669abf655206ba47d0e1635b271fd48dee/WIN_20251119_20_47_22_Pro.jpg)
![Pic of it working 2](https://github.com/Broseph9972/Timagotchi/blob/8dd138669abf655206ba47d0e1635b271fd48dee/WIN_20251106_21_18_16_Pro.jpg)
A school schedule display system for Raspberry Pi Zero WH with Waveshare 1.44" LCD HAT.
## LOTS OF CODE IS AI
## Overview
This project is a pi zero scheduler that tells u how much time u have left in school
## Features

- **Schedule View**: Shows what period ur in and how much time left( i want to add a progress bar)
- **Clock View**: its a clock. it shows time and date.
- **Menu System**: crappy menu ill change later
- **RetroArch Games Menu**: DOES NOT WORK YET but i have retroarch working and i will add later
- **Joystick & Buttons**: Full 5-way joystick plus three extra buttons for shortcuts/back navigation.
- **Systemd-Friendly**: Service file included for clean auto-start and restart after RetroPie exits.

## Target Hardware

- **Board**: Raspberry Pi Zero WH
- **Display**: Waveshare 1.44" LCD HAT
- **Operating System**: Raspberry Pi OS (tested on Bookworm)
- **(Not required) Battery**: Battery or battery bank w/ cable

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
- `configure_schedule.py` – makes ur config.json for u
- `schedule-display.service` – systemd unit for auto-start/restart.
- `install.sh` / `start.sh` – automated scripts
- `old code/` – old code w/ drivers and stuff, duct taped together

## Dependencies

### Python Packages
- `st7735>=0.2.0` – ST7735S display driver (128x128 LCD).
- `pillow>=10.0.0` – Image rendering and fonts.
- `numpy>=1.24.0` – Numerical helpers for drawing.
- `spidev>=3.6` – SPI communication.
- `rpi-lgpio>=0.4` – GPIO access on Raspberry Pi OS Bookworm.
- `lgpio>=0.2.2.0` – Low-level GPIO interface used when RPi.GPIO is unavailable.

### System Requirements
Root access
internet
basic knowledge

## Installation

### Automated Installation

```bash
chmod +x install.sh
./install.sh
```

**If install.sh and start.sh wont run, try ```dos2unix install.sh start.sh``` this happens when i sftp it over.


This will:
- Check if SPI is enabled
- Install system dependencies
- Install Python packages
- Add your user to the GPIO group

**Important**: Reboot after install.

### Manual Installation

#### 1. Enable SPI Interface

```bash
sudo raspi-config
```

Navigate to: **Interfacing Options → SPI → Yes**, then reboot. this is the screen to work

#### 2. Install Dependencies

```bash
sudo apt-get update
sudo apt-get install python3-pip python3-pil python3-numpy
pip3 install -r requirements.txt
```

#### 3. Do gpio stuff

```bash
sudo usermod -aG gpio [Your username]
```


#### 4. Configure Your Schedule

i made a script that does this for u, but it's made for my school system specifically, so feel free to edit and commit if u want. You can also edit manually, its just json.

```bash
python3 configure_schedule.py
```

## Usage

### Run Manually

```bash
sudo python3 main.py
```

### Controls

#### Joystick
its a joystick, it moves stuff. middle click is ok as well but rlly hard to use so just use key3

#### Buttons (not all implemented yet)
- **Key1**: Quick back to the main menu.
- **Key2**: Check grades
- **Key3**: OK

_All joystick directions and buttons are active-low with pull-ups enabled._

### Menu Options

1. **Schedule**: View current class and time until ___
2. **Clock**: View current time and date
3. **Settings**: its a settings menu
4. **Games**: opens retroarch launcher
5. **Exit**: closes it (shutdown)

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

## TODO

- A/B day toggle in the settings menu.
- Custom color themes.
- Network time synchronization.
- Weather display and additional widgets.
- Multiple schedule profiles.
- Timer/stopwatch mode and progress bar visual.
- check grades via canvas

### auto start w/ systemd service

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

## Troubleshooting

### Blank Screen
- Verify SPI is enabled: `ls /dev/spi*` (should show `/dev/spidev0.0` and `/dev/spidev0.1`)
- Make sure you're running with `sudo`
- Check connections on the HAT
