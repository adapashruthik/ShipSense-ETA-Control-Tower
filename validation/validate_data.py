import csv, json
from pathlib import Path
from datetime import datetime
ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"data"/"generated"
GT=ROOT/"data"/"ground_truth"

def read(name):
    p=DATA/f"{name}.csv"
    return list(csv.DictReader(p.open(encoding="utf-8"))) if p.exists() else []

def dt(v):
    return datetime.strptime(v,"%Y-%m-%d %H:%M:%S") if v else None

def validate():
    checks=[]
    def add(name,ok,detail): checks.append({"check":name,"passed":bool(ok),"detail":str(detail)})
    tables={p.stem:read(p.stem) for p in DATA.glob("*.csv")}
    pk={"carriers":"carrier_id","facilities":"facility_id","service_levels":"service_level_id",
        "routes":"route_id","shipments":"shipment_id","shipment_legs":"leg_id",
        "tracking_events":"event_id","facility_queues":"queue_id","weather_events":"weather_event_id",
        "eta_estimates":"eta_id","delay_reasons":"delay_reason_id",
        "shipment_delay_assessments":"assessment_id","shipment_status_history":"history_id",
        "data_quality_issues":"issue_id","carrier_calendars":"calendar_id",
        "facility_disruptions":"disruption_id","route_change_history":"route_change_id"}
    for table,key in pk.items():
        rows=tables.get(table,[]); values=[r.get(key,"") for r in rows]
        add(f"{table}: primary key exists and unique",len(values)==len(set(values)) and all(values),
            f"{len(rows)} rows; {len(set(values))} unique keys")
    sets={t:{r.get(k,"") for r in tables.get(t,[])} for t,k in pk.items()}
    fks={
      "routes.origin_facility_id":("routes","origin_facility_id","facilities"),
      "routes.destination_facility_id":("routes","destination_facility_id","facilities"),
      "shipments.carrier_id":("shipments","carrier_id","carriers"),
      "shipments.service_level_id":("shipments","service_level_id","service_levels"),
      "shipments.origin_facility_id":("shipments","origin_facility_id","facilities"),
      "shipments.destination_facility_id":("shipments","destination_facility_id","facilities"),
      "shipment_legs.shipment_id":("shipment_legs","shipment_id","shipments"),
      "shipment_legs.route_id":("shipment_legs","route_id","routes"),
      "shipment_legs.carrier_id":("shipment_legs","carrier_id","carriers"),
      "tracking_events.shipment_id":("tracking_events","shipment_id","shipments"),
      "tracking_events.leg_id":("tracking_events","leg_id","shipment_legs"),
      "tracking_events.carrier_id":("tracking_events","carrier_id","carriers"),
      "facility_queues.facility_id":("facility_queues","facility_id","facilities"),
      "route_weather_impacts.route_id":("route_weather_impacts","route_id","routes"),
      "route_weather_impacts.weather_event_id":("route_weather_impacts","weather_event_id","weather_events"),
      "eta_estimates.shipment_id":("eta_estimates","shipment_id","shipments"),
      "shipment_delay_assessments.shipment_id":("shipment_delay_assessments","shipment_id","shipments"),
      "shipment_delay_assessments.delay_reason_id":("shipment_delay_assessments","delay_reason_id","delay_reasons"),
      "shipment_status_history.shipment_id":("shipment_status_history","shipment_id","shipments"),
      "shipment_status_history.source_event_id":("shipment_status_history","source_event_id","tracking_events"),
      "data_quality_issues.shipment_id":("data_quality_issues","shipment_id","shipments"),
      "carrier_calendars.carrier_id":("carrier_calendars","carrier_id","carriers"),
      "facility_disruptions.facility_id":("facility_disruptions","facility_id","facilities"),
      "route_change_history.shipment_id":("route_change_history","shipment_id","shipments"),
      "route_change_history.old_route_id":("route_change_history","old_route_id","routes"),
      "route_change_history.new_route_id":("route_change_history","new_route_id","routes")}
    for label,(t,col,parent) in fks.items():
        bad=[r for r in tables.get(t,[]) if r.get(col) and r[col] not in sets.get(parent,set())]
        add(f"{label}: foreign key",not bad,f"{len(bad)} invalid references")
    enums={"carriers.service_type":{"ROAD","AIR","RAIL","SEA","MULTIMODAL"},
      "shipments.status":{"CREATED","PICKED_UP","IN_TRANSIT","OUT_FOR_DELIVERY","DELIVERED","DELAYED","EXCEPTION","CANCELLED"},
      "weather_events.severity":{"LOW","MODERATE","HIGH","SEVERE"},
      "eta_estimates.risk_level":{"LOW","MEDIUM","HIGH"},
      "facility_disruptions.disruption_type":{"CAPACITY_REDUCTION","CLOSURE","MAINTENANCE","WEATHER"},
      "route_change_history.change_reason":{"WEATHER_REROUTE","FACILITY_CLOSURE","CARRIER_CHANGE","PLANNING_UPDATE"},
      "tracking_events.event_type":{"PICKED_UP","DEPARTED_FACILITY","ARRIVED_FACILITY","IN_TRANSIT","OUT_FOR_DELIVERY","DELIVERED"},
      "data_quality_issues.severity":{"LOW","MEDIUM","HIGH","CRITICAL"},
      "shipment_delay_assessments.outcome":{"DELAYED","ON_TIME","PENDING"}}
    for label,allowed in enums.items():
        t,c=label.split("."); bad=[r for r in tables.get(t,[]) if r.get(c) not in allowed]
        add(f"{label}: allowed enum",not bad,f"{len(bad)} invalid values")
    # Temporal ordering and nonnegative / derived fields.
    date_rules=[("shipment_legs","planned_departure_at","planned_arrival_at"),
      ("weather_events","start_time","end_time"),("carrier_calendars","effective_from","effective_to"),
      ("facility_disruptions","start_time","end_time")]
    for t,a,b in date_rules:
        bad=[r for r in tables.get(t,[]) if dt(r[a]) >= dt(r[b])]
        add(f"{t}: date ordering",not bad,f"{len(bad)} invalid ranges")
    bad=[e for e in tables.get("tracking_events",[]) if dt(e["ingestion_time"]) < dt(e["event_time"])
         and e.get("issue_type")!="INGESTION_EVENT_TIME_CONFUSION"]
    add("tracking events: ingestion cannot precede event unless labelled",not bad,f"{len(bad)} unlabelled")
    eta=tables.get("eta_estimates",[])
    bad_cutoff=[e for e in eta if dt(e["feature_cutoff_time"])>dt(e["prediction_time"])
                and not any(g.get("shipment_id")==e["shipment_id"] and g.get("issue_type")=="FUTURE_EVENT_LEAKAGE"
                            for g in json.loads((GT/"ground_truth.json").read_text()))]
    add("ETA: point-in-time cutoff",not bad_cutoff,f"{len(bad_cutoff)} unlabelled future cutoffs")
    bad_math=[]
    for e in eta:
        if int(e["predicted_delay_minutes"])<0 or dt(e["predicted_eta"]) < dt(e["baseline_eta"]):
            bad_math.append(e["eta_id"])
        expected=max(0,int((dt(e["predicted_eta"])-dt(next(s["promised_delivery_at"] for s in tables["shipments"] if s["shipment_id"]==e["shipment_id"]))).total_seconds()/60))
        if expected != int(e["predicted_delay_minutes"]): bad_math.append(e["eta_id"])
    add("ETA: derived delay and timestamp arithmetic",not bad_math,f"{len(set(bad_math))} invalid snapshots")
    # Snapshot uniqueness and required lifecycle anchor snapshots.
    key=[(e["shipment_id"],e["prediction_time"]) for e in eta]
    add("ETA: unique shipment/cutoff snapshot",len(key)==len(set(key)),f"{len(eta)} snapshots")
    creation={s["shipment_id"]:s["created_at"] for s in tables.get("shipments",[])}
    missing=[sid for sid,t in creation.items() if not any(x["shipment_id"]==sid and x["prediction_time"]==t for x in eta)]
    add("ETA: snapshot at shipment creation",not missing,f"{len(missing)} shipments missing")
    # Duplicate events must be explicitly flagged and labelled; no silent duplicates.
    events=tables.get("tracking_events",[])
    signatures={}
    for e in events:
        sig=(e["shipment_id"],e["event_type"],e["event_location"],e["event_time"],e["source_system"])
        signatures.setdefault(sig,[]).append(e)
    duplicate_groups=[g for g in signatures.values() if len(g)>1]
    unlabelled=[]
    for group in duplicate_groups:
        canonical=[e for e in group if not int(e.get("is_duplicate",0)) and e.get("issue_type")!="DUPLICATE_EVENT"]
        extras=[e for e in group if int(e.get("is_duplicate",0)) and e.get("issue_type")=="DUPLICATE_EVENT"]
        if len(canonical)!=1 or len(extras)!=len(group)-1:
            unlabelled.extend(group)
    add("tracking events: duplicate rows explicitly flagged",not unlabelled,
        f"{len(duplicate_groups)} duplicate groups; {len(unlabelled)} unlabelled rows")
    # Lifecycle transitions must follow allowed graph; intentional injected mismatch is ground-truthed.
    allowed={"":"CREATED","CREATED":"PICKED_UP","PICKED_UP":"IN_TRANSIT","IN_TRANSIT":"OUT_FOR_DELIVERY",
             "OUT_FOR_DELIVERY":"DELIVERED","IN_TRANSIT":"DELIVERED","CREATED":"CANCELLED"}
    gt=json.loads((GT/"ground_truth.json").read_text(encoding="utf-8")) if (GT/"ground_truth.json").exists() else []
    gt_records={(x.get("record_id"),x.get("issue_type")) for x in gt}
    invalid=[]
    transition_graph={
      "": {"CREATED"}, "CREATED":{"PICKED_UP","CANCELLED","EXCEPTION"},
      "PICKED_UP":{"IN_TRANSIT","DELAYED","EXCEPTION"},
      "IN_TRANSIT":{"OUT_FOR_DELIVERY","DELIVERED","DELAYED","EXCEPTION"},
      "OUT_FOR_DELIVERY":{"DELIVERED","DELAYED","EXCEPTION"},
      "DELAYED":{"IN_TRANSIT","OUT_FOR_DELIVERY","DELIVERED","EXCEPTION","CANCELLED"},
      "EXCEPTION":{"IN_TRANSIT","CANCELLED"}, "DELIVERED":set(), "CANCELLED":set()}
    histories=sorted(tables.get("shipment_status_history",[]),
                     key=lambda h:(h["shipment_id"],dt(h["changed_at"])))
    last_time={}
    for h in histories:
        prev=h.get("previous_status") or ""
        if h["new_status"] not in transition_graph.get(prev,set()):
            invalid.append(h["history_id"])
        key=h["shipment_id"]; now=dt(h["changed_at"])
        if key in last_time and now < last_time[key]: invalid.append(h["history_id"])
        last_time[key]=now
    add("shipment lifecycle history: allowed transitions and chronological order",not invalid,
        f"{len(invalid)} invalid transitions/orderings")
    # Calendar and route-change windows must be effective-dated.
    route_bad=[r for r in tables.get("route_change_history",[]) if not r.get("ground_truth_label") or dt(r["effective_at"]) is None]
    add("route changes: effective timestamp and ground-truth label",not route_bad,f"{len(route_bad)} invalid rows")
    # Dataset anomaly examples are allowed only when a ground-truth row exists.
    issue_rows=tables.get("data_quality_issues",[])
    unlabelled_issues=[r for r in issue_rows if not any(g.get("record_id")==r["record_id"] and g.get("issue_type")==r["issue_type"] for g in gt)]
    add("data quality issues: labelled ground truth",not unlabelled_issues,f"{len(unlabelled_issues)} unlabelled issues")
    add("carrier calendars populated",len(tables.get("carrier_calendars",[]))>0,f"{len(tables.get('carrier_calendars',[]))} rows")
    add("facility disruption windows populated",len(tables.get("facility_disruptions",[]))>0,f"{len(tables.get('facility_disruptions',[]))} rows")
    add("multiple ETA snapshots generated",len(eta)>len(tables.get("shipments",[])),f"{len(eta)} snapshots for {len(tables.get('shipments',[]))} shipments")
    result={"passed":all(c["passed"] for c in checks),"checks":checks,"summary":{"check_count":len(checks),"passed":sum(c["passed"] for c in checks),"failed":sum(not c["passed"] for c in checks)}}
    (ROOT/"docs"/"VALIDATION_REPORT.json").write_text(json.dumps(result,indent=2),encoding="utf-8")
    print(json.dumps(result,indent=2)); return result

if __name__=="__main__": validate()
