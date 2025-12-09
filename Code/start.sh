#!/bin/bash

cd "$(dirname "$0")"

echo "Pi Schedule Display - Starting..."
echo "Press Ctrl+C to exit"
echo ""

# Run with sudo if not already root
if [ "$EUID" -ne 0 ]; then
  sudo python3 main.py
else
  python3 main.py
fi
