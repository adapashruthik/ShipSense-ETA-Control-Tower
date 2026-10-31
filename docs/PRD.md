# ShipSense PRD

## Goal
Combine carrier events, route plans, weather and facility queues to estimate delivery ETA, identify likely delays and preserve explainable operational decisions.

## Actors
Supplier, planner, carrier/warehouse operator, logistics analyst and operations manager.

## Functional scope
1. Create master data before dependent records.
2. Support multi-leg shipments, carriers, routes and facility calendars.
3. Capture event_time and ingestion_time separately.
4. Generate weather/facility disruption windows and queue snapshots.
5. Derive actual delivery and delay labels from source events and service-level commitments.
6. Create immutable ETA snapshots at prediction times.
7. Detect timestamp confusion, impossible route order, future-event leakage and delivered/in-transit contradictions.
8. Export CSV/JSON, validation reports and separate ground truth.
9. Expose operational APIs and dashboard KPIs.

## Business rules
- Actual delivery time comes from the delivery event.
- Actual delay minutes = max(0, actual delivery - promised delivery).
- Prediction features must be available at prediction time: event_time <= prediction_time AND ingestion_time <= prediction_time.
- Historical ETA snapshots are append-only.
- Ground truth is for evaluation only and must not leak into features.
- Duplicate source events are retained and flagged, not silently removed.

## Acceptance
- Referential integrity and deterministic IDs.
- Configurable starter/medium/full generation.
- Four required anomaly families represented.
- ETA and delay functions tested.
- API and dashboard execute locally.
- Repeated same-seed generation yields matching CSV checksums.


## Interactive ingestion and control-tower UX (v2 scope)

The Streamlit control tower provides three ingestion paths:
- Manual shipment creation with validated facility, carrier and service-level parent IDs.
- CSV bulk shipment ingestion with row-level validation and a downloadable template.
- Deterministic synthetic dataset generation at starter, medium and full scale with fixed-seed reproducibility. Loading a new synthetic dataset requires explicit confirmation because it replaces existing database records.

A successful manual/CSV record creates a shipment, one initial route leg, a `CREATED` tracking event with separate event and ingestion timestamps, a status-history record, optional weather and facility queue records, and an immutable ETA snapshot. The ETA snapshot records its feature cutoff, rule version, baseline ETA, predicted ETA, delay minutes, risk level and individual adjustments.

The online estimator is an explainable rule-based baseline. It does not claim live carrier feeds, live weather services or a trained ML model. ETA MAE is calculated only for delivered shipments with a stored ETA snapshot by comparing predicted ETA with actual delivery time.
