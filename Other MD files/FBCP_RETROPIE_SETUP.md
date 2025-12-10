# FBCP Setup for RetroPie on 1.44" LCD HAT

To use RetroPie with the Waveshare 1.44" LCD HAT, you need to setup FBCP (Framebuffer Copy) to mirror the HDMI output to the SPI display.

## What is FBCP?

FBCP copies the primary framebuffer (HDMI output) to the secondary framebuffer (your LCD). This allows RetroPie's EmulationStation and games to display on the small LCD screen.

## Installation

### Step 1: Install Dependencies

```bash
sudo apt-get install cmake git
```

### Step 2: Download and Compile FBCP for Waveshare HAT

```bash
cd ~
git clone https://github.com/juj/fbcp-ili9341.git
cd fbcp-ili9341
mkdir build
cd build
```

### Step 3: Configure for 1.44" LCD HAT (ST7735S)

```bash
cmake -DWAVESHARE_ST7735S_HAT=ON \
      -DSPI_BUS_CLOCK_DIVISOR=20 \
      -DGPIO_TFT_DATA_CONTROL=25 \
      -DGPIO_TFT_RESET_PIN=27 \
      -DGPIO_TFT_BACKLIGHT=24 \
      -DSTATISTICS=0 \
      ..
```

### Step 4: Compile

```bash
make -j
```

This creates the `fbcp-ili9341` binary in the build directory.

## Configuration

### Edit /boot/config.txt

Add these lines to set the HDMI output resolution to match the LCD:

```bash
sudo nano /boot/config.txt
```

Add at the end:

```
# Force HDMI output
hdmi_force_hotplug=1

# Custom resolution for 128x128 LCD
hdmi_group=2
hdmi_mode=87
hdmi_cvt=128 128 60 1 0 0 0

# Disable vc4 driver (for Pi 4)
#dtoverlay=vc4-fkms-v3d
#max_framebuffers=2
```

**Important**: Comment out the vc4 overlay lines if they exist. FBCP doesn't work with the vc4 driver.

### Auto-Start FBCP on Boot

```bash
sudo nano /etc/rc.local
```

Add this line before `exit 0`:

```bash
sudo /home/pi/fbcp-ili9341/build/fbcp-ili9341 &
```

## RetroPie Integration

### Option 1: Dual Boot Menu (Recommended)

Keep the schedule display as default, with an option to launch RetroPie:

1. The schedule app starts on boot (via systemd service)
2. Use the menu to select "Launch RetroPie"
3. Schedule app exits and EmulationStation starts
4. FBCP mirrors it to the LCD
5. When you exit EmulationStation, systemd restarts the schedule app

### Option 2: RetroPie as Default

Start RetroPie on boot:

```bash
# Disable the schedule display service
sudo systemctl disable schedule-display.service

# RetroPie will auto-start if configured
```

You can still run the schedule display manually with `./start.sh`

## Testing

1. Reboot your Pi:
   ```bash
   sudo reboot
   ```

2. You should see:
   - Boot messages mirrored on the LCD
   - Your schedule display (if using Option 1)
   - Or EmulationStation (if using Option 2)

3. Test the joystick - it should work for both the schedule menu and RetroPie navigation

## Troubleshooting

### LCD shows nothing
- Check that SPI is enabled: `ls /dev/spi*`
- Verify FBCP is running: `ps aux | grep fbcp`
- Check `/boot/config.txt` settings

### Display is rotated wrong
Add to the cmake command:
```bash
-DDISPLAY_ROTATE_180_DEGREES=ON
```
Then recompile.

### Performance is slow
- Lower SPI speed: `-DSPI_BUS_CLOCK_DIVISOR=30` (higher = slower but more stable)
- Reduce framerate in /boot/config.txt: `hdmi_cvt=128 128 30 1 0 0 0` (30fps instead of 60)

### Buttons don't work in RetroPie
EmulationStation may need controller configuration:
- Press and hold any button to configure
- Map the joystick/buttons

## Performance Notes

- The 128x128 LCD is perfect for retro games (NES, Game Boy, etc.)
- More complex systems (N64, PSX) may be slow due to the low resolution rendering
- FBCP uses about 5-10% CPU on a Pi Zero

## Alternative: Direct Display (No FBCP)

If you only want the schedule display (no RetroPie mirroring):
- Skip FBCP installation
- The schedule app draws directly to the LCD via SPI
- Much lower CPU usage
- Can't display EmulationStation

## Resources

- FBCP-ili9341: https://github.com/juj/fbcp-ili9341
- RetroPie Docs: https://retropie.org.uk/docs/
- Waveshare Wiki: https://www.waveshare.com/wiki/1.44inch_LCD_HAT
