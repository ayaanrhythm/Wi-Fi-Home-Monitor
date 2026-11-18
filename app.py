"""Streamlit dashboard for the WiFi Smart Home Monitor.

Reads predictions from the SQLite activity log (data/activity_log.db).
Fill it with a simulated day first:
    .\\.venv\\Scripts\\python.exe simulate_day.py
Then run:
    .\\.venv\\Scripts\\python.exe -m streamlit run app.py
"""

import streamlit as st

from activity_log import DB_PATH, find_falls, find_inactivity, load_events

st.set_page_config(page_title="WiFi Smart Home Monitoring")
st.title("WiFi Smart Home Monitoring")

events = load_events()
if events.empty:
    st.warning(f"No activity logged yet in {DB_PATH.name}. "
               "Run `simulate_day.py` to replay a simulated day.")
    st.stop()

with st.sidebar:
    st.header("Alert rules")
    hours = st.slider("Inactivity alert after (hours)", 0.5, 6.0, 2.0, 0.5)
    day_start, day_end = st.slider("Waking hours", 0, 24, (7, 22))
    fall_conf = st.slider("Fall alert min confidence", 0.0, 1.0, 0.5, 0.05)

# Alerts
st.subheader("Alerts")
gaps = find_inactivity(events, hours=hours, day_start=day_start, day_end=day_end)
falls = find_falls(events, min_confidence=fall_conf)
if not gaps and falls.empty:
    st.success("No alerts.")
for _, row in falls.iterrows():
    msg = f"at {row['time']:%H:%M} (confidence {row['confidence']:.0%})"
    if row["confident"]:
        st.error(f"Possible fall {msg}")
    else:
        st.warning(f"Low-confidence fall detection {msg}, worth checking")
for start, end in gaps:
    length = (end - start).total_seconds() / 3600
    st.warning(f"No activity detected from {start:%H:%M} to {end:%H:%M} ({length:.1f} h)")

# Summary
st.subheader("Daily Summary")
c1, c2, c3 = st.columns(3)
c1.metric("Events", len(events))
c2.metric("First activity", f"{events['time'].min():%H:%M}")
c3.metric("Last activity", f"{events['time'].max():%H:%M}")
st.bar_chart(events["activity"].value_counts())

# History
st.subheader("Activity History")
table = events.assign(
    Time=events["time"].dt.strftime("%H:%M"),
    Activity=events["activity"],
    Confidence=(events["confidence"] * 100).round().astype(int).astype(str) + "%",
)[["Time", "Activity", "Confidence"]]
st.dataframe(table, hide_index=True, width="stretch")

st.info("Simulated day: real model predictions on UT-HAR windows, "
        "replayed on a scripted schedule. Not live CSI.")
