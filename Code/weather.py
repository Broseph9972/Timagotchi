import os
import time
import json
import requests


_CACHE = None
_CACHE_TS = 0.0


def _load_weather_config():
    here = os.path.dirname(__file__)
    path = os.path.join(here, 'weather_config.json')
    if not os.path.exists(path):
        return None
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except Exception:
        return None


def fetch_weather(force=False):
    """Fetch current weather using OpenWeatherMap.
    Expects weather_config.json with: {"api_key":"...","lat":..,"lon":..} OR {"city":"Name","api_key":"..."}
    Caches for 10 minutes.
    Returns dict or None on failure.
    """
    global _CACHE, _CACHE_TS
    now = time.time()
    if (not force) and _CACHE and (now - _CACHE_TS < 600):
        return _CACHE

    cfg = _load_weather_config()
    if not cfg:
        return None
    api_key = cfg.get('api_key')
    if not api_key:
        return None

    base = 'https://api.openweathermap.org/data/2.5/weather'
    params = {'appid': api_key, 'units': 'metric'}
    if 'lat' in cfg and 'lon' in cfg:
        params.update({'lat': cfg['lat'], 'lon': cfg['lon']})
    elif 'city' in cfg:
        params.update({'q': cfg['city']})
    else:
        return None

    try:
        r = requests.get(base, params=params, timeout=5)
        if r.status_code != 200:
            return None
        data = r.json()
        temp_c = None
        desc = None
        try:
            temp_c = data['main']['temp']
        except Exception:
            pass
        try:
            weather = data.get('weather') or []
            if weather:
                desc = weather[0].get('description')
        except Exception:
            pass
        name = data.get('name')
        result = {'temp_c': temp_c, 'desc': desc, 'name': name}
        _CACHE = result
        _CACHE_TS = now
        return result
    except Exception:
        return None
