"""
data.py — Structured dataset for Dehradun zones.
Improvements:
  - 22 zones (up from 10) for better heatmap coverage
  - Time-variable crime scores (night multipliers per zone)
  - Sinusoidal crowd curve instead of binary on/off
  - Revised safety_score formula (higher = safer, more intuitive)
"""

import math
from datetime import datetime


# ── Zone Definitions ──────────────────────────────────────────────────────────
ZONES = [
    {
        "id": 1,
        "name": "Rajpur Road",
        "lat": 30.3433,
        "lng": 78.0631,
        "base_crime_score": 35,
        "busy": True,
        "description": "Major commercial and residential corridor"
    },
    {
        "id": 2,
        "name": "ISBT Dehradun",
        "lat": 30.2963,
        "lng": 78.0285,
        "base_crime_score": 62,
        "busy": True,
        "description": "Inter-State Bus Terminal — high footfall, elevated night risk"
    },
    {
        "id": 3,
        "name": "Ballupur",
        "lat": 30.3074,
        "lng": 78.0723,
        "base_crime_score": 28,
        "busy": False,
        "description": "Residential zone near ONGC campus"
    },
    {
        "id": 4,
        "name": "Prem Nagar",
        "lat": 30.2872,
        "lng": 77.9960,
        "base_crime_score": 55,
        "busy": False,
        "description": "Suburban locality on Haridwar road"
    },
    {
        "id": 5,
        "name": "Clement Town",
        "lat": 30.2623,
        "lng": 78.0110,
        "base_crime_score": 48,
        "busy": False,
        "description": "Mixed-use zone with military presence"
    },
    {
        "id": 6,
        "name": "Sahastradhara Road",
        "lat": 30.3612,
        "lng": 78.1022,
        "base_crime_score": 22,
        "busy": False,
        "description": "Scenic road towards sulphur springs — generally calm"
    },
    {
        "id": 7,
        "name": "Clock Tower (Ghanta Ghar)",
        "lat": 30.3204,
        "lng": 78.0430,
        "base_crime_score": 45,
        "busy": True,
        "description": "Central landmark and commercial hub — busy evenings"
    },
    {
        "id": 8,
        "name": "Rispana Bridge",
        "lat": 30.3005,
        "lng": 78.0550,
        "base_crime_score": 58,
        "busy": False,
        "description": "Urban junction near Rispana River — elevated late-night risk"
    },
    {
        "id": 9,
        "name": "Dalanwala",
        "lat": 30.3280,
        "lng": 78.0592,
        "base_crime_score": 30,
        "busy": False,
        "description": "Old Dehradun residential locality"
    },
    {
        "id": 10,
        "name": "Karanpur",
        "lat": 30.3155,
        "lng": 78.0395,
        "base_crime_score": 50,
        "busy": True,
        "description": "Busy market area in central Dehradun"
    },
    {
        "id": 11,
        "name": "Paltan Bazaar",
        "lat": 30.3168,
        "lng": 78.0342,
        "base_crime_score": 52,
        "busy": True,
        "description": "Dense retail market near railway station"
    },
    {
        "id": 12,
        "name": "Dehradun Railway Station",
        "lat": 30.3138,
        "lng": 78.0340,
        "base_crime_score": 60,
        "busy": True,
        "description": "Major rail hub — peak crowd at train arrivals"
    },
    {
        "id": 13,
        "name": "Mussoorie Diversion",
        "lat": 30.3680,
        "lng": 78.0725,
        "base_crime_score": 32,
        "busy": False,
        "description": "Junction towards Mussoorie hills — tourist transit zone"
    },
    {
        "id": 14,
        "name": "Niranjanpur",
        "lat": 30.3046,
        "lng": 78.0848,
        "base_crime_score": 42,
        "busy": False,
        "description": "Residential and commercial mix on Ring Road"
    },
    {
        "id": 15,
        "name": "Chakrata Road",
        "lat": 30.3369,
        "lng": 77.9989,
        "base_crime_score": 38,
        "busy": False,
        "description": "Western corridor towards Chakrata hills"
    },
    {
        "id": 16,
        "name": "Doiwala",
        "lat": 30.1834,
        "lng": 78.1180,
        "base_crime_score": 44,
        "busy": False,
        "description": "Small town on Rishikesh road, semi-rural"
    },
    {
        "id": 17,
        "name": "Raipur Road",
        "lat": 30.3542,
        "lng": 78.0912,
        "base_crime_score": 26,
        "busy": False,
        "description": "Quieter route through forest-adjacent neighbourhoods"
    },
    {
        "id": 18,
        "name": "Nehru Colony",
        "lat": 30.3095,
        "lng": 78.0635,
        "base_crime_score": 33,
        "busy": False,
        "description": "Dense residential colony, moderate activity"
    },
    {
        "id": 19,
        "name": "Haridwar Bypass",
        "lat": 30.2715,
        "lng": 78.0048,
        "base_crime_score": 65,
        "busy": False,
        "description": "Highway stretch — isolated at night"
    },
    {
        "id": 20,
        "name": "Sewla Kalan",
        "lat": 30.2550,
        "lng": 78.0370,
        "base_crime_score": 70,
        "busy": False,
        "description": "Peripheral zone, lower surveillance density"
    },
    {
        "id": 21,
        "name": "EC Road",
        "lat": 30.3342,
        "lng": 78.0518,
        "base_crime_score": 29,
        "busy": False,
        "description": "University-area road, safe during day"
    },
    {
        "id": 22,
        "name": "Bindal Bridge",
        "lat": 30.2924,
        "lng": 78.0721,
        "base_crime_score": 55,
        "busy": False,
        "description": "River crossing — poor lighting, elevated night risk"
    },
]


