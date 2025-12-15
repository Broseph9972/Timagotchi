// currentCode is set by inline script in config.html
let currentSection = 0;
const sections = ['schedule', 'canvas', 'custom', 'review'];

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    setupEventListeners();
});

function setupEventListeners() {
    // Toggle advisory config
    document.getElementById('has-advisory').addEventListener('change', (e) => {
        document.getElementById('advisory-config').style.display = e.target.checked ? 'block' : 'none';
    });
    
    // Toggle lunch config
    document.getElementById('has-lunch').addEventListener('change', (e) => {
        document.getElementById('lunch-config').style.display = e.target.checked ? 'block' : 'none';
    });
    
    // Toggle A/B day config
    document.getElementById('use-ab-day').addEventListener('change', (e) => {
        document.getElementById('ab-day-config').style.display = e.target.checked ? 'block' : 'none';
    });
    
    // Toggle Canvas config
    document.getElementById('enable-canvas').addEventListener('change', (e) => {
        document.getElementById('canvas-config').style.display = e.target.checked ? 'block' : 'none';
    });
    
    // Toggle custom phrases
    document.getElementById('enable-custom-phrases').addEventListener('change', (e) => {
        document.getElementById('phrases-config').style.display = e.target.checked ? 'block' : 'none';
    });
    
    // Form submission
    document.getElementById('config-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        await submitConfiguration();
    });
}

function showStep(stepId) {
    // No-op now since we removed step transitions
}

function nextSection() {
    if (currentSection === 3) {
        generateSummary();
    }
    
    if (currentSection < 3) {
        // Hide current section
        document.getElementById(`section-${sections[currentSection]}`).classList.remove('active');
        
        currentSection++;
        
        // Show next section
        document.getElementById(`section-${sections[currentSection]}`).classList.add('active');
        
        // Update progress indicator
        updateProgressIndicator();
        
        // Generate summary if we're on review
        if (currentSection === 3) {
            generateSummary();
        }
    }
}

function prevSection() {
    if (currentSection > 0) {
        // Hide current section
        document.getElementById(`section-${sections[currentSection]}`).classList.remove('active');
        
        currentSection--;
        
        // Show previous section
        document.getElementById(`section-${sections[currentSection]}`).classList.add('active');
        
        // Update progress indicator
        updateProgressIndicator();
    }
}

function updateProgressIndicator() {
    const steps = document.querySelectorAll('.progress-step');
    steps.forEach((step, index) => {
        if (index <= currentSection) {
            step.classList.add('active');
        } else {
            step.classList.remove('active');
        }
    });
}

function addWifiNetwork() {
    const container = document.getElementById('wifi-networks');
    const networkDiv = document.createElement('div');
    networkDiv.className = 'wifi-network';
    networkDiv.innerHTML = `
        <div class="form-row">
            <div class="form-group">
                <label>Network Name (SSID)</label>
                <input type="text" class="wifi-ssid" placeholder="MyWiFi">
            </div>
            <div class="form-group">
                <label>Password</label>
                <input type="password" class="wifi-password" placeholder="password123">
            </div>
        </div>
    `;
    container.appendChild(networkDiv);
}

function generateSummary() {
    const summary = document.getElementById('config-summary');
    const config = collectFormData();
    
    let html = '<h3>Schedule</h3>';
    html += `<p><strong>School Hours:</strong> ${config.schedule.school_start} - ${config.schedule.school_end}</p>`;
    html += `<p><strong>Periods:</strong> ${config.schedule.num_periods} periods of ${config.schedule.period_length} minutes</p>`;
    html += `<p><strong>Time Format:</strong> ${config.system.use_24_hour ? '24-Hour' : '12-Hour'}</p>`;
    
    if (config.schedule.has_advisory) {
        html += `<p><strong>Advisory:</strong> ${config.schedule.advisory_start} (${config.schedule.advisory_length} min)</p>`;
    }
    
    if (config.schedule.has_lunch) {
        html += `<p><strong>Lunch:</strong> ${config.schedule.lunch_start} - ${config.schedule.lunch_end}</p>`;
    }
    
    if (config.schedule.use_ab_day) {
        html += `<p><strong>A/B Day:</strong> ${config.schedule.ab_day_mode}</p>`;
    }
    
    html += '<h3>System</h3>';
    html += `<p><strong>Timezone:</strong> ${config.system.timezone}</p>`;
    html += `<p><strong>Time Sync:</strong> ${config.system.time_sync_mode}</p>`;
    
    if (config.canvas && config.canvas.enabled) {
        html += '<h3>Canvas LMS</h3>';
        html += `<p><strong>URL:</strong> ${config.canvas.base_url}</p>`;
        html += `<p><strong>API Token:</strong> ${config.canvas.api_token.substring(0, 10)}...</p>`;
    }
    
    const wifiNetworks = config.system.wifi_networks.filter(n => n[0]);
    if (wifiNetworks.length > 0) {
        html += '<h3>WiFi Networks</h3>';
        wifiNetworks.forEach(network => {
            html += `<p>📡 ${network[0]}</p>`;
        });
    }
    
    html += '<h3>Appearance</h3>';
    html += `<p><strong>Theme:</strong> ${config.customization.theme}</p>`;
    
    summary.innerHTML = html;
}

