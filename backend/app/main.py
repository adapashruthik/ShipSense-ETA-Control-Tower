import csv
import io
import json
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Query, UploadFile, File
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy import text

from .db import query, engine
from engine.risk import classify_eta_risk

ROOT = Path(__file__).resolve().parents[2]
app = FastAPI(
    title="ShipSense Logistics Intelligence API",
    version="2.0.0",
    description="Traceable shipment ingestion, ETA prediction, delay intelligence and data-quality API."
)

class ShipmentInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    origin_facility_id: str = Field(min_length=1, max_length=30)
    destination_facility_id: str = Field(min_length=1, max_length=30)
    carrier_id: str = Field(min_length=1, max_length=30)
    service_level_id: str = Field(min_length=1, max_length=30)
    promised_delivery_at: datetime
    total_distance_km: float = Field(gt=0, le=10000)
    weather_condition: str = "CLEAR"
    facility_wait_minutes: int = Field(default=0, ge=0, le=10080)
    priority: str = "MEDIUM"

def _create_shipment(conn, payload: dict):
    now = datetime.utcnow().replace(microsecond=0)
    origin = payload["origin_facility_id"]
    destination = payload["destination_facility_id"]
    if origin == destination:
        raise ValueError("Origin and destination facilities must be different.")

    for table, key, value in [
        ("facilities", "facility_id", origin),
        ("facilities", "facility_id", destination),
        ("carriers", "carrier_id", payload["carrier_id"]),
        ("service_levels", "service_level_id", payload["service_level_id"]),
    ]:
        exists = conn.execute(
            text(f"SELECT 1 FROM {table} WHERE {key}=:value"),
            {"value": value}
        ).first()
        if not exists:
            raise ValueError(f"Unknown {key}: {value}")

    seq = conn.execute(text("""
        SELECT COALESCE(MAX(CAST(SUBSTRING(shipment_id, 10) AS UNSIGNED)), 0) + 1
        FROM shipments WHERE shipment_id LIKE 'SHP-2026-%'
    """)).scalar_one()
    shipment_id = f"SHP-2026-{int(seq):06d}"
    leg_id = f"LEG-{shipment_id}-01"
    route_id = f"RTE-MAN-{int(seq):06d}"
    event_id = f"EVT-{shipment_id}-000001"
    prediction_time = now
    stamp = now.strftime("%Y%m%dT%H%M%SZ")
    eta_id = f"ETA-{shipment_id}-{stamp}"

    distance = float(payload["total_distance_km"])
    # Explainable baseline speed assumptions; these are configurable business rules, not live traffic data.
    service_speed = {"SVC-EXPRESS": 58, "SVC-PRIORITY": 62, "SVC-STANDARD": 45}
    service_id = payload["service_level_id"]
    speed = service_speed.get(service_id, 48)
    remaining_minutes = max(1, round(distance / speed * 60))
    baseline_eta = now + timedelta(minutes=remaining_minutes)

    weather = str(payload.get("weather_condition", "CLEAR")).upper()
    weather_adjustments = {
        "CLEAR": 0, "LIGHT_RAIN": 10, "HEAVY_RAIN": 35,
        "FOG": 25, "STORM": 75, "FLOODING": 120
    }
    weather_minutes = weather_adjustments.get(weather)
    if weather_minutes is None:
        raise ValueError("weather_condition must be CLEAR, LIGHT_RAIN, HEAVY_RAIN, FOG, STORM or FLOODING.")

    facility_minutes = int(payload.get("facility_wait_minutes", 0))
    carrier_score = conn.execute(
        text("SELECT reliability_score FROM carriers WHERE carrier_id=:id"),
        {"id": payload["carrier_id"]}
    ).scalar_one()
    carrier_minutes = max(0, round((100 - float(carrier_score)) * 2))
    priority = str(payload.get("priority", "MEDIUM")).upper()
    if priority not in {"LOW", "MEDIUM", "HIGH"}:
        raise ValueError("priority must be LOW, MEDIUM or HIGH.")
    # Priority is captured as an explicit, auditable adjustment in the route adjustment field.
    route_minutes = {"HIGH": 0, "MEDIUM": 10, "LOW": 20}[priority]
    predicted_eta = baseline_eta + timedelta(minutes=weather_minutes + facility_minutes + route_minutes + carrier_minutes)
    promised = payload["promised_delivery_at"]
    delay_minutes = max(0, round((predicted_eta - promised).total_seconds() / 60))
    risk = classify_eta_risk(delay_minutes)

    conn.execute(text("""
        INSERT INTO routes(route_id,origin_facility_id,destination_facility_id,distance_km,base_transit_hours)
        VALUES(:route,:origin,:destination,:distance,:hours)
    """), {"route": route_id, "origin": origin, "destination": destination,
           "distance": distance, "hours": round(remaining_minutes / 60, 2)})

    conn.execute(text("""
        INSERT INTO shipments(shipment_id,carrier_id,service_level_id,origin_facility_id,
        destination_facility_id,created_at,promised_delivery_at,actual_delivery_at,status,
        total_distance_km,issue_type)
        VALUES(:sid,:carrier,:service,:origin,:destination,:created,:promised,NULL,'CREATED',:distance,NULL)
    """), {"sid": shipment_id, "carrier": payload["carrier_id"], "service": service_id,
           "origin": origin, "destination": destination, "created": now,
           "promised": promised, "distance": distance})

    conn.execute(text("""
        INSERT INTO shipment_legs(leg_id,shipment_id,route_id,carrier_id,sequence_no,
        planned_departure_at,planned_arrival_at,actual_departure_at,actual_arrival_at,leg_status)
        VALUES(:leg,:sid,:route,:carrier,1,:departure,:arrival,NULL,NULL,'PLANNED')
    """), {"leg": leg_id, "sid": shipment_id, "route": route_id,
           "carrier": payload["carrier_id"], "departure": now, "arrival": baseline_eta})

    conn.execute(text("""
        INSERT INTO tracking_events(event_id,shipment_id,leg_id,carrier_id,event_type,event_location,
        event_time,ingestion_time,source_system,is_duplicate,issue_type)
        VALUES(:event,:sid,:leg,:carrier,'CREATED',:location,:event_time,:ingestion,'MANUAL_ENTRY',0,NULL)
    """), {"event": event_id, "sid": shipment_id, "leg": leg_id,
           "carrier": payload["carrier_id"], "location": origin,
           "event_time": now, "ingestion": now})

    conn.execute(text("""
        INSERT INTO eta_estimates(eta_id,shipment_id,prediction_time,feature_cutoff_time,
        baseline_eta,predicted_eta,predicted_delay_minutes,risk_level,weather_adjustment_minutes,
        facility_adjustment_minutes,route_adjustment_minutes,carrier_adjustment_minutes,
        rule_version,used_future_data)
        VALUES(:eta,:sid,:prediction,:cutoff,:baseline,:predicted,:delay,:risk,:weather,:facility,:route,:carrier,'rules-v2.1',0)
    """), {"eta": eta_id, "sid": shipment_id, "prediction": prediction_time,
           "cutoff": prediction_time, "baseline": baseline_eta, "predicted": predicted_eta,
           "delay": delay_minutes, "risk": risk, "weather": weather_minutes,
           "facility": facility_minutes, "route": route_minutes, "carrier": carrier_minutes})

    conn.execute(text("""
        INSERT INTO facility_queues(queue_id,facility_id,queue_time,queue_length,
        processing_capacity,average_processing_minutes,estimated_wait_minutes)
        SELECT :qid,:facility,:time,0,capacity_per_hour,0,:wait
        FROM facilities WHERE facility_id=:facility
    """), {"qid": f"QUE-MAN-{int(seq):06d}", "facility": destination,
           "time": now, "wait": facility_minutes})

    if weather != "CLEAR":
        severity = "SEVERE" if weather in ("STORM", "FLOODING") else ("HIGH" if weather == "HEAVY_RAIN" else "MODERATE")
        weather_id = f"WTH-MAN-{int(seq):06d}"
        conn.execute(text("""
            INSERT INTO weather_events(weather_event_id,region,weather_type,severity,start_time,end_time,travel_impact_minutes)
            SELECT :wid,region,:kind,:severity,:start,:end,:impact
            FROM facilities WHERE facility_id=:facility
        """), {"wid": weather_id, "kind": weather, "severity": severity,
               "start": now, "end": now + timedelta(hours=6),
               "impact": weather_minutes, "facility": origin})
        conn.execute(text("""
            INSERT INTO route_weather_impacts(route_id,weather_event_id)
            VALUES(:route,:weather)
        """), {"route": route_id, "weather": weather_id})

    conn.execute(text("""
        INSERT INTO shipment_status_history(history_id,shipment_id,previous_status,new_status,changed_at,source_event_id)
        VALUES(:history,:sid,NULL,'CREATED',:changed,:event)
    """), {"history": f"HST-MAN-{int(seq):06d}-01", "sid": shipment_id,
           "changed": now, "event": event_id})

    return {
        "shipment_id": shipment_id, "eta_id": eta_id, "status": "CREATED",
        "baseline_eta": baseline_eta, "predicted_eta": predicted_eta,
        "predicted_delay_minutes": delay_minutes, "risk_level": risk,
        "adjustments_minutes": {
            "weather": weather_minutes, "facility_queue": facility_minutes,
            "route": route_minutes, "carrier": carrier_minutes
        },
        "rule_version": "rules-v2.1",
        "explanation": "Baseline transit time plus weather, facility, priority/route and carrier adjustments. This is a transparent synthetic/rule-based estimate, not a live traffic forecast."
    }

