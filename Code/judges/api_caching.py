# Demonstrates: JSON file caching for Canvas LMS API with TTL expiration
import os
import time
import json as _json
def _read_cache(self):
    try:
        if os.path.exists(self.canvas_cache_path):
            with open(self.canvas_cache_path, 'r') as f:
                return _json.load(f)
    except Exception:
        pass
    return {}
def _write_cache(self, data):
    try:
        with open(self.canvas_cache_path, 'w') as f:
            _json.dump(data, f)
    except Exception:
        pass
def _canvas_fetch_courses(self, cfg):
    cache = self._read_cache()
    now_ts = time.time()
    c_entry = cache.get('courses')
    if c_entry and now_ts < c_entry.get('expires', 0):
        return c_entry.get('data', [])
    data = self._canvas_request(cfg, 'users/self/courses', params={'include[]': ['enrollments', 'total_scores'], 'enrollment_state': 'active', 'per_page': 50})
    if data is None:
        return None
    courses = []
    for c in data:
        name = c.get('name') or c.get('course_code') or 'Course'
        percent = None
        grade_text = None
        for e in c.get('enrollments', []):
            if e.get('computed_current_period_score') is not None:
                percent = e['computed_current_period_score']
                break
            if e.get('current_period_score') is not None:
                percent = e['current_period_score']
                break
            if e.get('computed_current_score') is not None:
                percent = e['computed_current_score']
                break
            if e.get('current_score') is not None:
                percent = e['current_score']
                break
            if e.get('computed_final_score') is not None:
                percent = e['computed_final_score']
                break
            if e.get('final_score') is not None:
                percent = e['final_score']
                break
            if grade_text is None:
                grade_text = e.get('computed_current_period_grade') or e.get('current_period_grade') or e.get('computed_current_grade') or e.get('current_grade') or e.get('computed_final_grade') or e.get('final_grade')
        if percent is None:
            g = c.get('grades') or {}
            percent = g.get('current_period_score') or g.get('current_score') or g.get('final_score')
            if grade_text is None:
                grade_text = g.get('current_period_grade') or g.get('current_grade') or g.get('final_grade')
        courses.append({'id': c.get('id'), 'name': name, 'percent': percent if percent is not None else grade_text})
    cache['courses'] = {'data': courses, 'expires': now_ts + 600}
    self._write_cache(cache)
    return courses
