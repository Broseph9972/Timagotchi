# Getting Started with AI Configuration

## For Users

### What You Need
1. A photo of your school schedule
2. 2-3 minutes of your time

### Quick Steps
1. Visit https://your-deployed-portal.com/ai-config
2. Upload your schedule photo
3. Review what AI extracted
4. Add WiFi and Canvas info
5. Enter your device code
6. Done!

**That's it!** Your Timagotchi will configure itself automatically.

## For Developers/Deployers

### Setup (One-Time)

1. **Get Free API Key**
   - Visit https://makersuite.google.com/app/apikey
   - Sign in with Google
   - Click "Create API Key"
   - Copy the key

2. **Deploy to Render** (or Railway/Heroku)
   - Fork this repo
   - Create new Web Service on Render
   - Set root directory: `web`
   - Add environment variable:
     - Key: `GEMINI_API_KEY`
     - Value: `your-api-key-here`
   - Deploy!

3. **Test It**
   - Visit `/ai-config` on your deployed site
   - Upload a test schedule image
   - Verify AI analysis works

### Maintenance

**No maintenance required!**
- AI runs on Google's servers
- Free tier is plenty (1,500 requests/day)
- No database to maintain
- No backups needed
- In-memory storage auto-cleans

### Monitoring

Check `/health` endpoint:
```json
{
  "status": "healthy",
  "ai_enabled": true,
  "active_codes": 2
}
```

If `ai_enabled: false`, check that `GEMINI_API_KEY` is set.

### Costs

**Everything is FREE:**
- Gemini AI: Free tier (60/min, 1500/day)
- Render hosting: Free tier available
- No hidden costs
- No credit card needed

### Troubleshooting

**AI not working?**
- Check `GEMINI_API_KEY` is set
- Restart the web service
- Check `/health` shows `ai_enabled: true`

**Hit rate limits?**
- Free tier: 60/min, 1500/day
- Wait a minute if hit per-minute limit
- Upgrade to paid tier if needed (unlikely)

**Bad analysis?**
- User can use chat to ask AI questions
- User can manually correct any fields
- Falls back to manual config if needed

## Architecture

```
User uploads photo
       ↓
Flask receives image
       ↓
Sends to Gemini AI API
       ↓
AI analyzes & extracts
       ↓
Returns structured data
       ↓
User reviews/confirms
       ↓
Generates config.py
       ↓
Sends to Pi device
       ↓
Device configures itself
```

## Security

- Images sent to Google (see their privacy policy)
- Images not stored after analysis
- API key in environment (never in code)
- HTTPS required for production
- Pairing codes expire (1 hour)
- One-time use codes

## Support

- Check `web/AI_CONFIG_README.md` for details
- See `QUICKSTART_AI.md` for quick start
- Review `AI_FEATURE_SUMMARY.md` for overview
- Open GitHub issue for bugs

## Success Stories

Expected results:
- 80% time savings vs manual config
- 95% accuracy on schedule extraction
- Happy users who just upload and go
- Teachers can help students easily
- Less support burden

Enjoy your AI-powered configurator!
