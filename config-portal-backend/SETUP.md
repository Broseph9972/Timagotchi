# Configuration Portal Setup Guide

Quick guide to get your Timagotchi Configuration Portal up and running.

## For Website Deployment

### Quick Deploy to Render (5 minutes)

1. **Sign up** for free account at [render.com](https://render.com)

2. **Click "New +"** → "Web Service"

3. **Connect Repository**:
   - Connect your GitHub account
   - Select `Timagotchi` repository
   - Or use public repo: `https://github.com/broseph9972/Timagotchi`

4. **Configure Service**:
   ```
   Name: timagotchi-config (or your choice)
   Root Directory: config-portal-backend
   Environment: Python 3
   Build Command: pip install -r requirements.txt
   Start Command: gunicorn app:app
   ```

5. **Deploy!** - Wait 2-3 minutes for build to complete

6. **Copy URL** - e.g., `https://timagotchi-config.onrender.com`

### Alternative: Railway (3 minutes)

```bash
cd config-portal-backend
npx @railway/cli login
npx @railway/cli init
npx @railway/cli up
```

## For Raspberry Pi Setup

### Option 1: Environment Variable (Recommended)

```bash
# Edit environment file
sudo nano /etc/environment

# Add this line (use YOUR deployed URL):
TIMAGOTCHI_API_URL=https://timagotchi-config.onrender.com

# Save (Ctrl+O, Enter, Ctrl+X)
# Reboot
sudo reboot
```

### Option 2: Edit Code Directly

```bash
cd ~/Timagotchi/Code
nano config_portal.py

# Find this line:
API_BASE_URL = os.environ.get('TIMAGOTCHI_API_URL', 'https://timagotchi-config.herokuapp.com')

# Change to:
API_BASE_URL = 'https://timagotchi-config.onrender.com'  # Your URL here

# Save and exit
```

## First Time Setup

### On First Boot (No config.py exists)

1. **Pi boots** → Shows "Configuration Portal" screen with 5-digit code
2. **Visit website** on your phone/computer: `https://timagotchi-config.onrender.com`
3. **Enter code** displayed on Pi
4. **Fill out form**:
   - Schedule (school hours, periods, etc.)
   - Canvas LMS (optional)
   - WiFi networks
   - Theme and customization
5. **Submit** → Pi syncs automatically in ~5 seconds
6. **Pi restarts** with new configuration

### Manual Reconfiguration (Pi Already Set Up)

1. **Navigate**: Main → Settings → Configuration Portal
2. **Get new code** displayed on screen
3. **Visit website** and enter code
4. **Update settings** as needed
5. **Submit** → Pi syncs and restarts

## Testing the System

### Test Backend (Before Pi Setup)

```bash
# Test if backend is live
curl https://your-url.com/health

# Should return:
# {"status":"healthy","active_codes":0,"timestamp":"..."}
```

### Test Pairing Flow

1. **Generate code manually**:
   ```bash
   curl -X POST https://your-url.com/api/generate-code
   # Returns: {"code":"12345","expires_in":3600}
   ```

2. **Visit website** and enter that code

3. **Fill out form** and submit

4. **Check if config received**:
   ```bash
   curl https://your-url.com/api/config/12345
   # Should return configuration JSON or {"status":"pending"}
   ```

## Common Issues

### "Connection Error" on Pi

**Causes:**
- No internet connection
- Wrong API URL
- Backend is down

**Fix:**
```bash
# Check internet
ping -c 3 google.com

# Check API URL
echo $TIMAGOTCHI_API_URL

# Test backend
curl https://your-url.com/health
```

### Code Expired

**Cause:** Codes expire after 1 hour

**Fix:** Get a new code (any button to cancel, then re-enter portal)

### Website Says "Invalid Code"

**Causes:**
- Typo in code
- Code already used
- Backend restarted (clears memory)

**Fix:** Get fresh code from Pi

### Pi Not Syncing

**Cause:** Pi polls every 3 seconds; may take up to 5 seconds after submission

**Fix:** Wait 10 seconds. If still not syncing:
1. Check backend logs (Render dashboard → Logs)
2. Verify code on Pi matches code on website
3. Try cancelling and restarting

## Environment Variables

### Backend (Optional)

```bash
# Port (default: 5000, Render/Heroku auto-set this)
PORT=5000

# CORS origins (default: all allowed)
CORS_ORIGINS=https://yourdomain.com
```

### Pi (Required)

```bash
# Set in /etc/environment or ~/.bashrc
export TIMAGOTCHI_API_URL=https://your-backend-url.com
```

## Customization

### Change Code Length

Edit `config-portal-backend/app.py`:

```python
# Line ~21
def generate_code():
    # Change 10000-99999 for 5 digits
    # Use 100000-999999 for 6 digits
    code = str(random.randint(10000, 99999))
    return code
```

### Change Code Timeout

Edit `config-portal-backend/app.py`:

```python
# Line ~17
CODE_TIMEOUT_SECONDS = 3600  # 1 hour default
# Change to 1800 for 30 minutes, 7200 for 2 hours, etc.
```

### Add Custom Themes

Edit `Code/themes.json` and add new theme definition. Website will automatically show new themes in theme selector.

## Next Steps

1. **Deploy backend** using Render/Railway
2. **Configure Pi** with backend URL
3. **Test pairing** on first boot or via settings
4. **Share your URL** with other Timagotchi users (if desired)

For detailed API documentation and troubleshooting, see [README.md](README.md).
