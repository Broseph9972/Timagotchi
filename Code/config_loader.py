# -*- coding: utf-8 -*-
"""
Configuration loader for Timagotchi.
Reads all settings from config.json instead of config.py
"""
import json
import os

CONFIG_FILE = 'config.json'

def _load_config():
    """Load configuration from JSON file"""
    if not os.path.exists(CONFIG_FILE):
        raise FileNotFoundError(f"{CONFIG_FILE} not found. Please create it based on config.json.example")
    
    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)

# Load config once at module import
_config = _load_config()

# School settings
SCHOOL_START = _config['school']['start']
SCHOOL_END = _config['school']['end']
USE_24_HOUR = _config['display']['time_format'] == '24h'

# Periods
PERIODS = {int(k): v for k, v in _config['schedule']['period_times'].items()}
PERIOD_LENGTH = _config['schedule']['period_length']
PASSING_TIME = _config['schedule']['passing_time']

# Period names
A_DAY_PERIODS = {int(k): v for k, v in _config['schedule']['period_names_a'].items()}
B_DAY_PERIODS = {int(k): v for k, v in _config['schedule']['period_names_b'].items()}

# Day presets (new format supporting multiple presets beyond A/B)
DAY_PRESETS = {}
NUM_DAY_PRESETS = 2
try:
    if 'day_presets' in _config['schedule']:
        # New format with multiple presets
        DAY_PRESETS = {k: {int(pk): pv for pk, pv in v.items()} 
                       for k, v in _config['schedule']['day_presets'].items()}
        NUM_DAY_PRESETS = len(DAY_PRESETS)
    else:
        # Fallback to legacy A/B format
        DAY_PRESETS = {'A': A_DAY_PERIODS, 'B': B_DAY_PERIODS}
        NUM_DAY_PRESETS = 2
except Exception:
    DAY_PRESETS = {'A': A_DAY_PERIODS, 'B': B_DAY_PRESETS}
    NUM_DAY_PRESETS = 2

# Lunch
LUNCH_START = _config['schedule']['lunch']['start']
LUNCH_END = _config['schedule']['lunch']['end']
lunchlength = str(_config['schedule']['lunch'].get('duration', 25))

# Advisory
ADVISORY_START = _config['schedule']['advisory']['start']
advisory = str(_config['schedule']['advisory']['enabled']).lower()
advisorylength = str(_config['schedule']['advisory']['length'])
ADVISORY_PERIOD = 0
# Convert "m,t" format to list of day names
_advisory_days_str = _config['schedule']['advisory']['days']
if isinstance(_advisory_days_str, str):
    # Convert abbreviations: m->monday, t->tuesday, w->wednesday, th->thursday, f->friday
    day_map = {'m': 'monday', 't': 'tuesday', 'w': 'wednesday', 'th': 'thursday', 'f': 'friday'}
    advisorydays = ",".join(day_map.get(d.strip(), d.strip()) for d in _advisory_days_str.split(','))
else:
    advisorydays = ",".join(_advisory_days_str)

freetimedaus = "w,th,f"  # Keep as constant for now

# A/B Day scheduling
abday = str(_config['schedule']['ab_day']['enabled']).lower()
AB_DAY_MODE = _config['schedule']['ab_day']['mode']  # "auto", "a", or "b"
MANUAL_AB_DAY = _config['schedule']['ab_day'].get('manual_selection', 'a')

# WiFi
WIFI_NETWORKS = [
    (net['ssid'], net['password']) 
    for net in _config['system'].get('wifi_networks', [])
]

# Time sync
TIME_SYNC_MODE = _config['system']['time_sync']  # "disabled", "on_boot", "periodic"
TIME_SYNC_INTERVAL = _config['system']['time_sync_interval']
TIMEZONE = _config['school'].get('timezone', 'America/New_York')

# Progress bar
PROGRESS_BAR_MODE = _config['display']['progress_bar_mode']

def reload_config():
    """Reload configuration from JSON file"""
    global _config, SCHOOL_START, SCHOOL_END, USE_24_HOUR, PERIODS, PERIOD_LENGTH
    global PASSING_TIME, A_DAY_PERIODS, B_DAY_PERIODS, DAY_PRESETS, NUM_DAY_PRESETS
    global LUNCH_START, LUNCH_END, lunchlength, ADVISORY_START, advisory, advisorylength, advisorydays
    global abday, AB_DAY_MODE, MANUAL_AB_DAY, WIFI_NETWORKS, TIME_SYNC_MODE
    global TIME_SYNC_INTERVAL, TIMEZONE, PROGRESS_BAR_MODE
    
    _config = _load_config()
    
    # Re-initialize all variables
    SCHOOL_START = _config['school']['start']
    SCHOOL_END = _config['school']['end']
    USE_24_HOUR = _config['display']['time_format'] == '24h'
    PERIODS = {int(k): v for k, v in _config['schedule']['period_times'].items()}
    PERIOD_LENGTH = _config['schedule']['period_length']
    PASSING_TIME = _config['schedule']['passing_time']
    A_DAY_PERIODS = {int(k): v for k, v in _config['schedule']['period_names_a'].items()}
    B_DAY_PERIODS = {int(k): v for k, v in _config['schedule']['period_names_b'].items()}
    # Reload day presets
    try:
        if 'day_presets' in _config['schedule']:
            DAY_PRESETS = {k: {int(pk): pv for pk, pv in v.items()} 
                           for k, v in _config['schedule']['day_presets'].items()}
            NUM_DAY_PRESETS = len(DAY_PRESETS)
        else:
            DAY_PRESETS = {'A': A_DAY_PERIODS, 'B': B_DAY_PERIODS}
            NUM_DAY_PRESETS = 2
    except Exception:
        DAY_PRESETS = {'A': A_DAY_PERIODS, 'B': B_DAY_PERIODS}
        NUM_DAY_PRESETS = 2
    LUNCH_START = _config['schedule']['lunch']['start']
    LUNCH_END = _config['schedule']['lunch']['end']
    lunchlength = str(_config['schedule']['lunch'].get('duration', 25))
    ADVISORY_START = _config['schedule']['advisory']['start']
    advisory = str(_config['schedule']['advisory']['enabled']).lower()
    advisorylength = str(_config['schedule']['advisory']['length'])
    _advisory_days_str = _config['schedule']['advisory']['days']
    if isinstance(_advisory_days_str, str):
        day_map = {'m': 'monday', 't': 'tuesday', 'w': 'wednesday', 'th': 'thursday', 'f': 'friday'}
        advisorydays = ",".join(day_map.get(d.strip(), d.strip()) for d in _advisory_days_str.split(','))
    else:
        advisorydays = ",".join(_advisory_days_str)
    abday = str(_config['schedule']['ab_day']['enabled']).lower()
    AB_DAY_MODE = _config['schedule']['ab_day']['mode']
    MANUAL_AB_DAY = _config['schedule']['ab_day'].get('manual_selection', 'a')
    WIFI_NETWORKS = [(net['ssid'], net['password']) for net in _config['system'].get('wifi_networks', [])]
    TIME_SYNC_MODE = _config['system']['time_sync']
    TIME_SYNC_INTERVAL = _config['system']['time_sync_interval']
    TIMEZONE = _config['school'].get('timezone', 'America/New_York')
    PROGRESS_BAR_MODE = _config['display']['progress_bar_mode']
