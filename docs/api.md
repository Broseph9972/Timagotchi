# API Reference

## Core Modules

### display_waveshare.py

Main display driver for the Waveshare 1.44" LCD HAT.

**Key Methods:**

- `clear(color)` - Clear display with specified RGB color
- `draw.text(xy, text, font, fill)` - Draw text
- `draw.rectangle(xy, fill, outline)` - Draw rectangle
- `draw.line(xy, fill, width)` - Draw line
- `_render()` - Push image to LCD

### input_handler.py

GPIO input handling with debouncing.

**Key Methods:**

- `get_input()` - Returns direction/action string
  - Directions: `'up'`, `'down'`, `'left'`, `'right'`
  - Actions: `'key1'`, `'key2'`, `'key3'`, `'press'`

### menu.py

Main application menu and state management.

**Key Attributes:**

- `current_screen` - Active screen name
- `schedule` - Current schedule data
- `canvas_data` - Cached Canvas API data
- `settings` - User settings

**Key Methods:**

- `run()` - Main event loop
- `launch_game(game_name)` - Launch a game

### theme_manager.py

Theme loading and color management.

**Key Methods:**

- `load_theme(name)` - Load theme by name
- `get_color(key)` - Get color from current theme

## GPIO Pin Mapping

### Joystick & Buttons

| Function | GPIO | BCM |
|----------|------|-----|
| Up | GPIO 6 | 6 |
| Down | GPIO 19 | 19 |
| Left | GPIO 5 | 5 |
| Right | GPIO 26 | 26 |
| Press (Center) | GPIO 13 | 13 |
| Key1 (Top Right) | GPIO 21 | 21 |
| Key2 (Middle Right) | GPIO 20 | 20 |
| Key3 (Bottom Right) | GPIO 16 | 16 |

### Display (ST7735S)

| Signal | GPIO | Purpose |
|--------|------|---------|
| SPI CS | GPIO 8 | Chip Select |
| DC | GPIO 25 | Data/Command |
| RST | GPIO 27 | Reset |
| BL | GPIO 24 | Backlight |

## Canvas API

Canvas integration is handled in `menu.py`.

**Setup:**

Create `Code/canvas_config.json`:

```json
{
  "base_url": "https://yourschool.instructure.com",
  "api_token": "your_api_token"
}
```

**Available Data:**

- Course list with names and IDs
- Current grade for each course
- Recent assignments
- Assignment due dates

## Configuration Schema

### config.py

```python
PERIODS = {int: str}  # Period number to start time
A_DAY_PERIODS = set   # Period numbers for A day
B_DAY_PERIODS = set   # Period numbers for B day
ADVISORY_PERIOD = int # Period number or 0 if none
ADVISORY_DAYS = str   # Comma-separated days (m,t,w,th,f)
LUNCH_START = str     # Time in HH:MM format
LUNCH_END = str       # Time in HH:MM format
AB_DAY_MODE = str     # "auto", "a", or "b"
```

### themes.json

```json
{
  "theme_name": {
    "background": [R, G, B],
    "text_primary": [R, G, B],
    "text_secondary": [R, G, B],
    "accent": [R, G, B],
    "sidebar_box": [R, G, B],
    "sidebar_box_selected": [R, G, B],
    "divider": [R, G, B]
  }
}
```

### Phrases.json

```json
{
  "period1": ["phrase1", "phrase2"],
  "period2": ["phrase1", "phrase2"],
  "lunch": ["phrase1", "phrase2"],
  "passing": ["phrase1", "phrase2"],
  "after_school": ["phrase1", "phrase2"]
}
```
