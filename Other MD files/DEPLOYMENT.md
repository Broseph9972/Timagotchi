# Deployment Guide for Raspberry Pi Zero WH w/ pi os 32bit
## How to Deploy

### 1. Transfer Files to Your Raspberry Pi

From your development machine, copy the project to your Pi:

```bash
# Using scp
scp -r . pi@raspberrypi.local:/home/pi/schedule-display

# Or using git
# On the Pi:
cd ~
git clone <your-repo-url> schedule-display
```

### 2. Run the Installation Script

```bash
cd /home/pi/schedule-display
chmod +x install.sh
./install.sh
```

### 3. Configure Your Schedule

```bash
python3 configure_schedule.py
```

Or manually edit `config.py` with your schedule details.

### 4. Test the Application

```bash
./start.sh
```

Use the joystick to navigate:
- Up/Down: Navigate menu
- Press/Right: Select
- Left/Key1: Back to main menu

### 5. Enable Auto-Start (Optional)

To have the schedule display start automatically when the Pi boots:

```bash
sudo cp schedule-display.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable schedule-display.service
sudo systemctl start schedule-display.service
```

## RetroPie Integration

If you have RetroPie installed:

1. The systemd service will start the schedule display on boot
2. Navigate to "Launch RetroPie" in the menu to start EmulationStation
3. When you exit EmulationStation, the systemd service will automatically restart the schedule display

## Hardware Requirements

- Raspberry Pi Zero WH (or any Pi model with GPIO)
- Waveshare 1.44" LCD HAT (https://www.waveshare.com/1.44inch-lcd-hat.htm)
  - ST7735S display controller
  - 128x128 pixel resolution
  - 5-way joystick + 3 buttons
- Raspberry Pi OS (Bookworm or later recommended)
- SPI interface enabled

## Troubleshooting

See README.md for common issues and solutions.
