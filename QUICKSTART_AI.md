# Quick Start: AI-Powered Configuration

Get your Timagotchi configured in under 5 minutes using AI!

## What You Need

1. A photo of your school schedule (from handbook, website, or planner)
2. A free Gemini AI API key
3. Your Timagotchi device powered on

## Step-by-Step Guide

### 1. Deploy the Web Portal

Choose one of these free hosting options:

**Option A: Render (Recommended)**
1. Fork this repository
2. Go to [render.com](https://render.com) and sign up
3. Create a new Web Service
4. Connect your GitHub repo
5. Set root directory: `web`
6. Build command: `pip install -r requirements.txt`
7. Start command: `gunicorn app:app`
8. Add environment variable: `GEMINI_API_KEY` = your key
9. Deploy

**Option B: Local Testing**
```bash
cd web
export GEMINI_API_KEY='your-key-here'
pip install -r requirements.txt
python app.py
```

### 2. Get Your Free API Key

1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with Google
3. Click "Create API Key"
4. Copy the key
5. Add to your deployment's environment variables

**Free Tier Limits:**
- 60 requests/minute
- 1,500 requests/day
- No credit card required

### 3. Take a Photo of Your Schedule

**Tips for Best Results:**
- Good lighting
- Clear, focused text
- Include all periods and times
- Flat (no curves or wrinkles)
- Fill the frame with the schedule

**Works With:**
- School handbooks
- Website screenshots
- Printed schedules
- Student planners
- Bell schedule posters

### 4. Configure Your Device

1. Power on your Timagotchi
2. If no config exists, it will show a 5-digit pairing code
3. Visit your web portal
4. Click "Use AI Configurator"
5. Upload your schedule photo
6. Wait for AI analysis (5-10 seconds)
7. Review extracted information
8. Answer any questions the AI asks
9. Add Canvas LMS info if you want grades (optional)
10. Add WiFi networks
11. Enter your device's pairing code
12. Click "Send to Timagotchi"

### 5. Device Syncs Automatically

Your Timagotchi will:
- Download the configuration
- Write config.py file
- Restart automatically
- Start displaying your schedule

## Example Workflow

```
User uploads photo:
┌─────────────────────┐
│  School Schedule    │
│  Period 1: 8:00 AM  │
│  Period 2: 8:50 AM  │
│  Lunch: 12:00 PM    │
│  ...                │
└─────────────────────┘
         ↓
    AI analyzes
         ↓
┌─────────────────────┐
│ Extracted Info:     │
│ - Start: 08:00      │
│ - 7 periods         │
│ - Lunch: 12:00      │
│ - A/B day: Yes      │
└─────────────────────┘
         ↓
    User confirms
         ↓
   Config generated
         ↓
  Sent to device
         ↓
    Device syncs!
```

## Troubleshooting

### AI Can't Read Schedule

**Problem:** Blurry photo or AI misreads text

**Solutions:**
- Retake photo with better lighting
- Use landscape orientation
- Zoom in on schedule
- Try manual configuration instead

### Pairing Code Invalid

**Problem:** "Invalid or expired code" error

**Solutions:**
- Codes expire after 1 hour
- Request a new code from device
- Check you entered the 5 digits correctly

### Missing Information

**Problem:** AI couldn't extract some details

**Solutions:**
- Use the chat to ask AI specific questions
- Fill in missing details manually
- Verify uncertain items marked by AI

### No API Key

**Problem:** "AI service not configured"

**Solutions:**
- Set GEMINI_API_KEY environment variable
- Restart the web server
- Check API key is valid
- Use manual configuration as fallback

## What Gets Configured

The AI extracts and configures:

- ✓ School start and end times
- ✓ Number of periods
- ✓ Period start times
- ✓ Period names/subjects
- ✓ Period length
- ✓ Passing time
- ✓ Lunch period
- ✓ Advisory/homeroom
- ✓ A/B day scheduling
- ✓ Free periods

You provide:
- WiFi networks
- Canvas LMS credentials
- Timezone
- Display preferences

## Privacy & Security

- Images sent to Google's Gemini API for analysis
- Images not stored after analysis
- Config data temporary (1 hour expiry)
- Use HTTPS in production
- Keep API key secret

## Manual Configuration Fallback

If AI doesn't work for your schedule:
1. Use the "Manual Configuration" option
2. Fill out the detailed form
3. Works without API key
4. Complete control over all settings

## Next Steps

After configuration:
- Customize themes in Settings
- Add Canvas API token on device
- Set up custom phrases
- Explore the built-in games

## Getting Help

- Check `web/AI_CONFIG_README.md` for detailed docs
- See `web/README.md` for web portal info
- Open an issue on GitHub
- Check existing issues/discussions

## Cost

**Everything is FREE:**
- Gemini AI: Free tier (1,500 requests/day)
- Hosting: Free on Render/Railway/Heroku
- No credit card required
- No hidden fees

Enjoy your AI-configured Timagotchi!
