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
sudo apt install -y python3-pip python3-pil python3-numpy git retroarch retroarch-assets
#sudo apt install -y libretro-common || echo "Warning: libretro-common package not available"

echo "Installing Python dependencies..."
pip3 install --break-system-packages pillow numpy spidev RPi.GPIO

echo "Building RetroArch cores (prboom-libretro, fceumm-libretro)..."
sudo apt install -y git build-essential cmake libsdl2-dev

CORE_BUILD_DIR=$(mktemp -d)
CORE_DEST_DIR="$HOME/.config/retroarch/cores"
mkdir -p "$CORE_DEST_DIR"

echo "Cloning and building prboom-libretro (Doom core)..."
cd "$CORE_BUILD_DIR"
git clone https://github.com/libretro/prboom-libretro.git
cd prboom-libretro
make -j2 || echo "Warning: prboom-libretro build failed"
if [ -f prboom_libretro.so ]; then
    cp prboom_libretro.so "$CORE_DEST_DIR/"
fi

echo "Cloning and building fceumm-libretro (NES core)..."
cd "$CORE_BUILD_DIR"
git clone https://github.com/libretro/fceumm.git
cd fceumm
make -j2 || echo "Warning: fceumm-libretro build failed"
if [ -f fceumm_libretro.so ]; then
    cp fceumm_libretro.so "$CORE_DEST_DIR/"
fi

cd ~
rm -rf "$CORE_BUILD_DIR"

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

echo "Preparing RetroArch ROM storage..."
sudo mkdir -p /home/pi/timagotchi/roms
sudo chown pi:pi /home/pi/timagotchi/roms

echo ""
echo "Setting up autostart service..."

# Get the directory where start.sh is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Create systemd service file
sudo tee /etc/systemd/system/timagotchi.service > /dev/null <<EOF
[Unit]
Description=Timagotchi Schedule Display
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=$SCRIPT_DIR
ExecStart=$SCRIPT_DIR/start.sh
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start the service
sudo systemctl daemon-reload
sudo systemctl enable timagotchi.service

echo "Autostart service installed!"
echo "To start: sudo systemctl start timagotchi"
echo "To stop: sudo systemctl stop timagotchi"
echo "To view logs: sudo journalctl -u timagotchi -f"

echo ""
echo "Installation complete!"
echo "Reboot required for GPIO permissions and autostart."
echo ""
echo "To run manually:"
echo "  ./start.sh"
echo "Made by Jqseph9972"
echo ""