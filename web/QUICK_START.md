# 🎮 Timagotchi Configuration Portal - Quick Start

## For Users: How to Configure Your Timagotchi

### First Time Setup

1. **Boot your Timagotchi**
   - If no configuration exists, you'll see a code on screen

2. **Visit the portal website**
   - URL: `https://timagotchi-config.onrender.com` (or your deployed URL)
   - On phone or computer

3. **Enter the 5-digit code**
   - Type the code shown on your Timagotchi screen
   - Click Continue

4. **Fill out the form**
   
   **Step 1: Schedule**
   - School start/end times
   - Number of periods
   - Period length and passing time
   - Advisory (if applicable)
   - Lunch times (if applicable)
   - A/B day scheduling (if applicable)
   
   **Step 2: Canvas & WiFi**
   - Canvas LMS URL and API token (optional)
   - WiFi network names and passwords
   - Timezone
   - Time sync settings
   
   **Step 3: Customization**
   - Choose a theme (Dark, Light, Ocean, Forest, Sunset, Cyberpunk)
   - Add custom phrases (optional)
   
   **Step 4: Review**
   - Check all settings
   - Click "Send to Timagotchi"

5. **Wait for sync**
   - Your Timagotchi will sync automatically (5-10 seconds)
   - Screen will show "Success!" and restart

### Reconfigure Later

1. **On your Timagotchi:**
   - Navigate to: Main → Settings → Configuration Portal

2. **Get new code and repeat steps 2-5 above**

## For Developers: How to Deploy

### Quick Deploy (5 minutes)

1. **Go to [render.com](https://render.com)**
   - Sign up for free account

2. **New Web Service**
   - Connect GitHub: `broseph9972/Timagotchi`
   - Or your fork

3. **Configure:**
   ```
   Name: timagotchi-config
   Root Directory: config-portal-backend
   Build Command: pip install -r requirements.txt
   Start Command: gunicorn app:app
   ```

4. **Deploy**
   - Wait 2-3 minutes
   - Copy your URL: `https://your-app.onrender.com`

5. **Configure Pi:**
   ```bash
   sudo nano /etc/environment
   # Add:
   TIMAGOTCHI_API_URL=https://your-app.onrender.com
   
   # Save and reboot
   sudo reboot
   ```

## Troubleshooting

### Pi shows "Connection Error"
- Check internet: `ping google.com`
- Check URL: `echo $TIMAGOTCHI_API_URL`
- Test backend: `curl https://your-url.com/health`

### Website says "Invalid Code"
- Code expired (1 hour timeout)
- Code already used
- Get new code from Pi

### Not syncing
- Wait 10 seconds
- Check code matches exactly
- Press any button to cancel and try again

## URLs & Links

- **GitHub Repo**: https://github.com/broseph9972/Timagotchi
- **Full Documentation**: See `config-portal-backend/README.md`
- **Setup Guide**: See `config-portal-backend/SETUP.md`
- **Implementation Details**: See `IMPLEMENTATION_SUMMARY.md`

## Support

- **Issues**: https://github.com/broseph9972/Timagotchi/issues
- **Discussions**: https://github.com/broseph9972/Timagotchi/discussions

---

**Need help?** Open an issue on GitHub or check the full documentation in the repo.