# ── Night / Early-Morning Risk Multipliers ────────────────────────────────────
# Each entry: zone name → (hour_range, multiplier)
TIME_RISK = {
    "ISBT Dehradun":             [(range(22, 24), 1.45), (range(0, 5), 1.50)],
    "Rispana Bridge":            [(range(22, 24), 1.40), (range(0, 6), 1.60)],
    "Haridwar Bypass":           [(range(21, 24), 1.50), (range(0, 5), 1.55)],
    "Sewla Kalan":               [(range(20, 24), 1.55), (range(0, 5), 1.60)],
    "Bindal Bridge":             [(range(21, 24), 1.45), (range(0, 5), 1.50)],
    "Dehradun Railway Station":  [(range(23, 24), 1.35), (range(0, 5), 1.30)],
    "Clock Tower (Ghanta Ghar)": [(range(22, 24), 1.30)],
    "Prem Nagar":                [(range(22, 24), 1.25), (range(0, 5), 1.30)],
    "Clement Town":              [(range(0,  5),  1.25)],
}


def get_crime_score(zone: dict, hour: int) -> int:
    """
    Compute crime score for a zone at a given hour.
    Applies time-based multipliers for high-risk zones at night/early morning.
    Returns an integer clamped to [0, 100].
    """
    base = zone["base_crime_score"]
    entries = TIME_RISK.get(zone["name"], [])
    for hour_range, mult in entries:
        if hour in hour_range:
            return min(100, int(base * mult))
    return base


def get_crowd_score(zone: dict, hour: int) -> int:
    """
    Sinusoidal crowd curve.
    - Busy zones: base=65, amplitude=28, peak ~14:00
    - Quiet zones: base=42, amplitude=22, peak ~12:00
    - Trough at ~03:00 for all zones
    Clamped to [5, 95].
    """
    if zone["busy"]:
        base, amplitude = 65, 28
    else:
        base, amplitude = 42, 22

    trough_h = 3
    angle = math.pi * (hour - trough_h) / 20.0
    score = base + amplitude * math.sin(angle)
    return int(max(5, min(95, score)))


def compute_safety_score(crime_score: float, crowd_score: float) -> float:
    """
    Revised formula — higher score = safer area (more intuitive).
      - Crime weighted at 0.65 (primary risk driver)
      - Excess crowd above 60 adds congestion / pickpocket risk (weight 0.30)
    Clamped to [0, 100].
    """
    crowd_risk = max(0.0, crowd_score - 60.0) * 0.30
    raw = 100.0 - (crime_score * 0.65) - crowd_risk
    return round(max(0.0, min(100.0, raw)), 2)


def get_all_zone_data(hour: int = None) -> list:
    """Return full zone data with computed scores for a given hour."""
    if hour is None:
        hour = datetime.now().hour

    results = []
    for zone in ZONES:
        crime  = get_crime_score(zone, hour)
        crowd  = get_crowd_score(zone, hour)
        safety = compute_safety_score(crime, crowd)
        results.append({
            "id":           zone["id"],
            "name":         zone["name"],
            "lat":          zone["lat"],
            "lng":          zone["lng"],
            "crime_score":  crime,
            "crowd_score":  crowd,
            "safety_score": safety,
            "description":  zone["description"],
        })
    return results
