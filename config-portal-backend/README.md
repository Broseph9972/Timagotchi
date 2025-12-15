# Timagotchi Configuration Portal - Backend

Cloud-hosted web interface for configuring Timagotchi devices via pairing codes.

## Overview

This Flask application provides a web-based configuration portal that pairs with Timagotchi devices using simple 5-digit codes. Users configure their schedule, Canvas LMS integration, WiFi networks, themes, and custom phrases through a modern web interface instead of running command-line scripts.

## Features

- **5-digit pairing codes** - Simple numeric codes for device pairing
- **One-time use codes** - Codes expire after successful configuration or 1 hour timeout
- **Complete configuration** - Schedule, Canvas LMS, WiFi, themes, custom phrases
- **Modern web UI** - Responsive design with step-by-step wizard
- **Polling mechanism** - Pi polls backend; no complex networking required
- **In-memory storage** - Lightweight, no database needed

## Deployment

### Option 1: Render (Recommended)

1. Fork or clone the Timagotchi repository
2. Create a new Web Service on [Render](https://render.com)
3. Connect your GitHub repository
4. Configure the service:
   - **Root Directory**: `config-portal-backend`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
   - **Environment**: Python 3
5. Deploy!

Your portal will be available at: `https://your-app-name.onrender.com`

### Option 2: Railway

1. Install Railway CLI: `npm i -g @railway/cli`
2. Navigate to `config-portal-backend` directory
3. Run: `railway login`
4. Run: `railway init`
5. Run: `railway up`
6. Run: `railway open` to view deployment

### Option 3: Heroku

1. Install Heroku CLI
2. Navigate to `config-portal-backend` directory
3. Login: `heroku login`
4. Create app: `heroku create timagotchi-config`
5. Deploy: `git push heroku main`

### Option 4: Self-Hosted (VPS/Cloud)

```bash
# Clone repository
git clone https://github.com/broseph9972/Timagotchi
cd Timagotchi/config-portal-backend

# Install dependencies
pip install -r requirements.txt

# Run with Gunicorn (production)
gunicorn -w 4 -b 0.0.0.0:5000 app:app

# Or run with Flask (development)
python app.py
```

**Note**: For production, use a process manager like systemd, supervisor, or PM2.

## Configuration on Pi

After deploying the backend, configure the Pi to use your deployment URL:

### Method 1: Environment Variable (Recommended)

Add to `/etc/environment` or your shell profile:

```bash
export TIMAGOTCHI_API_URL="https://your-deployment-url.com"
```

### Method 2: Edit config_portal.py

Edit `Code/config_portal.py` and change:

```python
API_BASE_URL = "https://your-deployment-url.com"
```

## API Endpoints

### `POST /api/generate-code`
Generate a new 5-digit pairing code.

**Response:**
```json
{
  "code": "12345",
  "expires_in": 3600
}
```

### `GET /api/validate-code/<code>`
Check if a code is valid and available.

**Response:**
```json
{
  "valid": true,
  "time_remaining": 3240
}
```

### `POST /api/config/<code>`
Submit configuration for a pairing code.

**Request Body:**
```json
{
  "schedule": {
    "school_start": "09:05",
    "school_end": "15:55",
    "num_periods": 6,
    "period_length": 51,
    "passing_time": 4,
    "has_advisory": true,
    "advisory_start": "09:20",
    "advisory_length": 36,
    "advisory_days": "m,t",
    "has_lunch": true,
    "lunch_start": "13:40",
    "lunch_end": "14:05",
    "use_ab_day": true,
    "ab_day_mode": "auto"
  },
  "system": {
    "timezone": "America/New_York",
    "time_sync_mode": "on_boot",
    "use_24_hour": false,
    "wifi_networks": [
      ["SSID1", "password1"],
      ["SSID2", "password2"]
    ]
  },
  "canvas": {
    "enabled": true,
    "base_url": "https://school.instructure.com",
    "api_token": "1234~xxxxx"
  },
  "customization": {
    "theme": "dark",
    "phrases": {
      "passing": ["Almost there!", "Quick break!"],
      "lunch": ["Time to eat!", "Lunch break!"]
    }
  }
}
```

### `GET /api/config/<code>`
Pi polls this endpoint to retrieve configuration.

**Responses:**
- `202 Accepted` - Configuration pending (not submitted yet)
- `200 OK` - Configuration ready (includes config JSON)
- `404 Not Found` - Invalid or expired code

### `GET /health`
Health check endpoint for monitoring.

**Response:**
```json
{
  "status": "healthy",
  "active_codes": 3,
  "timestamp": "2025-12-15T10:30:00"
}
```

## Usage Flow

### First Boot (No config.py)

1. Pi boots up and detects no `config.py`
2. Pi requests a pairing code from backend: `POST /api/generate-code`
3. Pi displays code on screen and starts polling
4. User visits portal website
5. User enters 5-digit code
6. Website validates code: `GET /api/validate-code/<code>`
7. User fills out configuration form
8. Website submits config: `POST /api/config/<code>`
9. Pi receives config on next poll: `GET /api/config/<code>`
10. Pi writes config files and restarts

### Manual Reconfiguration

1. User navigates to Settings → Configuration Portal
2. Same flow as first boot, but Pi is already running
3. After successful configuration, Pi restarts to apply changes

## Security Considerations

This system is designed for **simplicity**, not high security:

- Codes are random 5-digit numbers (100,000 combinations)
- Codes expire after 1 hour
- Codes are one-time use
- In-memory storage (cleared on restart)
- No authentication required

**For home/school use, this provides adequate security.** For production/commercial use, consider:
- HTTPS (required for production)
- Rate limiting
- Longer/alphanumeric codes
- Database with encryption
- User authentication

## Development

### Local Testing

```bash
# Install dependencies
pip install -r requirements.txt

# Run development server
python app.py
```

Visit `http://localhost:5000` to test the web interface.

### Testing with Pi

Update `config_portal.py` to use local URL:

```python
API_BASE_URL = "http://192.168.1.100:5000"  # Your computer's local IP
```

Or set environment variable:

```bash
export TIMAGOTCHI_API_URL="http://192.168.1.100:5000"
```

## Troubleshooting

### Pi Shows "Connection Error"

- Check internet connectivity on Pi
- Verify `TIMAGOTCHI_API_URL` is set correctly
- Ensure backend is deployed and accessible
- Check firewall/network settings

### Code Invalid or Expired

- Codes expire after 1 hour
- Codes are one-time use
- Server restart clears all codes (in-memory storage)
- Request a new code from Pi

### Configuration Not Syncing

- Ensure Pi is polling (should show "Waiting...")
- Check backend logs for errors
- Verify code was entered correctly on website
- Try refreshing/restarting Pi

### Backend Crashes/Restarts

In-memory storage is cleared on restart. Active pairing sessions will fail. Users should:
1. Press any button on Pi to cancel current pairing
2. Re-enter Configuration Portal menu
3. Get a new code and try again

## License

Part of the Timagotchi project. See main repository LICENSE.

## Contributing

Issues and pull requests welcome! Please test thoroughly before submitting.
