# Getting Started

## Requirements

- Raspberry Pi Zero WH
- Waveshare 1.44" LCD HAT
- Raspberry Pi OS (Bookworm or Trixie)
- Internet connection for Canvas integration (optional)

## Quick Setup

### 1. Enable SPI Interface

```bash
sudo raspi-config
```

Navigate to: **Interfacing Options → SPI → Yes**, then reboot.

### 2. Install Timagotchi

```bash
git clone https://github.com/Broseph9972/Timagotchi && cd Timagotchi/Code
chmod +x install.sh start.sh
./install.sh
```

### 3. Configure Your Schedule

```bash
python3 configure_schedule.py
```

### 4. Reboot

```bash
sudo reboot
```

The system should auto-start. If not, run:

```bash
sudo python3 main.py
```

## First Run

On first startup, you'll be guided through:
- Theme selection
- Schedule configuration
- Canvas API token setup (optional)

## Next Steps

- [Features](features.md) - Learn what Timagotchi can do
- [Usage](usage.md) - Control and navigation guide
- [Customization](customization.md) - Themes, phrases, and custom scripts
