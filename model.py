"""
model.py — Safety classification for Dehradun Urban Safety Heatmap.

Replaces KMeans with a transparent, threshold-based classifier.

Rationale: KMeans on 10–22 synthetic data points is not genuine ML —
it behaves as a soft threshold with unnecessary randomness. This version
uses an explicit risk-index formula that is:
  - Reproducible across every run
  - Interpretable (you can read exactly why a zone is "Risky")
  - Easy to tune by adjusting SAFE_THRESHOLD / MEDIUM_THRESHOLD

The /predict endpoint still returns 'ai_class' for API compatibility.
"""

# ── Thresholds ────────────────────────────────────────────────────────────────
# risk_index = crime_score * 0.70 + isolation_penalty
# isolation_penalty = crowd below 35 at night adds up to +15 isolation risk
# Safe   : risk_index < 38
# Medium : risk_index < 60
# Risky  : risk_index >= 60

SAFE_THRESHOLD   = 38.0
MEDIUM_THRESHOLD = 60.0


def _compute_risk_index(crime_score: float, crowd_score: float) -> float:
    """
    Risk index: higher = more dangerous.
    - Crime is the primary driver (weight 0.70).
    - Very low crowd (< 35) adds isolation penalty — empty streets are
      dangerous too, even when base crime is moderate.
    """
    isolation_penalty = max(0.0, (35.0 - crowd_score) * 0.30)
    return crime_score * 0.70 + isolation_penalty


def predict_class(crime_score: float, crowd_score: float) -> str:
    """
    Predict safety classification for a single zone.
    Returns one of: 'Safe', 'Medium', 'Risky'.
    """
    risk = _compute_risk_index(crime_score, crowd_score)
    if risk < SAFE_THRESHOLD:
        return "Safe"
    if risk < MEDIUM_THRESHOLD:
        return "Medium"
    return "Risky"


def predict_batch(zone_data: list) -> list:
    """
    Classify a list of zone dicts.
    Each dict must have 'crime_score' and 'crowd_score'.
    Returns a copy with 'ai_class' and 'risk_index' added.
    """
    results = []
    for zone in zone_data:
        label = predict_class(zone["crime_score"], zone["crowd_score"])
        risk  = round(_compute_risk_index(zone["crime_score"], zone["crowd_score"]), 2)
        results.append({**zone, "ai_class": label, "risk_index": risk})
    return results
