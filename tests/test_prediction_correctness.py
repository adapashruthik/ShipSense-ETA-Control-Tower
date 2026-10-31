
from copy import deepcopy
from datetime import datetime, timedelta

from engine.eta_engine import derive_source_features, predict_eta

CUTOFF = datetime(2026, 10, 31, 10, 0, 0)

def fixture():
    shipment = {"shipment_id": "SHP-TEST-1", "created_at": "2026-10-31 09:00:00"}
    carrier = {"carrier_id": "CAR-1", "reliability_score": 100}
    facilities = [
        {"facility_id": "FAC-A", "region": "NORTH"},
        {"facility_id": "FAC-B", "region": "NORTH"},
        {"facility_id": "FAC-C", "region": "SOUTH"},
    ]
    routes = [
        {"route_id": "R-1", "origin_facility_id": "FAC-A", "destination_facility_id": "FAC-B",
         "base_transit_hours": 6},
        {"route_id": "R-2", "origin_facility_id": "FAC-B", "destination_facility_id": "FAC-C",
         "base_transit_hours": 4},
    ]
    legs = [
        {"leg_id": "LEG-1", "shipment_id": "SHP-TEST-1", "route_id": "R-1",
         "sequence_no": 1, "leg_status": "COMPLETED"},
        {"leg_id": "LEG-2", "shipment_id": "SHP-TEST-1", "route_id": "R-2",
         "sequence_no": 2, "leg_status": "PLANNED"},
    ]
    events = []
    queues = [{"queue_id": "Q-1", "facility_id": "FAC-B", "queue_time": "2026-10-31 09:30:00",
               "estimated_wait_minutes": 10}]
    weather = []
    route_history = []
    carrier_calendar = []
    facility_calendar = []
    return (shipment, carrier, legs, events, queues, weather, route_history,
            carrier_calendar, facility_calendar, routes, facilities)

def calculate(data, at=CUTOFF):
    shipment, carrier, legs, events, queues, weather, route_history, carrier_calendar, facility_calendar, routes, facilities = data
    remaining_hours, weather_min, facility_min, route_min, carrier_min, eligible = derive_source_features(
        at, shipment, carrier, legs, events, queues, weather, route_history,
        carrier_calendar, facility_calendar, routes, facilities
    )
    result = predict_eta(at, remaining_hours * 60, weather_min, facility_min,
                         route_min, carrier_min)
    return result, eligible

def test_weather_change_changes_eta_in_expected_direction():
    data = fixture()
    baseline, _ = calculate(data)
    data[5].append({"weather_event_id":"W-1","region":"NORTH",
                    "start_time":"2026-10-31 09:00:00","end_time":"2026-10-31 12:00:00",
                    "travel_impact_minutes":45})
    severe, _ = calculate(data)
    assert severe["predicted_eta"] == baseline["predicted_eta"] + timedelta(minutes=45)
    assert severe["adjustments"]["weather"] == 45

def test_facility_queue_change_changes_eta_in_expected_direction():
    data = fixture()
    baseline, _ = calculate(data)
    data[4].append({"queue_id":"Q-2","facility_id":"FAC-B","queue_time":"2026-10-31 09:45:00",
                    "estimated_wait_minutes":70})
    congested, _ = calculate(data)
    assert congested["predicted_eta"] == baseline["predicted_eta"] + timedelta(minutes=60)
    assert congested["adjustments"]["facility"] == 70

def test_route_plan_change_changes_eta_in_expected_direction():
    data = fixture()
    baseline, _ = calculate(data)
    # Route plan R-2 now requires 2 additional transit hours.
    data[9][1]["base_transit_hours"] = 6
    revised, _ = calculate(data)
    assert revised["predicted_eta"] == baseline["predicted_eta"] + timedelta(hours=2)

def test_effective_route_change_history_changes_eta():
    data = fixture()
    baseline, _ = calculate(data)
    data[6].append({"route_change_id":"RC-1","shipment_id":"SHP-TEST-1",
                    "effective_at":"2026-10-31 09:50:00","transit_adjustment_minutes":35})
    revised, _ = calculate(data)
    assert revised["predicted_eta"] == baseline["predicted_eta"] + timedelta(minutes=35)
    assert revised["adjustments"]["route"] == 35

def test_new_eligible_carrier_event_advances_eta():
    data = fixture()
    baseline, eligible_before = calculate(data)
    data[3].append({"event_id":"EV-1","leg_id":"LEG-1","event_type":"ARRIVED_FACILITY",
                    "event_time":"2026-10-31 09:40:00","ingestion_time":"2026-10-31 09:45:00",
                    "is_duplicate":0})
    updated, eligible_after = calculate(data)
    assert len(eligible_after) == 1
    assert updated["predicted_eta"] < baseline["predicted_eta"]
    assert updated["predicted_eta"] == CUTOFF + timedelta(hours=4)

def test_future_event_does_not_change_prediction():
    data = fixture()
    baseline, eligible_before = calculate(data)
    data[3].append({"event_id":"EV-FUTURE","leg_id":"LEG-1","event_type":"ARRIVED_FACILITY",
                    "event_time":"2026-10-31 10:30:00","ingestion_time":"2026-10-31 10:35:00",
                    "is_duplicate":0})
    after, eligible_after = calculate(data)
    assert after["predicted_eta"] == baseline["predicted_eta"]
    assert eligible_after == eligible_before

def test_future_weather_queue_route_change_and_calendar_are_ignored():
    data = fixture()
    baseline, _ = calculate(data)
    data[5].append({"weather_event_id":"W-FUTURE","region":"NORTH",
                    "start_time":"2026-10-31 10:05:00","end_time":"2026-10-31 12:00:00",
                    "travel_impact_minutes":120})
    data[4].append({"queue_id":"Q-FUTURE","facility_id":"FAC-B","queue_time":"2026-10-31 10:05:00",
                    "estimated_wait_minutes":200})
    data[6].append({"route_change_id":"RC-FUTURE","shipment_id":"SHP-TEST-1",
                    "effective_at":"2026-10-31 10:05:00","transit_adjustment_minutes":180})
    data[7].append({"calendar_id":"CAL-FUTURE","carrier_id":"CAR-1",
                    "effective_from":"2026-10-31 10:05:00","effective_to":"2026-10-31 12:00:00",
                    "adjustment_minutes":90})
    data[8].append({"disruption_id":"FD-FUTURE","facility_id":"FAC-B",
                    "start_time":"2026-10-31 10:05:00","end_time":"2026-10-31 12:00:00",
                    "disruption_minutes":80})
    after, _ = calculate(data)
    assert after["predicted_eta"] == baseline["predicted_eta"]

def test_late_ingested_event_is_not_used_even_if_event_time_is_old():
    data = fixture()
    baseline, _ = calculate(data)
    data[3].append({"event_id":"EV-LATE","leg_id":"LEG-1","event_type":"ARRIVED_FACILITY",
                    "event_time":"2026-10-31 09:20:00","ingestion_time":"2026-10-31 10:01:00",
                    "is_duplicate":0})
    after, eligible = calculate(data)
    assert after["predicted_eta"] == baseline["predicted_eta"]
    assert eligible == []
