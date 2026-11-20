"""Plain-language summary of one day of activity.

summarize_day() is the only public function. It takes the same data the
dashboard already has and returns a short paragraph of text. Right now it
uses simple rules; later it can be swapped for an LLM call with the same
inputs and output, without touching app.py.
"""

# How each model label reads in a sentence
PHRASES = {
    "Walk": "walking",
    "Run": "running",
    "Sit down": "sitting down",
    "Stand up": "standing up",
    "Lie down": "lying down",
    "Pick up": "picking things up",
    "Fall": "a possible fall",
}


def _duration(delta):
    minutes = round(delta.total_seconds() / 60)
    hours, minutes = divmod(minutes, 60)
    if hours and minutes:
        return f"{hours} h {minutes} min"
    return f"{hours} h" if hours else f"{minutes} min"


def summarize_day(events, gaps, falls):
    """Describe one day in a few plain sentences.

    events: DataFrame with columns time, activity, confidence (one day only)
    gaps:   list of (start, end) datetimes with no detected activity
    falls:  DataFrame of Fall events with a boolean `confident` column
    Returns a string.
    """
    if events.empty:
        if gaps:
            return "No activity was detected at all on this day."
        return "There is no data for this day."

    first, last = events["time"].min(), events["time"].max()
    parts = [f"Activity was first detected at {first:%H:%M} "
             f"and last at {last:%H:%M}, with {len(events)} detections in total."]

    counts = events.loc[events["activity"] != "Fall", "activity"].value_counts()
    if not counts.empty:
        top = counts.index[0]
        parts.append(f"The most common activity was "
                     f"{PHRASES.get(top, top.lower())} ({counts.iloc[0]} times).")

    for start, end in gaps:
        parts.append(f"It was quiet from {start:%H:%M} to {end:%H:%M} "
                     f"({_duration(end - start)}) with no movement detected.")

    for _, fall in falls.iterrows():
        sure = "" if fall["confident"] else ", but the system was not very sure"
        sentence = f"A possible fall was detected at {fall['time']:%H:%M}{sure}."
        after = events[events["time"] > fall["time"]]
        if not after.empty:
            nxt = after.iloc[0]
            sentence += (f" Movement ({PHRASES.get(nxt['activity'], nxt['activity'].lower())})"
                         f" was seen again {_duration(nxt['time'] - fall['time'])} later.")
        else:
            sentence += " No movement has been detected since."
        parts.append(sentence)

    if not gaps and falls.empty:
        parts.append("Nothing unusual was noticed.")
    return " ".join(parts)
