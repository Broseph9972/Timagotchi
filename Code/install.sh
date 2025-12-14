#!/bin/bash

echo "Installing Pi Schedule Display dependencies..."

echo "Checking if SPI is enabled..."
if ! ls /dev/spidev* &> /dev/null; then
    echo "ERROR: SPI is not enabled!"
    echo "Enable it using: sudo raspi-config"
    echo "Interfacing Options -> SPI -> Yes"
    echo "Then reboot and run this again."
    exit 1
fi

echo "Installing system packages..."
sudo apt-get update
sudo apt install -y python3-pip python3-pil python3-numpy git
sudo apt install -y chocolate-doom xvfb xdotool || echo "Note: Doom packages optional"
#sudo apt install -y libretro-common || echo "Warning: libretro-common package not available"

echo "Installing Python dependencies..."
pip3 install --break-system-packages pillow numpy spidev RPi.GPIO requests pygame mss

echo "Downloading Waveshare LCD driver..."
GIT_TERMINAL_PROMPT=0 git clone --depth 1 https://github.com/waveshare/LCD_1in44.git /tmp/LCD_1in44

echo "Installing Waveshare LCD driver..."
cd /tmp/LCD_1in44/python
sudo python3 setup.py install

echo "Cleaning up..."
cd ~
rm -rf /tmp/LCD_1in44

echo "Adding user to gpio group..."
sudo usermod -aG gpio $USER

echo "Configuring sudoers for timedatectl..."
# Allow pi user to run timedatectl without password
echo "$USER ALL=(ALL) NOPASSWD: /usr/bin/timedatectl" | sudo tee /etc/sudoers.d/timagotchi-timedatectl > /dev/null
sudo chmod 0440 /etc/sudoers.d/timagotchi-timedatectl

echo "Preparing RetroArch ROM storage..."
sudo mkdir -p "$HOME/timagotchi/roms"
sudo chown $USER:$USER "$HOME/timagotchi/roms"

echo "Time synchronization can be configured in config.py"
echo "Set TIME_SYNC_MODE to: 'disabled', 'on_boot', or 'periodic'"

echo ""
echo "Setting up autostart service..."

# Set the default path for autostart
SCRIPT_DIR="/home/pi/Timagotchi/Code"

echo "Script directory: $SCRIPT_DIR"

# Create systemd service file - use 'cat' with quoted heredoc to avoid variable expansion issues
sudo tee /etc/systemd/system/timagotchi.service > /dev/null <<SERVICEFILE
[Unit]
Description=Timagotchi Schedule Display
After=network.target local-fs.target
Wants=network.target

[Service]
Type=simple
User=root
Group=root
WorkingDirectory=$SCRIPT_DIR
ExecStart=/usr/bin/python3 $SCRIPT_DIR/main.py
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
SERVICEFILE

# Fix permissions on service file
sudo chmod 644 /etc/systemd/system/timagotchi.service

# Enable and reload
sudo systemctl daemon-reload
sudo systemctl enable timagotchi.service

# Verify service is enabled
if sudo systemctl is-enabled timagotchi.service &> /dev/null; then
    echo "✓ Autostart service enabled successfully"
    echo "✓ Service path: $SCRIPT_DIR/start.sh"
else
    echo "✗ WARNING: Service may not be properly enabled"
fi

echo "Autostart service installed!"
echo "To start: sudo systemctl start timagotchi"
echo "To stop: sudo systemctl stop timagotchi"
echo "To view logs: sudo journalctl -u timagotchi -f"

echo ""
echo "Setting up optional Canvas config (press Enter to skip)"
read -p "Canvas base URL (e.g., https://aacps.instructure.com): " CANVAS_URL
read -p "Canvas API token (e.g., 27449~xxxxx): " CANVAS_TOKEN

if [ -n "$CANVAS_URL" ] && [ -n "$CANVAS_TOKEN" ]; then
    CFG_PATH="$SCRIPT_DIR/canvas_config.json"
    echo "{\"base_url\":\"$CANVAS_URL\",\"api_token\":\"$CANVAS_TOKEN\"}" > "$CFG_PATH"
    chmod 600 "$CFG_PATH"
    chown $USER:$USER "$CFG_PATH" 2>/dev/null || true
    echo "✓ Canvas config saved to $CFG_PATH (permissions 600)"
else
    echo "Skipping Canvas config creation. You can add Code/canvas_config.json later."
fi

echo "Installation complete!"
echo "Reboot required for GPIO permissions and autostart."
echo ""
echo "To run manually:"
echo "  cd $SCRIPT_DIR && ./start.sh"
echo "Made by Jqseph9972/Broseph9972"
echo ""