"""Altair charts for the dashboard (timeline, ring gauge, hourly area chart)."""

import math

import altair as alt
import pandas as pd

BLUE = "#5B8CFF"
VIOLET = "#8E7CFF"
ORANGE = "#F5A524"
RED = "#FF5C6C"
GRAY = "#8A8FB3"
TRACK = "#262A4D"

ACTIVITY_ORDER = ["Walk", "Run", "Stand up", "Sit down", "Pick up", "Lie down", "Fall"]


def hour_of_day(t):
    """Position on a 0-24 axis."""
    return t.hour + t.minute / 60 + t.second / 3600


def duration(a, b):
    mins = round((b - a).total_seconds() / 60)
    return f"{mins // 60} h {mins % 60} min" if mins >= 60 else f"{mins} min"


def _hour_axis():
    return alt.X("hour:Q", title=None, scale=alt.Scale(domain=[0, 24], nice=False),
                 axis=alt.Axis(values=list(range(0, 25, 3)), grid=False, domain=False,
                               labelExpr="(datum.value < 10 ? '0' : '') + datum.value + ':00'"))


def timeline(day_events, gaps, falls, day_start, day_end):
    """00:00-24:00 chart: dots per detection, quiet periods, falls, night."""
    x = _hour_axis()
    night = pd.DataFrame({"hour": [0, day_end], "end": [day_start, 24],
                          "label": ["Night (not checked)"] * 2})
    layers = [alt.Chart(night).mark_rect(color=GRAY, opacity=0.10)
              .encode(x=x, x2="end:Q", tooltip=[alt.Tooltip("label:N", title="")])]

    if gaps:
        quiet = pd.DataFrame({
            "hour": [hour_of_day(a) for a, _ in gaps],
            "end": [hour_of_day(b) for _, b in gaps],
            "label": [f"No movement {a:%H:%M}–{b:%H:%M} ({duration(a, b)})" for a, b in gaps],
        })
        layers.append(alt.Chart(quiet).mark_rect(color=ORANGE, opacity=0.22)
                      .encode(x=x, x2="end:Q",
                              tooltip=[alt.Tooltip("label:N", title="Quiet period")]))

    if not day_events.empty:
        points = day_events.assign(
            hour=day_events["time"].map(hour_of_day),
            clock=day_events["time"].dt.strftime("%H:%M"),
            sure=(day_events["confidence"] * 100).round().astype(int).astype(str) + "%",
            kind=day_events["activity"].eq("Fall").map({True: "Possible fall", False: "Activity"}),
        )
        order = [a for a in ACTIVITY_ORDER if a in set(points["activity"])]
        order += sorted(set(points["activity"]) - set(order))
        tooltip = [alt.Tooltip("clock:N", title="Time"),
                   alt.Tooltip("activity:N", title="Activity"),
                   alt.Tooltip("sure:N", title="Confidence")]
        if not falls.empty:
            layers.append(alt.Chart(points[points["activity"] == "Fall"])
                          .mark_rule(color=RED, strokeWidth=2, strokeDash=[4, 3])
                          .encode(x=x, tooltip=tooltip))
        layers.append(
            alt.Chart(points).mark_circle(size=120, opacity=0.95).encode(
                x=x,
                y=alt.Y("activity:N", sort=order, title=None,
                        axis=alt.Axis(grid=True, gridOpacity=0.12, domain=False, ticks=False)),
                color=alt.Color("kind:N", legend=None,
                                scale=alt.Scale(domain=["Activity", "Possible fall"],
                                                range=[BLUE, RED])),
                tooltip=tooltip,
            )
        )
    return _clean(alt.layer(*layers).properties(height=250))


def ring_gauge(fraction, big_text, small_text, color=VIOLET, size=220):
    """Open ring gauge (270 degrees) with text in the middle."""
    start, sweep = -0.75 * math.pi, 1.5 * math.pi
    end = start + sweep * max(0.0, min(1.0, fraction))
    arcs = pd.DataFrame({"s": [start, start], "e": [start + sweep, end],
                         "c": [TRACK, color]})
    ring = alt.Chart(arcs).mark_arc(innerRadius=size * 0.36, outerRadius=size * 0.43,
                                    cornerRadius=8).encode(
        theta=alt.Theta("s:Q", scale=None), theta2="e:Q",
        color=alt.Color("c:N", scale=None))
    big = alt.Chart(pd.DataFrame({"t": [big_text]})).mark_text(
        fontSize=40, fontWeight=700, dy=-8, color="#E8E9F5").encode(text="t:N")
    small = alt.Chart(pd.DataFrame({"t": [small_text]})).mark_text(
        fontSize=13, dy=26, color=GRAY).encode(text="t:N")
    return _clean(alt.layer(ring, big, small).properties(width=size, height=size))


def hourly_area(day_events, color=BLUE):
    """Detections per hour as a smooth area chart with a gradient fill."""
    counts = (day_events["time"].dt.hour.value_counts()
              .reindex(range(24), fill_value=0).rename_axis("hour").reset_index(name="n"))
    counts["label"] = counts["hour"].map(lambda h: f"{h:02d}:00–{h + 1:02d}:00")
    base = alt.Chart(counts).encode(
        x=alt.X("hour:Q", title=None, scale=alt.Scale(domain=[0, 23], nice=False),
                axis=alt.Axis(values=[0, 6, 12, 18, 23], grid=False, domain=False, ticks=False,
                              labelExpr="(datum.value < 10 ? '0' : '') + datum.value + 'h'")),
        y=alt.Y("n:Q", title=None, axis=alt.Axis(grid=True, gridOpacity=0.1, domain=False,
                                                 ticks=False, tickMinStep=1)),
        tooltip=[alt.Tooltip("label:N", title="Hour"), alt.Tooltip("n:Q", title="Detections")],
    )
    fill = alt.Gradient(gradient="linear", x1=0, x2=0, y1=1, y2=0,
                        stops=[alt.GradientStop(color="rgba(91,140,255,0.02)", offset=0),
                               alt.GradientStop(color="rgba(91,140,255,0.45)", offset=1)])
    area = base.mark_area(interpolate="monotone", line={"color": color, "strokeWidth": 2},
                          color=fill)
    dots = base.mark_point(size=1, opacity=0)  # wider hover target for the tooltip
    return _clean(alt.layer(area, dots).properties(height=130))


def activity_counts(day_events, color=BLUE):
    """Horizontal bars: how often each activity was detected."""
    counts = day_events["activity"].value_counts().rename_axis("activity").reset_index(name="n")
    bars = alt.Chart(counts).mark_bar(color=color, cornerRadiusEnd=6, height=18).encode(
        x=alt.X("n:Q", title="Times detected",
                axis=alt.Axis(grid=True, gridOpacity=0.1, domain=False, ticks=False, tickMinStep=1)),
        y=alt.Y("activity:N", sort="-x", title=None, axis=alt.Axis(domain=False, ticks=False)),
        tooltip=[alt.Tooltip("activity:N", title="Activity"),
                 alt.Tooltip("n:Q", title="Times detected")],
    )
    return _clean(bars.properties(height=alt.Step(30)))


def _clean(chart):
    """Transparent background and no frame, so charts sit directly on the card."""
    return chart.properties(background="transparent").configure_view(stroke=None)