@app.get("/")
def root():
    return {"application": "ShipSense", "version": "2.0.0", "docs": "/docs"}

@app.get("/api/health")
def health():
    try:
        result = query("SELECT DATABASE() AS db, VERSION() AS version")
        return {"status": "healthy", "database": "connected", **result[0]}
    except Exception as e:
        raise HTTPException(503, detail=f"Database unavailable: {e}")

@app.get("/api/meta/options")
def meta_options():
    try:
        return {
            "facilities": query("SELECT facility_id,facility_name,city,region FROM facilities ORDER BY facility_id"),
            "carriers": query("SELECT carrier_id,carrier_name,reliability_score FROM carriers WHERE active=1 ORDER BY carrier_name"),
            "service_levels": query("SELECT service_level_id,service_name,sla_hours FROM service_levels ORDER BY priority")
        }
    except Exception as e:
        raise HTTPException(500, detail=str(e))

@app.post("/api/shipments")
def create_shipment(payload: ShipmentInput):
    try:
        with engine.begin() as conn:
            result = _create_shipment(conn, payload.model_dump())
        return result
    except ValueError as e:
        raise HTTPException(422, detail=str(e))
    except Exception as e:
        raise HTTPException(500, detail=f"Shipment creation failed: {e}")

@app.post("/api/shipments/import")
async def import_shipments(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(400, detail="Upload a .csv file.")
    raw = await file.read()
    try:
        reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig")))
        required = {"origin_facility_id","destination_facility_id","carrier_id","service_level_id",
                    "promised_delivery_at","total_distance_km"}
        if not reader.fieldnames or not required.issubset(set(reader.fieldnames)):
            raise HTTPException(422, detail=f"CSV must include columns: {', '.join(sorted(required))}")
        created, errors = [], []
        for row_num, row in enumerate(reader, start=2):
            try:
                data = {
                    "origin_facility_id": row["origin_facility_id"].strip(),
                    "destination_facility_id": row["destination_facility_id"].strip(),
                    "carrier_id": row["carrier_id"].strip(),
                    "service_level_id": row["service_level_id"].strip(),
                    "promised_delivery_at": datetime.fromisoformat(row["promised_delivery_at"].strip()),
                    "total_distance_km": float(row["total_distance_km"]),
                    "weather_condition": (row.get("weather_condition") or "CLEAR").strip().upper(),
                    "facility_wait_minutes": int(row.get("facility_wait_minutes") or 0),
                    "priority": (row.get("priority") or "MEDIUM").strip().upper()
                }
                with engine.begin() as conn:
                    created.append(_create_shipment(conn, data))
            except Exception as e:
                errors.append({"row": row_num, "error": str(e)})
        return {"created_count": len(created), "error_count": len(errors),
                "created": created, "errors": errors}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(400, detail=f"Could not parse CSV: {e}")

@app.get("/api/analytics/overview")
def overview():
    try:
        return query("""
            SELECT
              COUNT(*) AS total_shipments,
              SUM(status='DELIVERED') AS delivered_count,
              SUM(status IN ('IN_TRANSIT','OUT_FOR_DELIVERY','PICKED_UP')) AS active_count,
              SUM(status IN ('DELAYED','EXCEPTION')) AS delayed_count,
              (
                SELECT COUNT(*)
                FROM eta_estimates e
                JOIN (
                  SELECT shipment_id, MAX(prediction_time) AS latest_time
                  FROM eta_estimates GROUP BY shipment_id
                ) latest ON latest.shipment_id=e.shipment_id
                       AND latest.latest_time=e.prediction_time
                WHERE e.risk_level IN ('HIGH','MEDIUM')
              ) AS at_risk_count,
              ROUND(
                100*SUM(status='DELIVERED' AND actual_delivery_at IS NOT NULL
                  AND actual_delivery_at<=promised_delivery_at) /
                NULLIF(SUM(status='DELIVERED'),0),2
              ) AS on_time_pct,
              (
                SELECT ROUND(AVG(ABS(TIMESTAMPDIFF(MINUTE,s.actual_delivery_at,e.predicted_eta))),1)
                FROM shipments s
                JOIN eta_estimates e ON e.shipment_id=s.shipment_id
                WHERE s.actual_delivery_at IS NOT NULL
                  AND e.prediction_time=(
                    SELECT MAX(e2.prediction_time) FROM eta_estimates e2
                    WHERE e2.shipment_id=s.shipment_id
                  )
              ) AS eta_mae_minutes
            FROM shipments
        """)[0]
    except Exception as e:
        raise HTTPException(500, detail=f"Overview query failed: {e}")

@app.get("/api/analytics/high-risk")
def high_risk(
    limit: int = Query(100, ge=1, le=1000),
    risk_level: Optional[str] = Query(None, description="Optional LOW, MEDIUM or HIGH filter")
):
    if risk_level is not None:
        risk_level = risk_level.upper()
        if risk_level not in {"LOW", "MEDIUM", "HIGH"}:
            raise HTTPException(422, detail="risk_level must be LOW, MEDIUM or HIGH")

    sql = """
        SELECT s.shipment_id, sl.service_name, s.status, e.predicted_eta,
               e.predicted_delay_minutes, e.risk_level,
               s.promised_delivery_at, e.prediction_time
        FROM eta_estimates e
        JOIN shipments s ON s.shipment_id = e.shipment_id
        JOIN service_levels sl ON sl.service_level_id = s.service_level_id
        WHERE e.eta_id IN (
            SELECT MAX(e2.eta_id)
            FROM eta_estimates e2
            GROUP BY e2.shipment_id
        )
    """
    params = {"lim": limit}
    if risk_level:
        sql += " AND e.risk_level = :risk_level"
        params["risk_level"] = risk_level
    sql += """
        ORDER BY FIELD(e.risk_level, 'HIGH', 'MEDIUM', 'LOW'),
                 e.predicted_delay_minutes DESC, s.shipment_id
        LIMIT :lim
    """
    return query(sql, params)


@app.get("/api/analytics/risk-distribution")
def risk_distribution():
    return query("""
        SELECT e.risk_level, COUNT(*) AS shipment_count
        FROM eta_estimates e
        WHERE e.eta_id IN (
            SELECT MAX(e2.eta_id)
            FROM eta_estimates e2
            GROUP BY e2.shipment_id
        )
        GROUP BY e.risk_level
        ORDER BY FIELD(e.risk_level, 'LOW', 'MEDIUM', 'HIGH')
    """)

@app.get("/api/shipments")
def shipments(limit: int = Query(100, ge=1, le=1000), status: Optional[str] = None, search: Optional[str] = None):
    sql = """SELECT shipment_id,status,carrier_id,service_level_id,origin_facility_id,destination_facility_id,
             created_at,promised_delivery_at,actual_delivery_at,total_distance_km
             FROM shipments WHERE 1=1"""
    params = {"lim": limit}
    if status:
        sql += " AND status=:status"; params["status"] = status
    if search:
        sql += " AND shipment_id LIKE :search"; params["search"] = f"%{search}%"
    return query(sql + " ORDER BY created_at DESC LIMIT :lim", params)

@app.get("/api/shipments/{shipment_id}")
def shipment_detail(shipment_id: str):
    rows = query("SELECT * FROM shipments WHERE shipment_id=:id", {"id": shipment_id})
    if not rows:
        raise HTTPException(404, "Shipment not found")
    return {
        "shipment": rows[0],
        "legs": query("SELECT * FROM shipment_legs WHERE shipment_id=:id ORDER BY sequence_no", {"id": shipment_id}),
        "events": query("SELECT * FROM tracking_events WHERE shipment_id=:id ORDER BY event_time", {"id": shipment_id}),
        "etas": query("SELECT * FROM eta_estimates WHERE shipment_id=:id ORDER BY prediction_time DESC", {"id": shipment_id})
    }

@app.get("/api/shipments/{shipment_id}/events")
def shipment_events(shipment_id: str):
    return query("SELECT * FROM tracking_events WHERE shipment_id=:id ORDER BY event_time", {"id": shipment_id})

@app.get("/api/shipments/{shipment_id}/eta")
def shipment_eta(shipment_id: str):
    return query("SELECT * FROM eta_estimates WHERE shipment_id=:id ORDER BY prediction_time DESC", {"id": shipment_id})

@app.get("/api/delays")
def delays(limit: int = Query(100, ge=1, le=1000)):
    return query("""
        SELECT s.shipment_id,s.status,s.promised_delivery_at,s.actual_delivery_at,
          a.actual_delay_minutes,a.outcome,d.reason_code,d.description
        FROM shipments s LEFT JOIN shipment_delay_assessments a USING(shipment_id)
        LEFT JOIN delay_reasons d USING(delay_reason_id)
        WHERE a.actual_delay_minutes>0
        ORDER BY a.actual_delay_minutes DESC LIMIT :lim
    """, {"lim": limit})

@app.get("/api/anomalies")
def anomalies():
    return query("SELECT * FROM data_quality_issues ORDER BY detected_at DESC LIMIT 1000")

@app.get("/api/facilities")
def facilities():
    return query("""
        SELECT f.facility_id,f.facility_name,f.city,f.region,
          ROUND(AVG(q.estimated_wait_minutes),1) AS avg_wait_minutes,
          MAX(q.queue_length) AS max_queue
        FROM facilities f LEFT JOIN facility_queues q USING(facility_id)
        GROUP BY f.facility_id,f.facility_name,f.city,f.region
        ORDER BY avg_wait_minutes DESC
    """)

@app.get("/api/carriers/performance")
def carrier_performance():
    return query("""
        SELECT c.carrier_id,c.carrier_name,COUNT(s.shipment_id) AS shipments,
          SUM(s.status='DELIVERED') AS delivered,
          ROUND(100*SUM(s.status='DELIVERED' AND s.actual_delivery_at<=s.promised_delivery_at)/
            NULLIF(SUM(s.status='DELIVERED'),0),1) AS on_time_pct,c.reliability_score
        FROM carriers c LEFT JOIN shipments s USING(carrier_id)
        GROUP BY c.carrier_id,c.carrier_name,c.reliability_score ORDER BY shipments DESC
    """)

@app.get("/api/analytics/delay-reasons")
def delay_reasons():
    return query("""
        SELECT d.reason_code,COUNT(*) AS count,SUM(a.actual_delay_minutes) AS delay_minutes
        FROM shipment_delay_assessments a JOIN delay_reasons d USING(delay_reason_id)
        WHERE a.actual_delay_minutes>0 GROUP BY d.reason_code ORDER BY count DESC
    """)

@app.post("/api/synthetic/generate")
def generate_synthetic(size: str = "starter", seed: int = 20261022, replace_existing: bool = False):
    if size not in {"starter", "medium", "full"}:
        raise HTTPException(422, detail="size must be starter, medium or full")
    if not replace_existing:
        raise HTTPException(409, detail="To load a generated dataset, explicitly confirm replace_existing=true. This replaces existing shipment and synthetic records.")
    try:
        tables = ["shipment_status_history","data_quality_issues","shipment_delay_assessments",
                  "eta_estimates","route_weather_impacts","facility_queues","tracking_events",
                  "shipment_legs","shipments","routes","weather_events","delay_reasons",
                  "service_levels","carriers","facilities","generation_runs"]
        with engine.connect() as conn:
            conn.execute(text("SET FOREIGN_KEY_CHECKS=0"))
            for table in tables:
                conn.execute(text(f"TRUNCATE TABLE {table}"))
            conn.execute(text("SET FOREIGN_KEY_CHECKS=1"))
            conn.commit()
        gen = subprocess.run([sys.executable, "-m", "generator.generate", "--size", size, "--seed", str(seed)],
                             cwd=ROOT, capture_output=True, text=True, timeout=900)
        if gen.returncode != 0:
            raise RuntimeError(gen.stderr[-3000:])
        load = subprocess.run([sys.executable, "scripts/load_data.py"], cwd=ROOT,
                              capture_output=True, text=True, timeout=900)
        if load.returncode != 0:
            raise RuntimeError(load.stderr[-3000:])
        manifest_path = ROOT / "data" / "manifests" / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        return {"status": "generated_and_loaded", "manifest": manifest, "loader_output": load.stdout}
    except Exception as e:
        raise HTTPException(500, detail=f"Synthetic generation failed: {e}")
