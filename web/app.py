"""
Timagotchi Configuration Portal Backend
Flask API for pairing Pi devices with web configuration interface
NOW WITH AI-POWERED SCHEDULE ANALYSIS
"""

from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
import random
import time
from datetime import datetime, timedelta
import os
import base64
import io
import json
from PIL import Image

# Try to import Gemini AI
try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    genai = None

app = Flask(__name__)
CORS(app)  # Enable CORS for Pi requests

# Configure Gemini AI
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
if GEMINI_API_KEY and GENAI_AVAILABLE:
    client = genai.Client(api_key=GEMINI_API_KEY)
    model_name = 'gemini-2.0-flash-exp'
else:
    client = None
    model_name = None

# In-memory storage for pairing codes and configurations
# Format: {code: {"config": {...}, "created_at": timestamp, "used": bool, "ai_session": {...}}}
pairing_codes = {}

# Configuration timeout (1 hour)
CODE_TIMEOUT_SECONDS = 3600

def generate_code():
    """Generate a unique 5-digit numeric code"""
    while True:
        code = str(random.randint(10000, 99999))
        if code not in pairing_codes:
            return code

def cleanup_expired_codes():
    """Remove codes older than timeout"""
    current_time = time.time()
    expired = [code for code, data in pairing_codes.items() 
               if current_time - data["created_at"] > CODE_TIMEOUT_SECONDS]
    for code in expired:
        del pairing_codes[code]

@app.route('/')
def index():
    """Serve the main landing page"""
    return render_template('index.html')

@app.route('/about')
def about():
    """About the Timagotchi project"""
    return render_template('about.html')

@app.route('/build')
def build_guide():
    """How to build your own Timagotchi"""
    return render_template('build.html')

@app.route('/docs')
def documentation():
    """Documentation and API reference"""
    return render_template('docs.html')

@app.route('/config/<code>')
def config_page(code):
    """Configuration interface for a specific pairing code"""
    # Allow 'temp' as placeholder code - validation happens on submission
    if code != 'temp':
        cleanup_expired_codes()
        if code not in pairing_codes:
            return render_template('error.html', message="Invalid or expired code"), 404
    
    return render_template('config.html', code=code)

@app.route('/ai-config')
def ai_config_page():
    """New AI-powered configuration interface"""
    return render_template('ai_config.html')

@app.route('/api/generate-code', methods=['POST'])
def generate_pairing_code():
    """Generate a new pairing code for a Pi device"""
    cleanup_expired_codes()
    
    code = generate_code()
    pairing_codes[code] = {
        "config": None,
        "created_at": time.time(),
        "used": False,
        "ai_session": {
            "analysis": None,
            "questions": [],
            "answers": {}
        }
    }
    
    return jsonify({
        "code": code,
        "expires_in": CODE_TIMEOUT_SECONDS
    })

@app.route('/api/config/<code>', methods=['GET'])
def get_config(code):
    """Pi polls this endpoint to check if configuration is ready"""
    cleanup_expired_codes()
    
    if code not in pairing_codes:
        return jsonify({"error": "Invalid or expired code"}), 404
    
    data = pairing_codes[code]
    
    if data["config"] is None:
        return jsonify({"status": "pending"}), 202
    
    # Configuration is ready - mark as used and return config
    config = data["config"]
    data["used"] = True
    
    # Delete code after successful retrieval (one-time use)
    del pairing_codes[code]
    
    return jsonify({
        "status": "ready",
        "config": config
    })

@app.route('/api/config/<code>', methods=['POST'])
def submit_config(code):
    """Website submits configuration for a specific pairing code"""
    cleanup_expired_codes()
    
    if code not in pairing_codes:
        return jsonify({"error": "Invalid or expired code"}), 404
    
    if pairing_codes[code]["used"]:
        return jsonify({"error": "Code already used"}), 410
    
    config_data = request.json
    
    # Validate required fields
    required_fields = ["schedule", "system"]
    for field in required_fields:
        if field not in config_data:
            return jsonify({"error": f"Missing required field: {field}"}), 400
    
    # Store configuration
    pairing_codes[code]["config"] = config_data
    
    return jsonify({
        "status": "success",
        "message": "Configuration saved. Your Timagotchi will sync shortly."
    })

