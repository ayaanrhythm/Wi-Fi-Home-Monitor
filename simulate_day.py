"""Replay a simulated day of activity into the SQLite log.

Takes a scripted daily routine, picks a UT-HAR test window of the matching
true activity for each step, runs the trained model on it, and logs the
*predicted* activity with the scripted timestamp. So the log contains real
model output (including its mistakes), just on a made-up schedule.

The routine includes a long quiet afternoon (to trigger the inactivity
alert) and a fall in the evening (to trigger the fall alert).

Run (after train.py):
    .\\.venv\\Scripts\\python.exe simulate_day.py
"""

from datetime import datetime, timedelta

import numpy as np

from activity_log import DB_PATH, connect, log_event
from predict import load_model, predict
from train import load_split

# (time of day, true activity) for the simulated day
ROUTINE = [
    ("07:05", "Stand up"), ("07:07", "Walk"), ("07:30", "Pick up"), ("07:32", "Walk"),
    ("07:50", "Sit down"), ("08:20", "Stand up"), ("08:22", "Walk"),
    ("09:00", "Run"), ("09:30", "Walk"), ("09:45", "Sit down"),
    ("10:40", "Stand up"), ("10:42", "Walk"), ("11:15", "Pick up"), ("11:17", "Walk"),
    ("12:00", "Sit down"), ("12:40", "Stand up"), ("12:42", "Walk"),
    ("13:10", "Lie down"),
    # 13:10 -> 16:20: nothing detected (long quiet afternoon)
    ("16:20", "Stand up"), ("16:22", "Walk"), ("17:00", "Pick up"), ("17:02", "Walk"),
    ("18:00", "Sit down"), ("18:45", "Stand up"), ("18:47", "Walk"),
    ("19:30", "Fall"),
    ("19:32", "Stand up"), ("19:34", "Walk"), ("20:00", "Sit down"),
    ("21:30", "Stand up"), ("21:32", "Walk"), ("21:50", "Lie down"),
]


def main(day=None, seed=0):
    day = day or datetime.now().date()
    rng = np.random.default_rng(seed)
    model, class_names = load_model()
    X_test, y_test = load_split("test")

    if DB_PATH.exists():
        DB_PATH.unlink()  # start each replay from an empty log
    conn = connect()

    correct = 0
    for clock, true_activity in ROUTINE:
        idx = rng.choice(np.flatnonzero(y_test == class_names.index(true_activity)))
        activity, conf = predict(model, class_names, X_test[idx])
        h, m = map(int, clock.split(":"))
        t = datetime.combine(day, datetime.min.time()) + timedelta(hours=h, minutes=m)
        log_event(conn, t, activity, conf)
        correct += activity == true_activity
        flag = "" if activity == true_activity else f"   (true: {true_activity})"
        print(f"{clock}  {activity:<9} {conf:.0%}{flag}")
    conn.close()
    print(f"\nLogged {len(ROUTINE)} events to {DB_PATH} "
          f"({correct}/{len(ROUTINE)} predicted correctly)")


if __name__ == "__main__":
    main()
