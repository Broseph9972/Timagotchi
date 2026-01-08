# AI-Powered Schedule Configuration

This feature uses Google's Gemini AI to automatically analyze photos of school schedules and generate configuration files.

## Features

- **Photo Upload**: Upload a photo of any school schedule
- **AI Analysis**: Gemini Vision AI extracts schedule information automatically
- **Smart Questions**: AI asks clarifying questions about uncertain items
- **Canvas Integration**: Prompts for Canvas LMS setup if needed
- **Interactive Chat**: Ask the AI questions about your schedule
- **Config Generation**: Automatically generates config.py file

## Setup

### Environment Variable

Set your Gemini API key as an environment variable:

```bash
export GEMINI_API_KEY="your-api-key-here"
```

### Get a Free Gemini API Key

1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the key and set it as environment variable

**Free Tier Limits:**
- 60 requests per minute
- 1,500 requests per day
- Completely free to use

### Deployment

For cloud deployment (Render, Railway, Heroku), add the environment variable in your platform's settings:

**Render:**
- Dashboard → Your Service → Environment → Add Environment Variable
- Key: `GEMINI_API_KEY`
- Value: Your API key

**Railway:**
```bash
railway variables set GEMINI_API_KEY=your-key-here
```

**Heroku:**
```bash
heroku config:set GEMINI_API_KEY=your-key-here
```

## Usage

### 1. Access the AI Configurator

Visit the home page and click "Use AI Configurator" or go directly to `/ai-config`

### 2. Upload Schedule Photo

- Take a clear photo of your school schedule
- Upload it by clicking or dragging
- Photo can be from:
  - School handbook
  - Website screenshot
  - Printed schedule
  - Student planner

### 3. AI Analysis

The AI will extract:
- School start and end times
- Number of periods
- Period start times
- Period names/subjects
- Lunch period
- Advisory/homeroom details
- A/B day scheduling
- And more...

### 4. Review & Questions

- Review extracted information
- Answer any clarification questions
- Use the chat to ask AI about unclear items
- Add Canvas LMS credentials if needed
- Configure WiFi networks

### 5. Generate & Submit

- Preview the generated config.py
- Enter your device's 5-digit code
- Submit to your Timagotchi

## Tips for Best Results

### Photo Quality

- **Good lighting**: Make sure schedule is clearly visible
- **Focus**: Ensure text is sharp and readable
- **Complete**: Include all periods and times
- **Flat**: Avoid curved or wrinkled paper
- **Close-up**: Fill frame with schedule

### Schedule Formats Supported

- Traditional 7-period schedules
- A/B block schedules
- 4x4 semester blocks
- Rotating drop schedules
- Elementary with specials
- College MWF/TR patterns

### If AI Makes Mistakes

Use the interactive chat to:
- Ask about specific times
- Clarify period names
- Confirm A/B day patterns
- Verify lunch periods

## API Endpoints

### POST /api/analyze-schedule

Upload and analyze a schedule image.

**Request:**
- `multipart/form-data` with `image` field

**Response:**
```json
{
  "status": "success",
  "analysis": {
    "school_start": "09:05",
    "school_end": "15:55",
    "num_periods": 6,
    "period_times": {...},
    "has_ab_day": true,
    ...
  },
  "has_uncertainties": false
}
```

### POST /api/ask-question

Ask AI a question about the schedule.

**Request:**
```json
{
  "question": "What time is lunch?",
  "context": { ... }
}
```

**Response:**
```json
{
  "status": "success",
  "answer": "Lunch is from 12:00 to 12:30"
}
```

### POST /api/generate-config

Generate config.py from analysis.

**Request:**
```json
{
  "analysis": { ... },
  "user_inputs": { ... }
}
```

**Response:**
```json
{
  "status": "success",
  "config_content": "# School Schedule Configuration\n..."
}
```

## Troubleshooting

### AI Service Not Configured

**Error:** "AI service not configured"

**Solution:** Set the `GEMINI_API_KEY` environment variable

### Failed to Analyze Image

**Causes:**
- Image too blurry
- Schedule not visible
- Unsupported format

**Solutions:**
- Retake photo with better lighting
- Try a different angle
- Ensure schedule text is clear

### Partial Analysis

If AI cannot extract all information:
- Check "uncertain_items" in response
- Use manual inputs to fill gaps
- Ask AI specific questions via chat

### API Rate Limits

Free tier limits:
- 60 requests/minute
- 1,500 requests/day

If you hit limits, wait a minute or upgrade to paid tier.

## Privacy & Security

- Images are sent to Google's Gemini API for analysis
- Images are not stored permanently
- API keys should be kept secret
- Generated configs are temporary (1 hour)
- Use HTTPS in production

## Comparison: AI vs Manual Configuration

### AI Configuration
- **Pros:** Fast, automatic, less error-prone
- **Cons:** Requires API key, internet, may need verification
- **Best for:** Most users, complex schedules

### Manual Configuration
- **Pros:** Complete control, no API needed, works offline
- **Cons:** Time-consuming, error-prone
- **Best for:** Simple schedules, privacy-focused users

## Future Enhancements

Potential improvements:
- OCR fallback for offline use
- Support for PDF schedules
- Multi-language support
- Schedule templates library
- Batch configuration for schools

## License

Part of the Timagotchi project. See main LICENSE file.
