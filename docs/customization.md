# Customization Guide

## Themes

Edit `Code/themes.json` to create or modify themes:

```json
{
  "your_theme_name": {
    "background": [20, 20, 30],
    "text_primary": [255, 255, 255],
    "text_secondary": [150, 150, 150],
    "accent": [100, 200, 255],
    "sidebar_box": [40, 40, 50],
    "sidebar_box_selected": [60, 60, 80],
    "divider": [80, 80, 100]
  }
}
```

All colors use RGB (0-255 range).

## Custom Phrases

Edit `Code/Phrases.json` to customize what your character says:

```json
{
  "passing": ["Almost there!", "Quick break!"],
  "lunch": ["Time to eat!", "Lunch break!"],
  "period1": ["Good morning!", "Let's start!"],
  "period2": ["Keep going!", "Focus time!"]
}
```

Supported period keys: `period1`, `period2`, ..., `period7`, `advisory`, `lunch`, `passing`, `after_school`

## Schedule Configuration

Run the interactive schedule tool:

```bash
python3 configure_schedule.py
```

Or manually edit `Code/config.py`:

```python
PERIODS = {
    1: "09:56",
    2: "10:51",
    3: "11:46",
    # ... etc
}

A_DAY_PERIODS = {1, 2, 3, 4, 5, 6, 7}
B_DAY_PERIODS = {1, 2, 3, 4, 5, 6, 7}

ADVISORY_PERIOD = 0
ADVISORY_DAYS = "m,t,w,th,f"  # Monday through Friday

LUNCH_START = "12:15"
LUNCH_END = "12:50"
```

## Custom Scripts

Create `Code/custom_script.py` with a `run()` function:

```python
def run(display, input_handler):
    """
    Your custom code here.
    Return 'key1', 'key2', or 'key3' to navigate on exit.
    """
    display.clear((0, 0, 0))
    display.draw.text(
        (10, 50), 
        "Hello World!", 
        font=display.font_large, 
        fill=(255, 255, 255)
    )
    display._render()
    
    while True:
        action = input_handler.get_input()
        if action in ('key1', 'key2', 'key3'):
            return action
```

Access via: Secret Menu → Run Custom Script

## Progress Bar Modes

Available modes (set in settings):
- **Time in Class**: Percentage of current period elapsed
- **Time in Day**: Percentage of school day elapsed
- **Lunch Countdown**: Minutes until lunch ends

## Configuration Files

- `config.py` - Schedule periods and times
- `themes.json` - Color definitions
- `Phrases.json` - Context-aware messages
- `canvas_config.json` - Canvas API credentials (created on first use)
- `fonts.json` - Font configuration
