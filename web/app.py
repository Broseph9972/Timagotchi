"""
Timagotchi Configuration Portal Backend
Flask API for pairing Pi devices with web configuration interface
"""

from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
import random
import time
from datetime import datetime, timedelta
import os

app = Flask(__name__)
CORS(app)  # Enable CORS for Pi requests

# In-memory storage for pairing codes and configurations
# Format: {code: {"config": {...}, "created_at": timestamp, "used": bool}}
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

@app.route('/api/generate-code', methods=['POST'])
def generate_pairing_code():
    """Generate a new pairing code for a Pi device"""
    cleanup_expired_codes()
    
    code = generate_code()
    pairing_codes[code] = {
        "config": None,
        "created_at": time.time(),
        "used": False
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
        "timestamp": datetime.now().isoformat()
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
