"""
app.py — Flask backend for Dehradun Urban Safety Heatmap.

Improvements:
  - LRU cache on classified zone data (keyed by hour)
  - Restricted CORS to localhost origins only
  - New /zones endpoint for static zone metadata
  - Exposes risk_index from improved model

Routes:
  GET /            → service info
  GET /zones       → static zone list (names, coords, descriptions)
  GET /data        → zone data with computed scores
  GET /predict     → zone data + safety classification + risk_index
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
from functools import lru_cache

from data import get_all_zone_data, ZONES
from model import predict_batch

app = Flask(__name__)

# Restrict CORS to local dev origins only
CORS(app, origins=[
    "http://localhost:5500",
    "http://127.0.0.1:5500",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "null",           # file:// origin in some browsers
])


# ── Cache ─────────────────────────────────────────────────────────────────────

@lru_cache(maxsize=24)
def _cached_classify(hour: int) -> tuple:
    """
    Cached zone classification keyed by hour (0-23).
    Returns a tuple (hashable) of zone dicts.
    Cache is cleared on first request if needed.
    """
    zones = get_all_zone_data(hour)
    classified = predict_batch(zones)
    return tuple(classified)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _parse_hour() -> int | None:
    """Parse optional ?hour= query param (0-23). Returns None if absent/invalid."""
    raw = request.args.get("hour")
    if raw is None:
        return None
    try:
        h = int(raw)
        if 0 <= h <= 23:
            return h
    except ValueError:
        pass
    return None


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return jsonify({
        "service":   "Dehradun Urban Safety Heatmap API",
        "endpoints": ["/zones", "/data", "/predict"],
        "version":   "2.0.0",
        "zones":     len(ZONES),
    })


@app.route("/zones")
def get_zones():
    """
    Returns static zone metadata (no score computation).
    Useful for pre-populating frontend zone lists quickly.
    """
    static = [
        {
            "id":          z["id"],
            "name":        z["name"],
            "lat":         z["lat"],
            "lng":         z["lng"],
            "description": z["description"],
        }
        for z in ZONES
    ]
    return jsonify({"status": "ok", "count": len(static), "data": static})


@app.route("/data")
def get_data():
    """
    Returns zone data with computed crime/crowd/safety scores.

    Query params:
      hour (int, 0-23): simulate time of day (defaults to current hour)
    """
    hour = _parse_hour()
    from datetime import datetime
    resolved_hour = hour if hour is not None else datetime.now().hour
    zones = get_all_zone_data(resolved_hour)
    return jsonify({
        "status": "ok",
        "hour":   resolved_hour,
        "count":  len(zones),
        "data":   zones,
    })


@app.route("/predict")
def predict():
    """
    Returns zone data + safety classification + risk_index.

    Query params:
      hour (int, 0-23): simulate time of day (defaults to current hour)
    """
    hour = _parse_hour()
    from datetime import datetime
    resolved_hour = hour if hour is not None else datetime.now().hour

    classified = list(_cached_classify(resolved_hour))
    return jsonify({
        "status": "ok",
        "hour":   resolved_hour,
        "count":  len(classified),
        "data":   classified,
    })


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 55)
    print("  Dehradun Urban Safety Heatmap — Flask Backend v2")
    print("  Running at: http://127.0.0.1:5000")
    print("=" * 55)
    app.run(debug=True, port=5000)
