"""Shared ETA risk policy used by generated and online predictions.

Risk is based on predicted lateness against the promised delivery time, not
on disruption presence alone. Thresholds are business rules and should be
calibrated against historical operational outcomes before production use.
"""

def classify_eta_risk(predicted_delay_minutes: int) -> str:
    delay = max(0, int(predicted_delay_minutes or 0))
    if delay <= 30:
        return "LOW"
    if delay <= 120:
        return "MEDIUM"
    return "HIGH"
