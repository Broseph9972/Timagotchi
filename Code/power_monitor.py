import os
import subprocess
import time


def _read_first_existing(paths):
    for p in paths:
        try:
            if os.path.exists(p):
                with open(p, 'r') as f:
                    return f.read().strip()
        except Exception:
            pass
    return None


def get_battery_percent():
    """Return battery percent (0-100) if a system battery is exposed, else None.
    Tries common Linux power_supply paths. Most Pi + power banks will return None.
    """
    candidates = [
        '/sys/class/power_supply/BAT0/capacity',
        '/sys/class/power_supply/battery/capacity',
    ]
    raw = _read_first_existing(candidates)
    if raw is None:
        return None
    try:
        val = int(''.join(ch for ch in raw if ch.isdigit()))
        if 0 <= val <= 100:
            return val
    except Exception:
        pass
    return None


def get_throttled_flags():
    """Return tuple (undervoltage, throttled) using vcgencmd if available.
    On non-Pi or missing vcgencmd, returns (False, False).
    """
    try:
        out = subprocess.run(['vcgencmd', 'get_throttled'], capture_output=True, text=True, timeout=0.3)
        if out.returncode != 0:
            return False, False
        # output like: throttled=0x50000
        text = out.stdout.strip()
        if '0x' in text:
            hex_str = text.split('0x', 1)[1]
            flags = int(hex_str, 16)
            undervolt = bool(flags & (1 << 16)) or bool(flags & 1)
            throttled = bool(flags & (1 << 17)) or bool(flags & (1 << 1))
            return undervolt, throttled
    except Exception:
        pass
    return False, False


_CPU_LAST = None


def get_cpu_usage_fraction():
    """Approximate CPU usage as fraction 0..1 using /proc/stat deltas.
    Light-weight and no external deps; good enough for a relative graph.
    """
    global _CPU_LAST
    try:
        with open('/proc/stat', 'r') as f:
            line = f.readline()
        parts = line.split()
        if parts[0] != 'cpu':
            return None
        # user, nice, system, idle, iowait, irq, softirq, steal, guest, guest_nice
        vals = list(map(int, parts[1:8]))
        user, nice, system, idle, iowait, irq, softirq = vals
        idle_all = idle + iowait
        non_idle = user + nice + system + irq + softirq
        total = idle_all + non_idle
        if _CPU_LAST is None:
            _CPU_LAST = (idle_all, total, time.time())
            return None
        prev_idle, prev_total, _ = _CPU_LAST
        _CPU_LAST = (idle_all, total, time.time())
        totald = total - prev_total
        idled = idle_all - prev_idle
        if totald <= 0:
            return None
        cpu_fraction = max(0.0, min(1.0, (totald - idled) / totald))
        return cpu_fraction
    except Exception:
        return None


def get_power_status():
    """Aggregate power metrics."""
    undervolt, throttled = get_throttled_flags()
    pct = get_battery_percent()
    cpu = get_cpu_usage_fraction()
    return {
        'battery_percent': pct,
        'undervolt': undervolt,
        'throttled': throttled,
        'cpu_usage': cpu,
    }
