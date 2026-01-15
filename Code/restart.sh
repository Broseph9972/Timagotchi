#!/bin/bash

# Restart script for Timagotchi program

# Try systemd service first
if systemctl is-active --quiet schedule-display.service; then
    echo "Restarting via systemd service..."
    sudo systemctl restart schedule-display.service
    echo "Service restarted."
else
    echo "Systemd service not active. Restarting manually..."
    
    # Kill any running instances
    pkill -f "python3.*main.py" 2>/dev/null
    
    # Wait a moment
    sleep 1
    
    # Get the script directory
    SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
    
    # Start main.py
    cd "$SCRIPT_DIR"
    sudo python3 main.py &
    
    echo "Program restarted in background."
fi
