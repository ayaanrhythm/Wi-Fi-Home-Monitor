"""SQLite activity log and rule-based alerts.

Every prediction is stored as one row: (time, activity, confidence).
Alerts are plain rules over those rows, kept separate from the ML model
and from any future LLM, so they are easy to test and always behave the same.
"""

import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

DB_PATH = Path(__file__).parent / "data" / "activity_log.db"


def connect(db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    conn.execute(
        """CREATE TABLE IF NOT EXISTS events (
               id INTEGER PRIMARY KEY AUTOINCREMENT,
               time TEXT NOT NULL,          -- ISO 8601, local time
               activity TEXT NOT NULL,
               confidence REAL NOT NULL
           )"""
    )
    return conn


def log_event(conn, time, activity, confidence):
    conn.execute(
        "INSERT INTO events (time, activity, confidence) VALUES (?, ?, ?)",
        (time.isoformat(timespec="seconds"), activity, float(confidence)),
    )
    conn.commit()


def load_events(db_path=DB_PATH):
    """Return all events as a DataFrame sorted by time (empty if no DB yet)."""
    if not Path(db_path).exists():
        return pd.DataFrame(columns=["time", "activity", "confidence"])
    with sqlite3.connect(db_path) as conn:
        df = pd.read_sql_query(
            "SELECT time, activity, confidence FROM events ORDER BY time", conn
        )
    df["time"] = pd.to_datetime(df["time"])
    return df


def find_inactivity(events, hours=2.0, day_start=7, day_end=22, now=None):
    """Find gaps of at least `hours` with no detected activity during waking hours.

    Gaps are measured between consecutive events, from day_start to the first
    event, and from the last event to day_end (or to `now` if the day is still
    going). Days up to today are checked, so if data stops arriving that also
    shows up as a gap. Night hours (outside day_start..day_end) are ignored on
    purpose, since no activity while asleep is normal.
    Returns a list of (start, end) datetimes.
    """
    if events.empty:
        return []
    now = now or datetime.now()
    limit = timedelta(hours=hours)
    times = sorted(t.to_pydatetime() for t in events["time"])
    gaps = []
    # Walk every calendar day from the first event to today, so a day with
    # no events at all still shows up as one long gap instead of being skipped.
    day = times[0].date()
    while day <= max(times[-1].date(), now.date()):
        midnight = datetime.combine(day, datetime.min.time())
        start = midnight + timedelta(hours=day_start)
        end = midnight + timedelta(hours=day_end)
        if now < start:
            break  # today's waking hours haven't started yet
        inside = [t for t in times if start <= t <= end]
        stop = max(min(end, now), inside[-1] if inside else start)
        points = [start] + inside + [stop]
        for a, b in zip(points, points[1:]):
            if b - a >= limit:
                gaps.append((a, b))
        day += timedelta(days=1)
    return gaps


def find_falls(events, min_confidence=0.5):
    """Return every Fall event with a `confident` flag.

    Low-confidence falls are kept (not dropped) so the dashboard can still
    show them as a softer notice instead of silently hiding them.
    """
    falls = events[events["activity"] == "Fall"].copy()
    falls["confident"] = falls["confidence"] >= min_confidence
    return falls
