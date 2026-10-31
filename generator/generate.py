import argparse, csv, json, random, hashlib
from pathlib import Path
from datetime import datetime, timedelta, timezone
from engine.risk import classify_eta_risk
from engine.eta_engine import derive_source_features, predict_eta

def _parse(value): return datetime.strptime(value, "%Y-%m-%d %H:%M:%S") if value else None

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "generated"
GT = ROOT / "data" / "ground_truth"
MAN = ROOT / "data" / "manifests"
BASE = datetime(2026, 1, 1, 8, 0, 0)

def dt(v): return v.strftime("%Y-%m-%d %H:%M:%S")
def write_csv(name, rows):
    path = OUT / f"{name}.csv"
    if rows:
        with path.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader(); w.writerows(rows)
    return path


def generate(size="starter", seed=20261022):
    rng = random.Random(seed)
    OUT.mkdir(parents=True, exist_ok=True); GT.mkdir(parents=True, exist_ok=True); MAN.mkdir(parents=True, exist_ok=True)
    n = {"starter":1000, "medium":10000, "full":50000}[size]
    carrier_names = ["NorthStar Logistics","BlueRoute Freight","SwiftHaul","Apex Cargo","MetroTrans"]
    carriers = [{"carrier_id":f"CAR-{i+1:03d}","carrier_name":name,"service_type":["ROAD","AIR","RAIL","MULTIMODAL","ROAD"][i],
                "reliability_score":round(rng.uniform(88,99),2),"active":1} for i,name in enumerate(carrier_names)]
    cities = [("Hyderabad","Telangana","SOUTH"),("Bengaluru","Karnataka","SOUTH"),("Chennai","Tamil Nadu","SOUTH"),
              ("Pune","Maharashtra","WEST"),("Mumbai","Maharashtra","WEST"),("Nagpur","Maharashtra","WEST"),
              ("Delhi","Delhi","NORTH"),("Jaipur","Rajasthan","NORTH"),("Kolkata","West Bengal","EAST"),
              ("Bhubaneswar","Odisha","EAST")]
    facilities=[]
    for i in range(100):
        c=cities[i%len(cities)]
        facilities.append({"facility_id":f"FAC-{i+1:03d}","facility_name":f"{c[0]} Distribution Hub {i+1:02d}",
          "city":c[0],"state":c[1],"region":c[2],"capacity_per_hour":rng.randint(20,100),
          "operating_start":"06:00:00","operating_end":"22:00:00"})
    carrier_calendar=[]
    for i,c in enumerate(carriers):
        start=BASE+timedelta(days=20+i*7)
        carrier_calendar.append({"calendar_id":f"CCAL-{i+1:03d}","carrier_id":c["carrier_id"],
          "effective_from":dt(start),"effective_to":dt(start+timedelta(days=35)),
          "adjustment_minutes":[0,8,15,22,5][i],"reason":"Scheduled carrier capacity / service calendar"})
    facility_calendar=[]
    for i,f in enumerate(facilities[:20]):
        start=BASE+timedelta(days=15+i)
        facility_calendar.append({"disruption_id":f"FDIS-{i+1:04d}","facility_id":f["facility_id"],
          "start_time":dt(start),"end_time":dt(start+timedelta(hours=8)),
          "disruption_type":"CAPACITY_REDUCTION","disruption_minutes":15+(i%4)*10,
          "description":"Synthetic planned facility disruption window"})
    levels=[{"service_level_id":"SVC-STANDARD","service_name":"Standard","sla_hours":48,"priority":3},
            {"service_level_id":"SVC-EXPRESS","service_name":"Express","sla_hours":30,"priority":2},
            {"service_level_id":"SVC-PRIORITY","service_name":"Priority","sla_hours":18,"priority":1}]
    routes=[]
    for i in range(100):
        a=i; b=(i+1+rng.randrange(1,9))%100
        routes.append({"route_id":f"RTE-{i+1:04d}","origin_facility_id":facilities[a]["facility_id"],
          "destination_facility_id":facilities[b]["facility_id"],"distance_km":round(rng.uniform(120,1800),2),
          "base_transit_hours":round(rng.uniform(4,42),2)})
    weather=[]
    weather_types=["HEAVY_RAIN","FOG","STORM","HEATWAVE","FLOODING"]
    severities=["LOW","MODERATE","HIGH","SEVERE"]
    for i in range(1000):
        start=BASE+timedelta(hours=rng.randint(0,24*180))
        weather.append({"weather_event_id":f"WTH-{i+1:05d}","region":rng.choice(["NORTH","SOUTH","EAST","WEST"]),
          "weather_type":rng.choice(weather_types),"severity":rng.choice(severities),
          "start_time":dt(start),"end_time":dt(start+timedelta(hours=rng.randint(2,36))),
          "travel_impact_minutes":rng.choice([10,20,35,60,90,150])})
    route_weather=[]
    weather_by_region={r:[] for r in ["NORTH","SOUTH","EAST","WEST"]}
    for w in weather: weather_by_region[w["region"]].append(w)
    for route in routes:
        region=next(f["region"] for f in facilities if f["facility_id"]==route["origin_facility_id"])
        candidates=weather_by_region[region]
        for w in candidates[::max(1,len(candidates)//3)][:3]:
            route_weather.append({"route_id":route["route_id"],"weather_event_id":w["weather_event_id"]})
    shipments=[]; legs=[]; events=[]; queues=[]; etas=[]; assessments=[]; status_hist=[]; issues=[]; gt=[]
    route_history=[]
    event_types=["PICKED_UP","DEPARTED_FACILITY","ARRIVED_FACILITY","IN_TRANSIT","OUT_FOR_DELIVERY","DELIVERED"]
    for i in range(1,n+1):
        sid=f"SHP-2026-{i:06d}"; carrier=rng.choice(carriers); svc=rng.choice(levels)
        origin=rng.randrange(100); dest=(origin+rng.randrange(1,10))%100
        created=BASE+timedelta(hours=rng.randint(0,24*180),minutes=rng.randint(0,59))
        distance=round(rng.uniform(120,1800),2)
        transit=distance/rng.uniform(35,65)
        disruption=rng.choice([0,0,0,20,45,90,150])
        actual=created+timedelta(hours=transit,minutes=disruption+rng.randint(-25,45))
        promised=created+timedelta(hours=svc["sla_hours"])
        delivered=rng.random()<0.82
        actual_delivery=actual if delivered else None
        status="DELIVERED" if delivered else rng.choice(["IN_TRANSIT","DELAYED","OUT_FOR_DELIVERY"])
        # Keep service-level labels derived from actual outcome, not independently randomized.
        shipments.append({"shipment_id":sid,"carrier_id":carrier["carrier_id"],"service_level_id":svc["service_level_id"],
          "origin_facility_id":facilities[origin]["facility_id"],"destination_facility_id":facilities[dest]["facility_id"],
          "created_at":dt(created),"promised_delivery_at":dt(promised),"actual_delivery_at":dt(actual_delivery) if actual_delivery else "",
          "status":status,"total_distance_km":distance,"issue_type":""})
        # 1-3 legs, each with route references; intermediate facility IDs are valid.
        leg_count=rng.randint(1,3); current=origin
        shipment_leg_ids=[]
        for j in range(1,leg_count+1):
            next_fac=dest if j==leg_count else (current+rng.randint(1,9))%100
            route_idx=(current*7+j*13)%100
            route=routes[route_idx]
            # Keep route master endpoint aligned with leg endpoints via a shipment-specific route record.
            rid=f"RTE-SHP-{i:06d}-{j:02d}"
            routes.append({"route_id":rid,"origin_facility_id":facilities[current]["facility_id"],
              "destination_facility_id":facilities[next_fac]["facility_id"],"distance_km":round(distance/leg_count,2),
              "base_transit_hours":round(transit/leg_count,2)})
            lid=f"LEG-{sid}-{j:02d}"; shipment_leg_ids.append(lid)
            dep=created+timedelta(hours=(j-1)*transit/leg_count)
            arr=created+timedelta(hours=j*transit/leg_count)
            legs.append({"leg_id":lid,"shipment_id":sid,"route_id":rid,"carrier_id":carrier["carrier_id"],
              "sequence_no":j,"planned_departure_at":dt(dep),"planned_arrival_at":dt(arr),
              "actual_departure_at":dt(dep+timedelta(minutes=rng.randint(0,40))),
              "actual_arrival_at":dt(arr+timedelta(minutes=disruption/leg_count)) if delivered else "",
              "leg_status":"COMPLETED" if delivered else ("IN_PROGRESS" if j==1 else "PLANNED")})
            current=next_fac
        # 4-8 source events per shipment, with separate event/ingestion timestamps.
        count=rng.randint(4,8); event_ids=[]
        for k in range(count):
            frac=(k+1)/(count+1)
            # The final delivery scan is the source-of-truth timestamp for actual_delivery_at.
            et=actual if delivered and k==count-1 else created+timedelta(seconds=(actual-created).total_seconds()*frac)
            ing=et+timedelta(minutes=rng.choice([1,3,5,10,25,60]))
            typ="DELIVERED" if delivered and k==count-1 else event_types[min(4,int(frac*6))]
            eid=f"EVT-{sid}-{k+1:06d}"; event_ids.append(eid)
            events.append({"event_id":eid,"shipment_id":sid,"leg_id":shipment_leg_ids[min(len(shipment_leg_ids)-1,int(frac*len(shipment_leg_ids)))],
              "carrier_id":carrier["carrier_id"],"event_type":typ,"event_location":facilities[(origin+k+1)%100]["city"],
              "event_time":dt(et),"ingestion_time":dt(ing),"source_system":"SYNTHETIC_CARRIER",
              "is_duplicate":0,"issue_type":""})
        # Deliberate duplicate delivery/scan rows with explicit labels and stable source identity.
        if i % 100 == 0 and events:
            original=events[-1]
            duplicate=dict(original)
            duplicate["event_id"]=f"EVT-DUP-{sid}"
            duplicate["is_duplicate"]=1
            duplicate["issue_type"]="DUPLICATE_EVENT"
            events.append(duplicate)
            gt.append({"ground_truth_id":f"GT-{len(gt)+1:06d}","shipment_id":sid,
              "issue_type":"DUPLICATE_EVENT","expected_label":"ANOMALY","record_id":duplicate["event_id"]})
            issues.append({"issue_id":f"ISS-{len(issues)+1:06d}","shipment_id":sid,
              "record_id":duplicate["event_id"],"issue_type":"DUPLICATE_EVENT","severity":"MEDIUM",
              "detected_at":dt(_parse(original["ingestion_time"])),"description":"Intentional duplicate carrier event"})
        # Route revisions are append-only and become eligible only from effective_at.
        if i % 50 == 0:
            change_time=created+timedelta(hours=max(1,transit*0.30))
            route_history.append({"route_change_id":f"RCH-{sid}-01","shipment_id":sid,
              "old_route_id":next(x["route_id"] for x in legs if x["leg_id"]==shipment_leg_ids[0]),"new_route_id":next(x["route_id"] for x in legs if x["leg_id"]==shipment_leg_ids[-1]),
              "effective_at":dt(change_time),"transit_adjustment_minutes":15+(i%5)*5,
              "change_reason":"WEATHER_REROUTE","ground_truth_label":"ROUTE_CHANGED"})
            gt.append({"ground_truth_id":f"GT-{len(gt)+1:06d}","shipment_id":sid,
              "issue_type":"ROUTE_CHANGE","expected_label":"ROUTE_CHANGED","record_id":route_history[-1]["route_change_id"]})
        # Facility queue snapshots are source inputs.
        for q in range(2):
            qtime=created+timedelta(hours=q*max(1,transit/2))
            qlen=rng.randint(2,180); cap=rng.randint(20,100); wait=round(qlen/max(1,cap)*60,2)
            queues.append({"queue_id":f"QUE-{i:06d}-{q+1:02d}","facility_id":facilities[(origin+q+1)%100]["facility_id"],
              "queue_time":dt(qtime),"queue_length":qlen,"processing_capacity":cap,
              "average_processing_minutes":round(rng.uniform(3,18),2),"estimated_wait_minutes":wait})
        # Point-in-time ETA snapshots: creation, departure, intermediate arrivals,
        # and every subsequent carrier update. Feature cutoffs are immutable.
        snapshot_times={created}
        for ev in events:
            if ev["shipment_id"] == sid:
                ing=_parse(ev["ingestion_time"])
                if ing and ing >= created: snapshot_times.add(ing)
        for leg in [x for x in legs if x["shipment_id"] == sid]:
            for key in ("actual_departure_at","actual_arrival_at"):
                value=_parse(leg.get(key,""))
                if value and value >= created: snapshot_times.add(value)
        carrier_for_shipment=carrier
        for prediction in sorted(snapshot_times):
            shipment_legs_now=[x for x in legs if x["shipment_id"]==sid]
            shipment_events_now=[x for x in events if x["shipment_id"]==sid]
            shipment_queues_now=[x for x in queues if x["queue_id"].startswith(f"QUE-{i:06d}-")]
            shipment_route_history=[x for x in route_history if x["shipment_id"]==sid]
            remaining_h, weather_adj, facility_adj, route_adj, carrier_adj, eligible = derive_source_features(
                prediction, shipments[-1], carrier_for_shipment, shipment_legs_now, shipment_events_now,
                shipment_queues_now, weather, shipment_route_history, carrier_calendar,
                facility_calendar, routes, facilities)
            prediction_result=predict_eta(prediction, int(remaining_h*60), weather_adj,
                facility_adj, route_adj, carrier_adj, promised)
            baseline=prediction_result["baseline_eta"]
            predicted=prediction_result["predicted_eta"]
            predicted_delay=prediction_result["predicted_delay_minutes"]
            etaid=f"ETA-{sid}-{prediction.strftime('%Y%m%dT%H%M%S')}"
            etas.append({"eta_id":etaid,"shipment_id":sid,"prediction_time":dt(prediction),
              "feature_cutoff_time":dt(prediction),"baseline_eta":dt(baseline),"predicted_eta":dt(predicted),
              "predicted_delay_minutes":predicted_delay,"risk_level":prediction_result["risk_level"],
              "weather_adjustment_minutes":weather_adj,"facility_adjustment_minutes":facility_adj,
              "route_adjustment_minutes":route_adj,"carrier_adjustment_minutes":carrier_adj,
              "eligible_event_count":len(eligible),"rule_version":"rules-v3.0","used_future_data":0})
        delay=max(0,int((actual-promised).total_seconds()/60)) if delivered else 0
        reason="WEATHER" if disruption>=60 else ("FACILITY_QUEUE" if disruption>=25 else "CARRIER_VARIANCE")
        assessments.append({"assessment_id":f"DLY-2026-{i:06d}","shipment_id":sid,"delay_reason_id":{"WEATHER":"DR-WEATHER","FACILITY_QUEUE":"DR-QUEUE","CARRIER_VARIANCE":"DR-CARRIER"}[reason],
          "actual_delay_minutes":delay,"outcome":"DELAYED" if delay>0 else ("ON_TIME" if delivered else "PENDING"),
          "assessed_at":dt(actual if delivered else prediction)})
        status_hist.append({"history_id":f"HST-{i:06d}-01","shipment_id":sid,"previous_status":"","new_status":"CREATED",
          "changed_at":dt(created),"source_event_id":""})
        # Deliberately inject four anomaly families into a small labelled sample.
        if i % 250 == 0:
            typ=["INGESTION_EVENT_TIME_CONFUSION","IMPOSSIBLE_ROUTE_ORDER","FUTURE_EVENT_LEAKAGE","DELIVERED_MARKED_IN_TRANSIT"][(i//250-1)%4]
            gt.append({"ground_truth_id":f"GT-{len(gt)+1:06d}","shipment_id":sid,"issue_type":typ,"expected_label":"ANOMALY",
                       "record_id":event_ids[-1] if typ in ("INGESTION_EVENT_TIME_CONFUSION","FUTURE_EVENT_LEAKAGE") else shipment_leg_ids[-1]})
            issues.append({"issue_id":f"ISS-{len(issues)+1:06d}","shipment_id":sid,"record_id":gt[-1]["record_id"],
              "issue_type":typ,"severity":"HIGH","detected_at":dt(prediction),
              "description":"Synthetic labelled exception for validation and reviewer walkthrough."})
            if typ=="INGESTION_EVENT_TIME_CONFUSION":
                events[-1]["issue_type"]=typ
                events[-1]["ingestion_time"]=dt(et-timedelta(minutes=10))
            elif typ=="FUTURE_EVENT_LEAKAGE":
                etas[-1]["used_future_data"]=1
                etas[-1]["feature_cutoff_time"]=dt(prediction+timedelta(minutes=30))
            elif typ=="DELIVERED_MARKED_IN_TRANSIT":
                shipments[-1]["status"]="IN_TRANSIT"
                shipments[-1]["issue_type"]=typ
            elif typ=="IMPOSSIBLE_ROUTE_ORDER":
                legs[-1]["sequence_no"]=0
                legs[-1]["leg_status"]="INVALID_ORDER"
        if delivered:
            status_hist.append({"history_id":f"HST-{i:06d}-02","shipment_id":sid,"previous_status":"IN_TRANSIT",
              "new_status":"DELIVERED","changed_at":dt(actual),"source_event_id":event_ids[-1]})
    reasons=[{"delay_reason_id":"DR-WEATHER","reason_code":"WEATHER","description":"Weather disruption affecting route transit"},
             {"delay_reason_id":"DR-QUEUE","reason_code":"FACILITY_QUEUE","description":"Facility queue congestion and processing wait"},
             {"delay_reason_id":"DR-CARRIER","reason_code":"CARRIER_VARIANCE","description":"Carrier transit-time variance"}]
    datasets={"carriers":carriers,"facilities":facilities,"service_levels":levels,"routes":routes,"shipments":shipments,
      "shipment_legs":legs,"tracking_events":events,"facility_queues":queues,"weather_events":weather,
      "eta_estimates":etas,"delay_reasons":reasons,"route_weather_impacts":route_weather,"shipment_delay_assessments":assessments,
       "shipment_status_history":status_hist,"data_quality_issues":issues,
      "carrier_calendars":carrier_calendar,"facility_disruptions":facility_calendar,
      "route_change_history":route_history}
    manifest={"seed":seed,"size":size,"shipments":len(shipments),"tracking_events":len(events),"facilities":len(facilities),
      "weather_events":len(weather),"eta_snapshots":len(etas),"generated_utc":datetime.now(timezone.utc).isoformat(),"files":{}}
    for name,rows in datasets.items():
        p=write_csv(name,rows)
        manifest["files"][p.name]={"rows":len(rows),"sha256":hashlib.sha256(p.read_bytes()).hexdigest()}
    with (GT/"ground_truth.json").open("w",encoding="utf-8") as f: json.dump(gt,f,indent=2)
    with (GT/"ground_truth.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(gt[0].keys()) if gt else ["ground_truth_id","shipment_id","issue_type","expected_label","record_id"])
        w.writeheader(); w.writerows(gt)
    (MAN/"manifest.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")
    print(json.dumps(manifest,indent=2))
    return manifest

if __name__=="__main__":
    p=argparse.ArgumentParser(); p.add_argument("--size",choices=["starter","medium","full"],default="starter"); p.add_argument("--seed",type=int,default=20261022)
    a=p.parse_args(); generate(a.size,a.seed)
