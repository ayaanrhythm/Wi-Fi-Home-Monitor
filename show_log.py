"""Print the activity log and current alerts in the terminal.

Run:
    python show_log.py            # whole log
    python show_log.py --last 10  # only the last 10 events
"""

import argparse

from activity_log import DB_PATH, find_falls, find_inactivity, load_events


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--last", type=int, help="show only the last N events")
    parser.add_argument("--hours", type=float, default=2.0, help="inactivity limit")
    args = parser.parse_args()

    events = load_events()
    if events.empty:
        print(f"No events in {DB_PATH}. Run simulate_day.py first.")
        return

    shown = events.tail(args.last) if args.last else events
    print(f"{len(events)} events in {DB_PATH}\n")
    for _, row in shown.iterrows():
        print(f"{row['time']:%Y-%m-%d %H:%M}  {row['activity']:<9} {row['confidence']:.0%}")

    print("\nAlerts:")
    falls = find_falls(events)
    gaps = find_inactivity(events, hours=args.hours)
    for _, row in falls.iterrows():
        kind = "Possible fall" if row["confident"] else "Low-confidence fall"
        print(f"  {kind} at {row['time']:%Y-%m-%d %H:%M} ({row['confidence']:.0%})")
    for start, end in gaps:
        print(f"  No activity {start:%Y-%m-%d %H:%M} -> {end:%H:%M}")
    if falls.empty and not gaps:
        print("  none")


if __name__ == "__main__":
    main()
