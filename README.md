# Pi Schedule Display

A school schedule display system for Raspberry Pi Zero WH with Waveshare 1.44" LCD HAT.

## Features

- **Schedule View**: Shows current period, class name, time remaining, lunch countdown, and end of day
- **Clock View**: Digital clock display
- **Settings**: Configure display preferences
- **RetroPie Integration**: Launch EmulationStation directly from the menu (requires FBCP setup)
- **Joystick Navigation**: Easy menu navigation with the HAT's 5-way joystick

## Hardware Requirements

- Raspberry Pi Zero WH (or any Raspberry Pi model)
- Waveshare 1.44" LCD HAT (ST7735S, 128x128 pixels)
- Raspberry Pi OS (tested on Bookworm)

## Installation

### Automated Installation (Recommended)

```bash
chmod +x install.sh
./install.sh
```

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

- **Joystick Up/Down**: Navigate menu
- **Joystick Press/Right**: Select menu item
- **Joystick Left/Key1**: Go back to main menu
- **Key2, Key3**: Reserved for future use

### Menu Options

1. **Schedule**: View current class schedule
2. **Clock**: View current time and date
3. **Settings**: Configure preferences
4. **Launch RetroPie**: Start EmulationStation (if installed)
5. **Exit**: Close the application

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

## RetroPie Integration

### Prerequisites

RetroPie integration requires FBCP (Framebuffer Copy) to mirror the display output to the LCD.

**See [FBCP_RETROPIE_SETUP.md](FBCP_RETROPIE_SETUP.md) for detailed setup instructions.**

### Quick Setup

1. Install and configure FBCP for the 1.44" LCD HAT
2. Configure `/boot/config.txt` for 128x128 HDMI output
3. The "Launch RetroPie" menu option will start EmulationStation
4. FBCP will mirror EmulationStation to the LCD
5. Exit EmulationStation to return to the schedule display

### How It Works

- Schedule app draws directly to LCD via SPI (no FBCP needed)
- When you select "Launch RetroPie", the schedule app exits
- EmulationStation starts and FBCP mirrors it to the LCD
- Systemd auto-restarts the schedule app when you exit EmulationStation

## Troubleshooting

### Blank Screen
- Verify SPI is enabled: `ls /dev/spi*` (should show `/dev/spidev0.0` and `/dev/spidev0.1`)
- Make sure you're running with `sudo`
- Check connections on the HAT

### GPIO Errors
- Make sure you have `rpi-lgpio` installed (not old `RPi.GPIO`)
- Add your user to gpio group: `sudo usermod -aG gpio $USER` then reboot

### RetroPie Not Launching
- Make sure EmulationStation is installed: `which emulationstation`
- Install RetroPie: https://retropie.org.uk/docs/Manual-Installation/

## License

MIT
