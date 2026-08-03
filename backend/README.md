# EmberShield Backend

FastAPI backend for wildfire risk prediction. No manual image upload —
Gemini searches the web for a real photo of whatever location the
user picks on the map, then Claude / Gemini / live weather data
predict wildfire risk for that location.

## Pipeline

**Single location** — `POST /analyze`
```
Scout Agent (Gemini + Google Search grounding, finds a real photo)
    → Sentinel Agent (Claude Vision, assesses the photo)
    → Risk Analyst (live weather + spread model)
    → Commander (Claude, severity + recommended action + alert)
    → Excel log
```

**Multi-hotspot (bounding box)** — `POST /analyze-multi`
```
Scout Agent (samples 5 grid points across the box, searches each independently)
    → Multi-Hotspot Agent (Gemini, ONE combined multimodal call rates all found photos)
    → Risk Analyst + Commander (per hotspot, same as above)
    → Excel log
```

**Live reasoning** — `WS /ws/updates` streams each step above to the frontend.

## Setup

```bash
pip install -r requirements.txt
```

Edit `.env`:

```
GEMINI_API_KEY=...      # required — get one at https://aistudio.google.com/apikey
ANTHROPIC_API_KEY=...   # optional — without it, Sentinel/Commander/Multi-Hotspot* run in demo mode
```

\* see note below — multi-hotspot no longer uses Claude at all, only Gemini.

Run it:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## What's verified vs. what isn't

Everything here has been syntax-checked, and the pure-Python logic
(grid-point math, JSON fence-stripping, demo-mode fallbacks) has been
unit-tested in isolation. What has **not** been tested is the live
Gemini API calls in `agents/scout_agent.py` and
`agents/multi_hotspot_agent.py` — this was built with no network
access or API key available, directly against Google's published
`google-genai` SDK docs. If grounding metadata comes back in an
unexpected shape on your first real run, it fails closed (treated as
"nothing found" rather than crashing) — but the actual field-access
code may need a small correction. Run it, and if a search that should
find something comes back empty, share the raw `print(response)`
output and it can be fixed from there.

## Security

The `ANTHROPIC_API_KEY` / `GEMINI_API_KEY` values that were originally
in this project's `.env` were shared in a chat at some point in this
project's history and should be treated as compromised — rotate both
before deploying, even if you're not sure which ones were exposed.

## File overview

| File | Role |
|---|---|
| `main.py` | FastAPI app, routes, WebSocket manager wiring |
| `config.py` | All tunable constants (models, radii, thresholds) |
| `models.py` | Pydantic models matching the actual response shapes |
| `websocket_manager.py` | Broadcasts live agent reasoning to connected clients |
| `agents/scout_agent.py` | Gemini + Google Search grounding — finds real photos |
| `agents/sentinel_agent.py` | Claude Vision — fire detection on a single photo |
| `agents/multi_hotspot_agent.py` | Gemini — combined multi-photo risk scoring |
| `agents/risk_analyst_agent.py` | Live weather + fire spread model + nearby settlements |
| `agents/commander_agent.py` | Claude — severity, recommended action, alert message |
| `utils/excel_logger.py` | Appends every analysis to an Excel log |

Not included here: the frontend (Mapbox-based map UI) — none of those
files have been shared in this project yet.
