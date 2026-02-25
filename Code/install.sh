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
sudo apt install -y python3-pip python3-pil python3-numpy
sudo apt install -y chocolate-doom xvfb xdotool || echo "Note: Doom packages optional"
#sudo apt install -y libretro-common || echo "Warning: libretro-common package not available"

echo "Installing Python dependencies..."
pip3 install --break-system-packages pillow numpy spidev RPi.GPIO requests pygame mss Cython

# Waveshare LCD driver download requires git
# Uncomment and install git if needed:
# echo "Downloading Waveshare LCD driver..."
# git clone --depth 1 https://github.com/waveshare/LCD_1in44.git /tmp/LCD_1in44
# echo "Installing Waveshare LCD driver..."
# cd /tmp/LCD_1in44/python
# sudo python3 setup.py install
# echo "Cleaning up..."
# cd ~
# rm -rf /tmp/LCD_1in44

echo "Adding user to gpio group..."
sudo usermod -aG gpio $USER

echo "Configuring sudoers for timedatectl..."
# Allow pi user to run timedatectl without password
echo "$USER ALL=(ALL) NOPASSWD: /usr/bin/timedatectl" | sudo tee /etc/sudoers.d/timagotchi-timedatectl > /dev/null
sudo chmod 0440 /etc/sudoers.d/timagotchi-timedatectl

echo "Preparing RetroArch ROM storage..."
sudo mkdir -p "$HOME/timagotchi/roms"
sudo chown $USER:$USER "$HOME/timagotchi/roms"

# PyDoom installation requires git (optional)
# Uncomment and install git if needed:
# echo "Installing PyDoom (optional Doom engine)..."
# PYDOOM_DIR="$(dirname "$(readlink -f "$0")")/pydoom"
# if [ -d "$PYDOOM_DIR" ]; then
#     echo "PyDoom directory already exists, skipping..."
# else
#     git clone --depth 1 https://github.com/Pink-Silver/PyDoom.git "$PYDOOM_DIR" || echo "Warning: PyDoom clone failed (optional)"
#     if [ -d "$PYDOOM_DIR" ]; then
#         echo "PyDoom cloned successfully. Place doom1.wad in Code/pydoom/ to use."
#     fi
# fi

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

# Install splash-animated.service
echo "Installing Splash screen service..."
sudo tee /etc/systemd/system/splash-animated.service > /dev/null <<SPLASHFILE
[Unit]
Description=Timagotchi Animated Splash Screen
After=network.target
Before=timagotchi.service

[Service]
Type=oneshot
User=root
Group=root
WorkingDirectory=$SCRIPT_DIR
ExecStart=/usr/bin/python3 $SCRIPT_DIR/splash_animated.py
Restart=no
RemainAfterExit=no
StandardOutput=journal
StandardError=journal
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
SPLASHFILE

# Fix permissions on splash service file
sudo chmod 644 /etc/systemd/system/splash-animated.service

# Enable and reload
sudo systemctl daemon-reload
sudo systemctl enable splash-animated.service
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
echo "Made by Jqseph9972/Broseph9972"
echo ""