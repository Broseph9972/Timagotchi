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
#sudo apt install -y libretro-common || echo "Warning: libretro-common package not available"

echo "Installing Python dependencies..."
pip3 install --break-system-packages pillow numpy spidev RPi.GPIO

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
SCRIPT_DIR="$HOME/Timagotchi/Code"

echo "Script directory: $SCRIPT_DIR"

# Create systemd service file - use 'cat' with quoted heredoc to avoid variable expansion issues
sudo tee /etc/systemd/system/timagotchi.service > /dev/null <<SERVICEFILE
[Unit]
Description=Timagotchi Schedule Display
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$SCRIPT_DIR
ExecStart=$SCRIPT_DIR/start.sh
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

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
echo "Installation complete!"
echo "Reboot required for GPIO permissions and autostart."
echo ""
echo "To run manually:"
echo "  cd $SCRIPT_DIR && ./start.sh"
echo "Made by Jqseph9972"
echo ""