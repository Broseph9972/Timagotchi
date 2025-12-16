# Copilot Instructions for Timagotchi

## Project Overview
Timagotchi is a Raspberry Pi Zero WH school schedule display system using a Waveshare 1.44" LCD HAT. It displays the current school period, progress bars, grades from Canvas LMS, and includes embedded games (Tetris, Doom raycaster). The display is 128x128 pixels with GPIO button controls. DO NOT USE ANY FUCKING EMOJIS

## Architecture & Data Flow

### Core Components
- **main.py**: Entry point; initializes `WaveshareDisplay`, `InputHandler`, `ThemeManager`, and `Menu` sequentially. Handles CLI errors gracefully.
- **menu.py** (~1600 lines): Main application logic. Single infinite loop in `menu.run()` handles screen rendering and input processing. Contains schedule logic, Canvas API integration, game launchers, and settings.
- **display_waveshare.py** (~574 lines): Display abstraction layer. Wraps legacy `LCD_1in44` driver with PIL image rendering. Manages fonts, icons, ASCII art faces, and theme-aware color rendering.
- **input_handler.py**: GPIO abstraction supporting both `RPi.GPIO` (legacy) and `lgpio` (Bookworm+) with automatic fallback.
- **theme_manager.py**: JSON-based theme system loading from `themes.json`. Manages color palettes; themes are applied to all UI elements via `display.theme_manager`.

### Data Flow
1. **Input**: Buttons → `InputHandler.get_input()` → returns direction/action strings
2. **State**: `Menu` class holds all state (schedule, settings, Canvas data, stopwatch, etc.)
3. **Rendering**: `Menu` calls `display.render_*()` methods → PIL Image → LCD via SPI
4. **External**: Canvas API via `requests` library; caching in `canvas_cache.json`

## Key Files & Patterns

### Schedule Configuration
- **config.py**: Master schedule file with hardcoded periods, times, A/B day logic
  - Periods defined as dict: `PERIODS = {1: "09:56", 2: "10:51", ...}`
  - A/B day support: `A_DAY_PERIODS` vs `B_DAY_PERIODS`; `AB_DAY_MODE = "auto"|"a"|"b"`
  - Advisory period: `ADVISORY_PERIOD`, `advisory`, `advisorydays` (e.g., "m,t")
  - Lunch window: `LUNCH_START`, `LUNCH_END`
  - `TIME_SYNC_MODE` controls NTP sync ("disabled"|"on_boot"|"periodic")

### Display & Rendering
- **display_waveshare.py**:
  - `_load_lcd_driver()`: Complex module loading to support both legacy and packaged drivers
  - Fallback to `old code/LCD_1in44.py` if packaged driver unavailable
  - Icons loaded from `Icons/` directory (PNG format, cached)
  - ASCII faces borrowed from Pwnagotchi (e.g., `"look_r": "( ⚆_⚆)"`)

### Menu Navigation
- **menu.py**:
  - State machine approach: `self.current_screen` = "main"|"grades"|"settings"|game names
  - Sidebar navigation: `self.nav_items` = ["Main Page", "Grades", "Settings"]
  - Settings submenu items conditional on `config.py` (e.g., A/B Day only if enabled)
  - Input-to-action mapping: up/down = navigate, left/right = change screen, press = select
  - Keyboard developer mode: Konami code detection in input loop

### Canvas Integration
- **Location**: Canvas API calls in `menu.py` (not separated module)
- **Setup**: Creates `canvas_config.json` on first use (base URL + API token)
- **Caching**: `canvas_cache.json` persists course/grade data; cleared on every boot
- **Usage**: Fetch courses → select course → view assignments by grade/date

### Configuration & Persistence
- **config.py**: All hardcoded; edited manually or via `configure_schedule.py` CLI tool
- **themes.json**: Theme definitions with `current_theme` key
- **Phrases.json**: Context-aware messages by period (e.g., "5 more minutes!" during lunch)
- **schedule_state.json**: Tracks preset rotation for A/B day scheduling
- **systemd service**: `schedule-display.service` for auto-start/restart on boot

## Development Workflow

### Installation & Setup
```bash
sudo raspi-config  # Enable SPI interface
./install.sh       # Install dependencies, drivers, systemd unit
./start.sh         # Manual launch (debug mode)
```

### Testing & Debugging
- **Desktop simulation**: Not supported; requires actual Pi hardware for GPIO
- **Error handling**: Graceful fallback to default fonts if system fonts unavailable
- **Driver issues**: Re-run `install.sh` to repair driver installation; check `old code/` folder

### Adding Features
1. **New period logic**: Edit `config.py` + update `A_DAY_PERIODS`/`B_DAY_PERIODS`
2. **New screen**: Add to `Menu` class, update `self.nav_items`, implement `render_*()` in display
3. **New game**: Create launcher in `games_config.py`, subprocess spawned via `Menu.launch_game()`
4. **New theme**: Add entry to `themes.json` with color dict; auto-loaded by `ThemeManager`
5. **Custom phrases**: Add period → message mapping to `Phrases.json`

## Project-Specific Conventions

### Naming & Structure
- GPIO pins defined as class attributes in `InputHandler` (BCM numbering)
- Time format everywhere is "HH:MM" (24-hour); display format controlled by `USE_24_HOUR` config
- Colors are RGB tuples: `(R, G, B)` where each is 0–255
- JSON files in `Code/` directory for config; no subdirectories

### Error Handling
- **Graceful degradation**: Missing icons → render text; Canvas API failure → skip grades display
- **No crash on Pi reboot**: Main loop catches `KeyboardInterrupt` and `Exception`, logs trace
- **Driver loading**: Priority order: installed package → legacy `old code/` → raise `FileNotFoundError`

### Performance Considerations
- **Display refresh**: ~40ms per frame on Pi Zero; limited by SPI speed
- **Canvas sync**: API calls cached; only fresh fetch on explicit "Update Grades"
- **Memory**: Pi Zero W has 512MB RAM; icon cache limited to prevent bloat
- **Button debounce**: 200ms (`InputHandler.debounce_time`)

## Testing & Validation

No formal test suite; validation is manual on hardware:
1. Verify schedule periods display correctly
2. Test A/B day rotation (check state file increment)
3. Canvas API token validation on first setup
4. Theme colors render correctly on LCD
5. GPIO buttons debounce consistently

## Cross-References

- **Hardware**: [bom.csv](../bom.csv) lists components
- **Installation**: [README.md](../README.md) § Installation
- **Legacy support**: [Code/old code/](Code/old%20code) contains original drivers
- **Example custom script**: [Code/custom_script_example.py](Code/custom_script_example.py)
