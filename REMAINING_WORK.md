# Timagotchi Web Portal - Remaining Work

## ✅ Completed

1. **Multi-page website structure**
   - Created index.html (landing page)
   - Created about.html (project info)
   - Created build.html (build guide)
   - Created docs.html (API documentation)
   - Created error.html (error page)
   - Updated app.py with all routes

2. **Refactored config to `/config/<code>` route**
   - Renamed original index.html to config.html
   - Updated config.html to work with code in URL
   - Removed code entry step from config flow
   - Users can now visit timagotchi.com/config/12345 directly

3. **Updated JavaScript**
   - Removed code validation step
   - Code now comes from URL parameter
   - Simplified form submission

## 🚧 Still TODO

### 1. Update CSS for Multi-Page Site

**File**: `web/static/style.css`

**Need to add:**
- Navbar styling (`.navbar`, `.nav-container`, `.nav-menu`, `.nav-link`, `.nav-logo`)
- Hero section (`.hero`, `.hero-title`, `.hero-subtitle`, `.hero-buttons`)
- Features grid (`.features`, `.feature-grid`, `.feature-card`, `.feature-icon`)
- Config section on landing page (`.config-section`, `.config-card`, `.code-input-large`)
- Showcase grid (`.showcase`, `.showcase-grid`, `.showcase-item`)
- Footer (`.footer`, `.footer-content`, `.footer-section`, `.footer-bottom`)
- Content pages (`.page-header`, `.content-section`, `.content-card`)
- Error page (`.error-page`, `.error-card`, `.error-icon`)
- API docs styling (`.api-endpoint`, `.endpoint-header`, `.method`, `.params-table`)
- Build guide styling (`.bom-table`, `.build-steps`, `.controls-grid`, `.troubleshooting`)

**Quick fix**: Append new styles to existing style.css or create a separate `main.css` for new pages.

### 2. Move config.py Generation to Backend

**File**: `web/app.py`

**What to add:**
```python
def generate_config_py(config_data):
    """Generate config.py file content from configuration JSON"""
    schedule = config_data['schedule']
    system = config_data['system']
    
    # Calculate period times
    periods = calculate_periods(schedule)
    
    # Generate Python code as string
    lines = [
        f'SCHOOL_START = "{schedule["school_start"]}"',
        f'SCHOOL_END = "{schedule["school_end"]}"',
        f'USE_24_HOUR = {system["use_24_hour"]}',
        # ... etc
    ]
    
    return '\n'.join(lines)

def calculate_periods(schedule):
    """Calculate period start times"""
    # Port logic from config_portal.py
    pass
```

**Update** `@app.route('/api/config/<code>', methods=['POST'])`:
- Call `generate_config_py(config_data)`
- Generate canvas_config.json string
- Store as: `{"config_py": "...", "canvas_config": "{...}", ...}`

### 3. Simplify Pi Client

**File**: `Code/config_portal.py`

**Changes needed:**
- Remove `_write_config_py()` method
- Remove `_calculate_periods()` method
- Update `write_config_files()` to expect:
  ```python
  config = {
      "config_py": "SCHOOL_START = ...",  # Already formatted
      "canvas_config": '{"base_url": ...}',  # JSON string
      "themes_update": {"current_theme": "dark"},
      "phrases_update": {...}
  }
  ```
- Just write strings directly to files

### 4. Update API Response Format

**Current**: Nested JSON with schedule/system/canvas objects

**New**:
```json
{
  "config_py": "SCHOOL_START = \"09:05\"\nSCHOOL_END = \"15:55\"\n...",
  "canvas_config": "{\"base_url\": \"...\", \"api_token\": \"...\"}",
  "themes_update": {"current_theme": "dark"},
  "phrases_update": {
    "passing": ["phrase1", "phrase2"],
    "lunch": ["phrase3", "phrase4"]
  }
}
```

**Benefits**:
- Pi just writes strings to files
- No complex generation logic on Pi
- Easier to test (can verify config.py format on backend)

### 5. Test End-to-End

1. Deploy backend to Render/Railway
2. Update `TIMAGOTCHI_API_URL` on Pi
3. Delete config.py
4. Boot Pi → generates code
5. Visit website home page
6. Enter code in landing page input
7. Get redirected to `/config/12345`
8. Fill out form
9. Submit
10. Pi syncs and restarts

## Quick CSS Addition

Add this to `web/static/style.css` to get basic styling working:

```css
/* Navigation */
.navbar {
    background: var(--card-bg);
    border-bottom: 1px solid var(--border-color);
    padding: 1rem 0;
}

.nav-container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 2rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.nav-logo {
    font-size: 1.5rem;
    font-weight: bold;
    color: var(--primary-color);
    text-decoration: none;
}

.nav-menu {
    display: flex;
    gap: 2rem;
}

.nav-link {
    color: var(--text-secondary);
    text-decoration: none;
    transition: color 0.2s;
}

.nav-link:hover, .nav-link.active {
    color: var(--primary-color);
}

/* Hero Section */
.hero {
    background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
    padding: 6rem 2rem;
    text-align: center;
}

.hero-title {
    font-size: 4rem;
    margin-bottom: 1rem;
    background: linear-gradient(135deg, var(--primary-color), #a855f7);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

/* Footer */
.footer {
    background: var(--card-bg);
    border-top: 1px solid var(--border-color);
    padding: 3rem 0 1rem;
    margin-top: 4rem;
}

.footer-content {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 2rem;
    margin-bottom: 2rem;
}

/* ... add rest of styles as needed */
```

## Priority Order

1. **CSS** - Add basic styles so pages look decent
2. **Backend generation** - Move config.py logic to app.py
3. **Pi client** - Simplify to just write strings
4. **Test** - Deploy and test full flow

Let me know if you want me to continue with any of these specific tasks!
