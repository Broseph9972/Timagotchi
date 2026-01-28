# Installation Guide

## Automated Installation (Recommended)

### Prerequisites

- Fresh Raspberry Pi OS installation (32-bit, Bookworm or Trixie)
- SSH access or direct terminal
- Waveshare 1.44" LCD HAT properly seated

### Installation Steps

1. **Enable SPI Interface**

   ```bash
   sudo raspi-config
   ```
   
   - Go to **Interfacing Options → SPI → Yes**
   - Select **Yes** when asked
   - Reboot when prompted

2. **Clone Repository**

   ```bash
   git clone https://github.com/Broseph9972/Timagotchi
   cd Timagotchi/Code
   ```

3. **Run Installation Script**

   ```bash
   chmod +x install.sh start.sh
   ./install.sh
   ```

   If scripts won't run, try:
   ```bash
   dos2unix install.sh start.sh
   ```

4. **Reboot**

   ```bash
   sudo reboot
   ```

## Manual Installation

### 1. Dependencies

```bash
sudo apt-get update
sudo apt-get install python3-pip python3-pil python3-numpy
pip3 install -r requirements.txt
```

### 2. GPIO Configuration

```bash
sudo usermod -aG gpio $USER
```

### 3. Schedule Configuration

```bash
python3 configure_schedule.py
```

### 4. Canvas Setup (Optional)

Create `Code/canvas_config.json`:

```json
{
  "base_url": "https://yourschool.instructure.com",
  "api_token": "your_canvas_api_token_here"
}
```

To get a Canvas API token:
1. Log into Canvas
2. Account → Settings → New Access Token
3. Copy token to the config file

## Auto-Start with systemd

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