@app.route('/api/validate-code/<code>', methods=['GET'])
def validate_code(code):
    """Validate if a code exists and is still valid"""
    cleanup_expired_codes()
    
    if code not in pairing_codes:
        return jsonify({"valid": False, "error": "Invalid or expired code"}), 404
    
    if pairing_codes[code]["used"]:
        return jsonify({"valid": False, "error": "Code already used"}), 410
    
    if pairing_codes[code]["config"] is not None:
        return jsonify({"valid": False, "error": "Code already configured"}), 410
    
    time_remaining = CODE_TIMEOUT_SECONDS - (time.time() - pairing_codes[code]["created_at"])
    
    return jsonify({
        "valid": True,
        "time_remaining": int(time_remaining)
    })

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for deployment monitoring"""
    return jsonify({
        "status": "healthy",
        "active_codes": len([c for c in pairing_codes.values() if not c["used"]]),
        "timestamp": datetime.now().isoformat(),
        "ai_enabled": client is not None
    })

@app.route('/api/analyze-schedule', methods=['POST'])
def analyze_schedule():
    """Analyze a schedule image using Gemini AI"""
    if not client:
        return jsonify({"error": "AI service not configured. Set GEMINI_API_KEY environment variable."}), 503
    
    try:
        # Get image from request
        if 'image' not in request.files:
            return jsonify({"error": "No image file provided"}), 400
        
        image_file = request.files['image']
        
        # Read image bytes
        image_bytes = image_file.read()
        
        # Create AI prompt for schedule analysis
        prompt = """You are an expert at analyzing school schedule images. Analyze this schedule image and extract ALL information in a structured format.

Extract the following information:
1. School start time and end time (format: HH:MM in 24-hour)
2. Number of periods per day
3. Each period's start time (format: HH:MM in 24-hour)
4. Period length in minutes
5. Passing time between periods in minutes
6. Period names/subjects (if visible)
7. Whether there's an A/B day schedule (alternating days)
8. Advisory/homeroom period details (if any): start time, length, which days
9. Lunch period: start time and end time
10. Any special notes or patterns

IMPORTANT RULES:
- If you see any text that looks like a schedule, extract it
- Look for times, period numbers, subject names
- Note if schedule alternates (A day / B day or similar patterns)
- Identify lunch periods
- Note advisory/homeroom if present
- Be PRECISE with times - convert to 24-hour format
- If you're uncertain about ANYTHING, note it in an "uncertain_items" list

Return your analysis in this EXACT JSON format (no markdown, just raw JSON):
{
  "school_start": "HH:MM",
  "school_end": "HH:MM",
  "num_periods": number,
  "period_times": {"1": "HH:MM", "2": "HH:MM", ...},
  "period_length": number,
  "passing_time": number,
  "period_names": {"1": "Name", "2": "Name", ...},
  "has_ab_day": true/false,
  "a_day_periods": {"1": "Name", ...} or null,
  "b_day_periods": {"1": "Name", ...} or null,
  "has_advisory": true/false,
  "advisory_start": "HH:MM" or null,
  "advisory_length": number or null,
  "advisory_days": ["m", "t", "w", "th", "f"] or null,
  "has_lunch": true/false,
  "lunch_start": "HH:MM" or null,
  "lunch_end": "HH:MM" or null,
  "uncertain_items": ["list of things you're not 100% sure about"],
  "notes": "any additional observations"
}"""

        # Generate response using new API
        response = client.models.generate_content(
            model=model_name,
            contents=[
                types.Part.from_bytes(
                    data=image_bytes,
                    mime_type=image_file.content_type or 'image/jpeg'
                ),
                types.Part.from_text(text=prompt)
            ]
        )
        
        # Parse the response
        response_text = response.text.strip()
        
        # Remove markdown code blocks if present
        if response_text.startswith('```'):
            # Find the actual JSON content
            lines = response_text.split('\n')
            json_lines = []
            in_json = False
            for line in lines:
                if line.strip().startswith('```'):
                    in_json = not in_json
                    continue
                if in_json or (line.strip().startswith('{') or json_lines):
                    json_lines.append(line)
                    if line.strip().endswith('}') and line.strip().count('{') <= line.strip().count('}'):
                        break
            response_text = '\n'.join(json_lines)
        
        try:
            analysis = json.loads(response_text)
        except json.JSONDecodeError as e:
            # If JSON parsing fails, return raw text for debugging
            return jsonify({
                "error": "Failed to parse AI response",
                "raw_response": response_text,
                "parse_error": str(e)
            }), 500
        
        # Validate that we got something useful
        if not analysis.get('school_start') or not analysis.get('num_periods'):
            return jsonify({
                "error": "Could not extract complete schedule information",
                "partial_analysis": analysis,
                "uncertain_items": analysis.get('uncertain_items', [])
            }), 422
        
        return jsonify({
            "status": "success",
            "analysis": analysis,
            "has_uncertainties": len(analysis.get('uncertain_items', [])) > 0
        })
        
    except Exception as e:
        import traceback
        return jsonify({
            "error": "Failed to analyze image",
            "details": str(e),
            "trace": traceback.format_exc()
        }), 500

@app.route('/api/ask-question', methods=['POST'])
def ask_question():
    """Ask AI a follow-up question about the schedule"""
    if not client:
        return jsonify({"error": "AI service not configured"}), 503
    
    try:
        data = request.json
        question = data.get('question')
        context = data.get('context', {})  # Previous analysis
        
        if not question:
            return jsonify({"error": "No question provided"}), 400
        
        # Create context-aware prompt
        prompt_text = f"""You are helping configure a school schedule display system. 

