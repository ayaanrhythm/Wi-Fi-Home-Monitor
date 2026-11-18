# WiFi-Based Smart Home Activity Monitoring Agent

Recognizes activities (walking, sitting, falling, ...) from WiFi CSI signals
captured by ESP32 boards, logs them, and shows them on a dashboard with alerts.
Final demo: **Dec 7, 2026**.

## Setup

Needs Python 3.10+ and Git. Run in PowerShell (e.g. the VS Code terminal).

```powershell
git clone <repo-url>
cd wifi-home-monitor
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python download_data.py         # gets the UT-HAR dataset (~380 MB)
python train.py                 # trains the model
```

If `Activate.ps1` says running scripts is disabled, run
`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once and try again.

If Google Drive blocks the download, get `UT_HAR.zip` from a teammate and run
`python download_data.py C:\path\to\UT_HAR.zip`.

## Commands

Activate the venv first in each new terminal (`.\.venv\Scripts\Activate.ps1`).

```powershell
python simulate_day.py               # fill the activity log with a simulated day
python show_log.py                   # view the log and alerts in the terminal
python -m streamlit run app.py       # open the dashboard
python predict.py                    # try the model on sample windows
```

Note: the 95.8% test accuracy is optimistic, since UT-HAR's test windows
overlap its training windows.

## Remaining tasks

- Check which UT-HAR label number is which activity
- LLM agent that answers questions from the activity log
- Record empty-room data on the ESP32 and add it as a class
- Live ESP32 data collection and prediction
- Measure accuracy on data the model hasn't seen
- Dashboard polish
- Demo script (with the simulated day as a fallback)
