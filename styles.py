"""Custom CSS for the dashboard.

Colors and fonts live in .streamlit/config.toml. This file adds what the
theme can't do: card surfaces, the tall hero panel, chips, tiles, and table
rows. Every rule targets a container key (st.container(key=...) ->
.st-key-<key>), never Streamlit's private classes.

Optional hero photo: put an image at static/hero.jpg and restart Streamlit.
"""

from pathlib import Path

import streamlit as st

HERO_IMAGE = Path(__file__).parent / "static" / "hero.jpg"

TINTS = {
    "green": "rgba(61, 214, 140, 0.30)",
    "orange": "rgba(245, 165, 36, 0.32)",
    "red": "rgba(255, 92, 108, 0.36)",
    "violet": "rgba(108, 92, 231, 0.38)",
}

CSS = """
<style>
/* Cards: any container whose key starts with "card-" */
[class*="st-key-card-"] {
    background: linear-gradient(180deg, #171A38 0%, #12142C 100%);
    border: 1px solid #23274A;
    border-radius: 22px;
    padding: 1.3rem 1.5rem;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.30);
}
[class*="st-key-card-"] h3 { font-size: 1.15rem; }

/* Hero: tall panel, content pinned to top and bottom */
.st-key-hero {
    min-height: 420px;
    justify-content: space-between;
    border-radius: 26px;
    padding: 2rem 2.2rem;
    border: 1px solid #23274A;
    background: HERO_BACKGROUND;
    background-size: cover;
    background-position: center;
    box-shadow: 0 14px 40px rgba(0, 0, 0, 0.40);
}
.st-key-hero h1 { font-size: 3rem; line-height: 1.1; }

/* Small rounded chips (hero stats) */
[class*="st-key-chip-"] {
    background: rgba(12, 14, 34, 0.55);
    backdrop-filter: blur(6px);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 14px;
    padding: 0 1rem;
    min-height: 2.6rem;
    justify-content: center;   /* vertical centering (the container is a flex column) */
    align-items: center;
}
[class*="st-key-chip-"] p { margin: 0; font-size: 0.92rem; line-height: 1; }

/* Streamlit gives text blocks a -1rem bottom margin; inside these small
   boxes that makes the box shorter than its text, so cancel it. */
[class*="st-key-chip-"] div,
[class*="st-key-tile-"] div,
[class*="st-key-row-"] div,
.st-key-hero-status div { margin-bottom: 0 !important; }

/* Status line in the hero's top-right corner */
.st-key-hero-status p { margin: 0; line-height: 1.5; }

/* Rows in the monitoring card: [icon] Name ........ value */
[class*="st-key-tile-"] {
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 14px;
    padding: 0.5rem 0.8rem 0.5rem 0.5rem;
}
[class*="st-key-tile-"] p { margin: 0; font-size: 0.88rem; line-height: 1.3; white-space: nowrap; }
/* Small colored square behind each icon */
[class*="st-key-tile-icon-"] {
    border-radius: 10px;
    flex-shrink: 0;
    padding: 0 !important;
    border: none;
    justify-content: center;
    align-items: center;
}
[class*="st-key-tile-icon-green"]  { background: rgba(61, 214, 140, 0.14); }
[class*="st-key-tile-icon-violet"] { background: rgba(142, 124, 255, 0.16); }
[class*="st-key-tile-icon-"] p { font-size: 1.1rem; line-height: 1; margin-right: -0.5rem; }

/* Recent activity table rows: compact, like a device list */
[class*="st-key-row-"] {
    border-top: 1px solid rgba(255, 255, 255, 0.06);
    padding: 0.35rem 0;
}
[class*="st-key-row-"] p { margin: 0; font-size: 0.9rem; line-height: 1.35; }
[class*="st-key-row-"] small { font-size: 0.75rem; }
.st-key-row-head p { font-size: 0.78rem; color: #8A8FB3; }
.st-key-row-head { border-top: none; }
</style>
"""


def inject(status_color):
    tint = TINTS[status_color]
    layers = [f"radial-gradient(110% 120% at 100% 0%, {tint} 0%, transparent 55%)"]
    if HERO_IMAGE.exists():
        layers += ["linear-gradient(180deg, rgba(11,13,33,0.55) 0%, rgba(11,13,33,0.15) 45%, "
                   "rgba(11,13,33,0.85) 100%)",
                   "url('app/static/hero.jpg')"]
    else:
        # No photo: layered night-sky gradients instead
        layers += ["radial-gradient(60% 50% at 25% 85%, rgba(108,92,231,0.25) 0%, transparent 70%)",
                   "radial-gradient(40% 35% at 80% 75%, rgba(91,140,255,0.18) 0%, transparent 70%)",
                   "linear-gradient(160deg, #1D2050 0%, #12143A 45%, #0B0D21 100%)"]
    st.html(CSS.replace("HERO_BACKGROUND", ", ".join(layers)))
