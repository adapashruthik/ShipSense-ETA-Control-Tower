from datetime import datetime, timedelta
from engine.risk import classify_eta_risk


def predict_eta(prediction_time, remaining_minutes, weather_minutes=0, facility_wait_minutes=0,
                route_change_minutes=0, carrier_adjustment_minutes=0, promised_eta=None):
    """Explainable additive ETA rule. Caller must supply point-in-time eligible features only."""
    adjustments = {
        "weather": max(0, int(weather_minutes)),
        "facility": max(0, int(facility_wait_minutes)),
        "route": max(0, int(route_change_minutes)),
        "carrier": max(0, int(carrier_adjustment_minutes)),
    }
    baseline = prediction_time + timedelta(minutes=max(0, int(remaining_minutes)))
    predicted = baseline + timedelta(minutes=sum(adjustments.values()))
    delay = max(0, int((predicted - promised_eta).total_seconds() / 60)) if promised_eta else 0
    return {
        "baseline_eta": baseline,
        "predicted_eta": predicted,
        "adjustments": adjustments,
        "predicted_delay_minutes": delay,
        "risk_level": classify_eta_risk(delay),
        "rule_version": "rules-v2.1",
    }


def eligible_events(events, prediction_time):
    """Prevent temporal leakage: both event time and ingestion time must be at/before cutoff."""
    return [e for e in events if e["event_time"] <= prediction_time and e["ingestion_time"] <= prediction_time]


# Source-backed point-in-time feature derivation used by the synthetic generator and API.
def _parse(value):
    return datetime.strptime(value, "%Y-%m-%d %H:%M:%S") if value else None

def derive_source_features(prediction_time, shipment, carrier, legs, events, queues, weather,
                  route_history, carrier_calendar, facility_calendar, routes, facilities):
    """Derive only from source rows visible at the prediction cutoff."""
    cutoff = prediction_time
    eligible = [e for e in events if _parse(e["event_time"]) <= cutoff
                and _parse(e["ingestion_time"]) <= cutoff and not int(e.get("is_duplicate", 0))]
    eligible.sort(key=lambda e: (_parse(e["event_time"]), e["event_id"]))
    shipment_legs = sorted([x for x in legs if x["shipment_id"] == shipment["shipment_id"]],
                           key=lambda x: x["sequence_no"])
    elapsed = max(0.0, (cutoff - _parse(shipment["created_at"])).total_seconds()/3600)
    route_by_id = {r["route_id"]: r for r in routes}
    total_hours = sum(float(route_by_id[x["route_id"]]["base_transit_hours"]) for x in shipment_legs)
    remaining_hours = max(0.25, total_hours - elapsed)
    # A visible arrival/departure event advances the active leg; no future event is consulted.
    visible_leg_ids = {e.get("leg_id") for e in eligible}
    completed = sum(1 for leg in shipment_legs if leg["leg_status"] == "COMPLETED"
                    and leg["leg_id"] in visible_leg_ids)
    if completed:
        remaining_hours = max(0.25, sum(float(route_by_id[x["route_id"]]["base_transit_hours"]) for x in shipment_legs[completed:]))
    route_adj = 0
    for change in route_history:
        if change["shipment_id"] == shipment["shipment_id"] and _parse(change["effective_at"]) <= cutoff:
            route_adj += int(change["transit_adjustment_minutes"])
    active_route_ids = {x["route_id"] for x in shipment_legs[completed:]}
    region_by_fac = {f["facility_id"]: f["region"] for f in facilities}
    route_regions = {region_by_fac.get(r["origin_facility_id"]) for r in routes if r["route_id"] in active_route_ids}
    weather_adj = sum(int(w["travel_impact_minutes"]) for w in weather
        if w["region"] in route_regions and _parse(w["start_time"]) <= cutoff < _parse(w["end_time"]))
    relevant_facilities = {route_by_id[x["route_id"]]["destination_facility_id"] for x in shipment_legs[completed:]}
    visible_queues = [q for q in queues if q["facility_id"] in relevant_facilities
                      and _parse(q["queue_time"]) <= cutoff]
    facility_adj = 0
    for fid in relevant_facilities:
        qrows = [q for q in visible_queues if q["facility_id"] == fid]
        if qrows:
            latest = max(qrows, key=lambda q: _parse(q["queue_time"]))
            facility_adj += int(float(latest["estimated_wait_minutes"]))
    for cal in facility_calendar:
        if cal["facility_id"] in relevant_facilities and _parse(cal["start_time"]) <= cutoff < _parse(cal["end_time"]):
            facility_adj += int(cal["disruption_minutes"])
    reliability = float(carrier["reliability_score"])
    carrier_adj = max(0, round((100-reliability)*2))
    for cal in carrier_calendar:
        if cal["carrier_id"] == carrier["carrier_id"] and _parse(cal["effective_from"]) <= cutoff < _parse(cal["effective_to"]):
            carrier_adj += int(cal["adjustment_minutes"])
    return remaining_hours, weather_adj, facility_adj, route_adj, carrier_adj, eligible