function collectFormData() {
    // Schedule data
    const schedule = {
        school_start: document.getElementById('school-start').value,
        school_end: document.getElementById('school-end').value,
        num_periods: parseInt(document.getElementById('num-periods').value),
        period_length: parseInt(document.getElementById('period-length').value),
        passing_time: parseInt(document.getElementById('passing-time').value),
        has_advisory: document.getElementById('has-advisory').checked,
        has_lunch: document.getElementById('has-lunch').checked,
        use_ab_day: document.getElementById('use-ab-day').checked
    };
    
    if (schedule.has_advisory) {
        schedule.advisory_start = document.getElementById('advisory-start').value;
        schedule.advisory_length = parseInt(document.getElementById('advisory-length').value);
        schedule.advisory_days = Array.from(document.querySelectorAll('.advisory-day:checked'))
            .map(cb => cb.value)
            .join(',');
    }
    
    if (schedule.has_lunch) {
        schedule.lunch_start = document.getElementById('lunch-start').value;
        schedule.lunch_end = document.getElementById('lunch-end').value;
    }
    
    if (schedule.use_ab_day) {
        schedule.ab_day_mode = document.getElementById('ab-day-mode').value;
    }
    
    // System data
    const wifiSSIDs = document.querySelectorAll('.wifi-ssid');
    const wifiPasswords = document.querySelectorAll('.wifi-password');
    const wifiNetworks = [];
    
    for (let i = 0; i < wifiSSIDs.length; i++) {
        const ssid = wifiSSIDs[i].value.trim();
        const password = wifiPasswords[i].value.trim();
        if (ssid) {
            wifiNetworks.push([ssid, password]);
        }
    }
    
    const system = {
        timezone: document.getElementById('timezone').value,
        time_sync_mode: document.getElementById('time-sync').value,
        use_24_hour: document.getElementById('time-format').value === '24',
        wifi_networks: wifiNetworks
    };
    
    // Canvas data
    let canvas = null;
    if (document.getElementById('enable-canvas').checked) {
        canvas = {
            enabled: true,
            base_url: document.getElementById('canvas-url').value.trim(),
            api_token: document.getElementById('canvas-token').value.trim()
        };
    }
    
    // Customization data
    const customization = {
        theme: document.querySelector('input[name="theme"]:checked').value
    };
    
    if (document.getElementById('enable-custom-phrases').checked) {
        customization.phrases = {
            passing: document.getElementById('phrases-passing').value.split(',').map(s => s.trim()).filter(s => s),
            lunch: document.getElementById('phrases-lunch').value.split(',').map(s => s.trim()).filter(s => s)
        };
    }
    
    return {
        schedule,
        system,
        canvas,
        customization
    };
}

async function submitConfiguration() {
    const config = collectFormData();
    const deviceCode = document.getElementById('device-code-input').value.trim();
    
    if (!deviceCode || deviceCode.length !== 5) {
        alert('Please enter a valid 5-digit device code');
        return;
    }
    
    try {
        const response = await fetch(`/api/config/${deviceCode}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(config)
        });
        
        const data = await response.json();
        
        if (response.ok) {
            // Show success screen
            document.getElementById('step-config').classList.remove('active');
            document.getElementById('step-success').classList.add('active');
        } else {
            alert('Error: ' + (data.error || 'Failed to save configuration'));
        }
    } catch (error) {
        alert('Connection error. Please try again.');
        console.error(error);
    }
}

function showError(element, message) {
    element.textContent = message;
    element.classList.add('show');
}

function hideError(element) {
    element.classList.remove('show');
}
