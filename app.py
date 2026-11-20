"""Caregiver dashboard for the WiFi Smart Home Monitor.

Reads predictions from the SQLite activity log (data/activity_log.db).
Fill it with a simulated day first:
    .\\.venv\\Scripts\\python.exe simulate_day.py
Then run:
    .\\.venv\\Scripts\\python.exe -m streamlit run app.py
"""

from datetime import date, datetime, timedelta

import pandas as pd
import streamlit as st

import charts
import styles
from activity_log import DB_PATH, find_falls, find_inactivity, load_events
from summary import summarize_day

ICONS = {"Walk": "directions_walk", "Run": "directions_run", "Stand up": "accessibility_new",
         "Sit down": "chair", "Pick up": "back_hand", "Lie down": "bed",
         "Fall": "personal_injury"}

st.set_page_config(page_title="Home monitor", page_icon=":material/home_health:",
                   layout="wide")

# ---------- Sidebar ----------
today = date.today()
with st.sidebar:
    st.markdown("## :violet[:material/home_health:] Home monitor")
    st.caption("WiFi activity monitoring · caregiver view")
    day = st.date_input("Day", value=today)
    st.subheader("Alert rules")
    hours = st.slider("Inactivity alert after (hours)", 0.5, 6.0, 2.0, 0.5)
    day_start, day_end = st.slider("Waking hours", 0, 24, (7, 22))
    fall_conf = st.slider("Fall alert min confidence", 0.0, 1.0, 0.5, 0.05)

# ---------- Data ----------
events = load_events()
if events.empty:
    styles.inject("violet")
    st.title("Home monitor")
    st.warning(f"No activity logged yet in {DB_PATH.name}. "
               "Run `simulate_day.py` to replay a simulated day.")
    st.stop()

# Alert rules run on the whole log, then we keep the chosen day. That way a
# day with no events at all still shows up as one long quiet period.
day_events = events[events["time"].dt.date == day].reset_index(drop=True)
prev_count = int((events["time"].dt.date == day - timedelta(days=1)).sum())
gaps = [(a, b) for a, b in find_inactivity(events, hours=hours, day_start=day_start,
                                           day_end=day_end) if a.date() == day]
falls = find_falls(day_events, min_confidence=fall_conf)
confident_falls = falls[falls["confident"]]
n_alerts = len(falls) + len(gaps)

if not confident_falls.empty:
    color, label, headline, sub = ("red", "Possible fall",
                                   f"Possible fall at {confident_falls['time'].iloc[-1]:%H:%M}",
                                   "Please check in now")
elif gaps or not falls.empty:
    color, label, headline, sub = "orange", "Check in", "Worth a check-in", "Something looked unusual"
elif day_events.empty:
    color, label, headline, sub = "violet", "No data", "No data for this day", "Nothing was recorded"
else:
    color, label, headline, sub = "green", "All clear", "Everything looks normal", "No alerts today"

styles.inject(color)

# ---------- Layout ----------
main, side = st.columns([2.2, 1], gap="medium")

with main:
    # 1. Hero / status banner
    with st.container(key="hero"):
        top_left, top_right = st.columns([2.4, 1.6])
        with top_left:
            hour = datetime.now().hour
            greeting = ("Good morning" if hour < 12 else
                        "Good afternoon" if hour < 18 else "Good evening")
            st.markdown(f"#### {greeting},")
            st.markdown(f"## {'Today' if day == today else f'{day:%A %d %B}'}")
            st.caption("Here's what's happening at home.")
        with top_right, st.container(key="hero-status"):
            st.markdown(f":{color}[**{label}**]  \n:gray[{sub}]", text_alignment="right")

        with st.container(gap="small"):
            st.title(headline)
            with st.container(horizontal=True):
                last = (f"{day_events['time'].max():%H:%M}" if not day_events.empty else "--:--")
                for key, text in {
                    "last": f":material/schedule: Last activity **{last}**",
                    "count": f":material/directions_walk: **{len(day_events)}** detections",
                    "alerts": f":{color if n_alerts else 'green'}[:material/notifications:] "
                              f"**{n_alerts}** alert{'s' * (n_alerts != 1)}",
                }.items():
                    with st.container(key=f"chip-{key}", width="content"):
                        st.markdown(text)

    # 2. Summary
    with st.container(key="card-summary"):
        st.subheader(":violet[:material/auto_awesome:] Daily summary")
        st.write(summarize_day(day_events, gaps, falls))

    # 3. Timeline
    with st.container(key="card-timeline"):
        st.subheader("Timeline")
        st.altair_chart(charts.timeline(day_events, gaps, falls, day_start, day_end),
                        alt="When activity was detected during the day, "
                            "with quiet periods and possible falls marked")
        st.caption(":blue[●] Activity   :orange[■] Quiet period   "
                   ":red[●] Possible fall   :gray[■] Night (not checked)")

    # Recent activity table (like a devices overview)
    with st.container(key="card-recent"):
        head_l, head_r = st.columns([3, 1], vertical_alignment="center")
        head_l.markdown(f"### Recent activity &nbsp; :violet[{len(day_events)} detections]")
        head_r.markdown(f":gray[:material/calendar_today:] {day:%b %d, %Y}", text_alignment="right")
        widths = [3, 2, 1.2, 1.4]
        with st.container(key="row-head"):
            for col, name in zip(st.columns(widths), ["Activity", "Status", "Time", "Confidence"]):
                col.markdown(name)
        if day_events.empty:
            st.caption("No activity recorded on this day.")
        for i, ev in day_events.iloc[::-1].head(6).iterrows():
            if ev["activity"] == "Fall":
                status = ":red[●] Possible fall" if ev["confidence"] >= fall_conf else ":orange[●] Check"
            else:
                status = ":green[●] Normal"
            with st.container(key=f"row-{i}"):
                c1, c2, c3, c4 = st.columns(widths, vertical_alignment="center")
                tint = "red" if ev["activity"] == "Fall" else "violet"
                c1.markdown(f":{tint}[:material/{ICONS.get(ev['activity'], 'sensors')}:] "
                            f"**{ev['activity']}**  \n"
                            "<small style='color:#8A8FB3'>WiFi sensor</small>",
                            unsafe_allow_html=True)
                c2.markdown(status)
                c3.markdown(f"{ev['time']:%H:%M}")
                c4.markdown(f"{ev['confidence']:.0%}")

