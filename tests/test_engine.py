from datetime import datetime, timedelta
from engine.eta_engine import predict_eta, eligible_events
from engine.delay_classifier import classify_actual_delivery
from engine.anomaly_detector import detect_future_leakage, detect_delivered_in_transit, detect_impossible_leg_order
def test_eta_adjustments():
 t=datetime(2026,1,1); r=predict_eta(t,60,weather_minutes=30,facility_wait_minutes=10)
 assert r["predicted_eta"]==t+timedelta(minutes=100)
def test_no_future_event_leakage():
 t=datetime(2026,1,1,10)
 ev=[{"event_time":t-timedelta(minutes=5),"ingestion_time":t-timedelta(minutes=2)},
     {"event_time":t+timedelta(minutes=5),"ingestion_time":t+timedelta(minutes=6)}]
 assert len(eligible_events(ev,t))==1
def test_future_leakage_flag():
 t=datetime(2026,1,1,10)
 assert detect_future_leakage(t,t+timedelta(minutes=1))
def test_lifecycle_anomaly():
 assert detect_delivered_in_transit("IN_TRANSIT",True)
def test_impossible_sequence():
 assert detect_impossible_leg_order([1,3,2])
def test_delay_label_is_derived():
 p=datetime(2026,1,2); a=p+timedelta(minutes=45)
 assert classify_actual_delivery(a,p)==("DELAYED",45)


def test_eta_risk_bands():
 from engine.risk import classify_eta_risk
 assert classify_eta_risk(0) == "LOW"
 assert classify_eta_risk(30) == "LOW"
 assert classify_eta_risk(31) == "MEDIUM"
 assert classify_eta_risk(120) == "MEDIUM"
 assert classify_eta_risk(121) == "HIGH"


def test_eta_engine_uses_risk_bands():
 t = datetime(2026, 1, 1, 8)
 promise = t + timedelta(minutes=90)
 low = predict_eta(t, 60, promised_eta=promise)
 medium = predict_eta(t, 130, promised_eta=promise)
 high = predict_eta(t, 220, promised_eta=promise)
 assert low["risk_level"] == "LOW"
 assert medium["risk_level"] == "MEDIUM"
 assert high["risk_level"] == "HIGH"


def test_eligible_events_requires_event_and_ingestion_before_cutoff():
    from datetime import datetime
    from engine.eta_engine import eligible_events
    cutoff=datetime(2026,1,1,10,0,0)
    rows=[
      {"event_id":"A","event_time":datetime(2026,1,1,9,0,0),"ingestion_time":datetime(2026,1,1,9,5,0)},
      {"event_id":"B","event_time":datetime(2026,1,1,9,0,0),"ingestion_time":datetime(2026,1,1,10,1,0)},
      {"event_id":"C","event_time":datetime(2026,1,1,10,1,0),"ingestion_time":datetime(2026,1,1,9,5,0)},
    ]
    assert [x["event_id"] for x in eligible_events(rows,cutoff)] == ["A"]