Previous analysis: {json.dumps(context, indent=2)}

User question: {question}

Provide a clear, concise answer. If asking about a specific value (like a time, period name, etc.), provide ONLY the requested value in a simple format. If it's a yes/no question, respond with just "yes" or "no" followed by brief explanation if needed.

For Canvas LMS questions, explain what Canvas is and ask if they want to integrate grades display.

Keep responses under 100 words unless more detail is specifically requested."""

        response = client.models.generate_content(
            model=model_name,
            contents=prompt_text
        )
        
        return jsonify({
            "status": "success",
            "answer": response.text.strip()
        })
        
    except Exception as e:
        return jsonify({
            "error": "Failed to process question",
            "details": str(e)
        }), 500

@app.route('/api/generate-config', methods=['POST'])
def generate_config():
    """Generate config.py content from analysis and user inputs"""
    try:
        data = request.json
        analysis = data.get('analysis', {})
        user_inputs = data.get('user_inputs', {})
        
        # Merge analysis with user inputs (user inputs override)
        config_data = {**analysis, **user_inputs}
        
        # Generate config.py content
        config_content = f"""# School Schedule Configuration
# Generated by Timagotchi AI Configurator

# Time format: "HH:MM" (24-hour format)
SCHOOL_START = "{config_data.get('school_start', '09:00')}"
SCHOOL_END = "{config_data.get('school_end', '15:00')}"
USE_24_HOUR = {str(config_data.get('use_24_hour', False))}

# Advisory period
ADVISORY_START = "{config_data.get('advisory_start', '09:00')}"
ADVISORY_PERIOD = 0
advisory = "{str(config_data.get('has_advisory', False)).lower()}"
advisorylength = "{config_data.get('advisory_length', 30)}"
advisorydays = "{','.join(config_data.get('advisory_days', []))}"
freetimedaus = "{','.join(config_data.get('free_time_days', []))}"

# Period start times
PERIODS = {{
    {', '.join([f'{k}: "{v}"' for k, v in sorted(config_data.get('period_times', {}).items(), key=lambda x: int(x[0]))])}
}}

# Lunch information
LUNCH_START = "{config_data.get('lunch_start', '12:00')}"
LUNCH_END = "{config_data.get('lunch_end', '12:30')}"

# Period names
"""
        
        # Handle A/B day periods
        if config_data.get('has_ab_day'):
            a_day = config_data.get('a_day_periods', config_data.get('period_names', {}))
            b_day = config_data.get('b_day_periods', config_data.get('period_names', {}))
            config_content += f"A_DAY_PERIODS = {{{', '.join([f'{k}: {repr(v)}' for k, v in sorted(a_day.items(), key=lambda x: int(x[0]))])}}}\n\n"
            config_content += f"B_DAY_PERIODS = {{{', '.join([f'{k}: {repr(v)}' for k, v in sorted(b_day.items(), key=lambda x: int(x[0]))])}}}\n\n"
        else:
            period_names = config_data.get('period_names', {})
            config_content += f"A_DAY_PERIODS = {{{', '.join([f'{k}: {repr(v)}' for k, v in sorted(period_names.items(), key=lambda x: int(x[0]))])}}}\n\n"
            config_content += f"B_DAY_PERIODS = {{{', '.join([f'{k}: {repr(v)}' for k, v in sorted(period_names.items(), key=lambda x: int(x[0]))])}}}\n\n"
        
        config_content += f"""# Period lengths (in minutes)
PERIOD_LENGTH = {config_data.get('period_length', 50)}
PASSING_TIME = {config_data.get('passing_time', 5)}

# Additional settings
lunchlength = "{int(config_data.get('lunch_length', 30))}"
abday = "{str(config_data.get('has_ab_day', False)).lower()}"
AB_DAY_MODE = "{config_data.get('ab_day_mode', 'auto')}"
MANUAL_AB_DAY = "a"

# WiFi Networks
WIFI_NETWORKS = [
    {', '.join([f'("{ssid}", "{pwd}")' for ssid, pwd in config_data.get('wifi_networks', [])])}
]

# Time Sync Settings
TIME_SYNC_MODE = "{config_data.get('time_sync_mode', 'on_boot')}"
TIME_SYNC_INTERVAL = {config_data.get('time_sync_interval', 6)}
TIMEZONE = "{config_data.get('timezone', 'America/New_York')}"

# Progress Bar Settings
PROGRESS_BAR_MODE = "{config_data.get('progress_bar_mode', 'time_in_class')}"
"""
        
        return jsonify({
            "status": "success",
            "config_content": config_content,
            "preview": config_content
        })
        
    except Exception as e:
        import traceback
        return jsonify({
            "error": "Failed to generate config",
            "details": str(e),
            "trace": traceback.format_exc()
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