with side:
    # Active hours gauge
    with st.container(key="card-gauge"):
        st.subheader("Active hours")
        st.caption("Waking hours with movement")
        if day == today:
            span_end = min(day_end, datetime.now().hour + 1)
        else:
            span_end = day_end
        waking = max(span_end - day_start, 1)
        hrs = day_events["time"].dt.hour
        active = int(hrs[(hrs >= day_start) & (hrs < span_end)].nunique())
        frac = active / waking
        mood = "Active day" if frac >= 0.6 else "Quieter day" if frac >= 0.3 else "Very quiet"
        st.altair_chart(charts.ring_gauge(frac, f"{active}/{waking}", mood),
                        width="content", alt=f"{active} of {waking} waking hours had movement")
        with st.container(horizontal=True, horizontal_alignment="distribute"):
            st.markdown(f":gray[:material/wb_sunny:] {day_start:02d}:00 – {day_end:02d}:00")
            st.markdown(f":gray[:material/percent:] {frac:.0%} active")

    # Detections card
    with st.container(key="card-detections"):
        st.subheader("Detections")
        if prev_count:
            st.metric("Detections today", len(day_events), delta=len(day_events) - prev_count,
                      delta_color="off", delta_description="vs the day before",
                      label_visibility="collapsed")
        else:
            st.metric("Detections today", len(day_events), label_visibility="collapsed")
            st.caption("No data for the day before to compare with.")
        if not day_events.empty:
            st.altair_chart(charts.hourly_area(day_events), alt="Detections per hour")

    # Alerts card
    with st.container(key="card-alerts"):
        st.subheader("Alerts")
        alerts = []
        for _, f in falls.iterrows():
            if f["confident"]:
                alerts.append((f["time"], ":red[:material/emergency:]",
                               f"**Possible fall** at {f['time']:%H:%M}",
                               f"Confidence {f['confidence']:.0%}"))
            else:
                alerts.append((f["time"], ":orange[:material/help:]",
                               f"**Possible fall?** at {f['time']:%H:%M}",
                               f"Low confidence ({f['confidence']:.0%}), worth checking"))
        for a, b in gaps:
            alerts.append((a, ":orange[:material/hourglass_empty:]",
                           f"**No movement** {a:%H:%M}–{b:%H:%M}",
                           f"For {charts.duration(a, b)}"))
        if not alerts:
            st.markdown(":green[:material/check_circle:] No alerts on this day.")
        for _, icon, title, detail in sorted(alerts, key=lambda x: x[0]):
            st.markdown(f"{icon} {title}  \n:gray[{detail}]")

    # Monitoring card (like a security panel)
    with st.container(key="card-monitoring"):
        st.subheader("Monitoring")
        st.caption(":green[All checks active]")
        checks = [
            ("fall", "green", "personal_injury", "Fall check", f"from {fall_conf:.0%} sure"),
            ("quiet", "green", "hourglass_empty", "Inactivity check", f"after {hours:g} h"),
            ("hours", "green", "wb_sunny", "Waking hours", f"{day_start:02d}–{day_end:02d}"),
            ("sensor", "violet", "wifi", "Sensor", "Simulated"),
        ]
        for key, tone, icon, name, value in checks:
            with st.container(key=f"tile-{key}", horizontal=True,
                              vertical_alignment="center", gap="small"):
                with st.container(key=f"tile-icon-{tone}-{key}", width=34, height=34):
                    st.markdown(f":{tone}[:material/{icon}:]", text_alignment="center")
                st.markdown(f"**{name}**", width="stretch")
                st.markdown(f":gray[{value}]", width="content")

# Details (collapsed)
with st.expander("Details", icon=":material/table_rows:"):
    if day_events.empty:
        st.write("No events on this day.")
    else:
        table_col, chart_col = st.columns([3, 2], gap="medium")
        with table_col:
            table = pd.DataFrame({
                "Time": day_events["time"].dt.strftime("%H:%M"),
                "Activity": day_events["activity"],
                "Confidence": (day_events["confidence"] * 100).round(),
            })
            st.dataframe(table, hide_index=True,
                         column_config={"Confidence": st.column_config.ProgressColumn(
                             format="%d%%", min_value=0, max_value=100)},
                         alt="All detected events for the day")
        with chart_col:
            st.altair_chart(charts.activity_counts(day_events),
                            alt="How often each activity was detected")

st.caption("Simulated day: real model predictions on UT-HAR windows, "
           "replayed on a scripted schedule. Not live CSI.")
