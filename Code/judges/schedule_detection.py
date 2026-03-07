# Demonstrates: School period detection with advisory, lunch, and class period logic
import datetime
from config_loader import (
    PERIODS, LUNCH_START, LUNCH_END,
    PERIOD_LENGTH, PASSING_TIME,
    advisory, advisorylength, advisorydays
)
def get_current_period(self, current_time):
    if 'advisory' in PERIODS and advisory.lower() == "true":
        weekday_abbr = {0: 'm', 1: 't', 2: 'w', 3: 'th', 4: 'f', 5: 'sat', 6: 'sun'}
        today_abbr = weekday_abbr.get(datetime.date.today().weekday(), '')
        advisory_day_list = [d.strip() for d in advisorydays.split(',')]
        if today_abbr in advisory_day_list:
            advisory_start = datetime.datetime.strptime(PERIODS['advisory'], "%H:%M").time()
            advisory_start_dt = datetime.datetime.combine(datetime.date.today(), advisory_start)
            advisory_len = int(advisorylength)
            advisory_end = advisory_start_dt + datetime.timedelta(minutes=advisory_len)
            if advisory_start_dt <= current_time < advisory_end:
                time_remaining = advisory_end - current_time
                return "ADVISORY", time_remaining, False
    lunch_start = datetime.datetime.strptime(LUNCH_START, "%H:%M").time()
    lunch_start_dt = datetime.datetime.combine(datetime.date.today(), lunch_start)
    lunch_end = datetime.datetime.strptime(LUNCH_END, "%H:%M").time()
    lunch_end_dt = datetime.datetime.combine(datetime.date.today(), lunch_end)
    if lunch_start_dt <= current_time < lunch_end_dt:
        time_remaining = lunch_end_dt - current_time
        return "LUNCH", time_remaining, True
    numbered_periods = sorted([p for p in PERIODS.keys() if isinstance(p, int)])
    for i, period in enumerate(numbered_periods):
        period_start_time = datetime.datetime.strptime(PERIODS[period], "%H:%M").time()
        period_start = datetime.datetime.combine(datetime.date.today(), period_start_time)
        if i + 1 < len(numbered_periods):
            next_period = numbered_periods[i + 1]
            next_period_time = datetime.datetime.strptime(PERIODS[next_period], "%H:%M").time()
            next_period_start = datetime.datetime.combine(datetime.date.today(), next_period_time)
            max_end = period_start + datetime.timedelta(minutes=PERIOD_LENGTH + PASSING_TIME)
            period_end = min(next_period_start, max_end)
        else:
            period_end = period_start + datetime.timedelta(minutes=PERIOD_LENGTH)
        if period_start <= current_time < period_end:
            time_remaining = period_end - current_time
            return period, time_remaining, False
    return None, None, False
