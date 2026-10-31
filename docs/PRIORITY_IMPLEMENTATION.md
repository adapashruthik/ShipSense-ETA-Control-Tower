# Priority implementation notes

## Priority 1 — source-integrated ETA
`generator/generate.py` calls the point-in-time feature derivation for every snapshot. It reads tracking events, route plans, weather windows, queue snapshots, disruption windows, carrier reliability, and carrier calendars. No adjustment is randomly selected inside the ETA calculation. The ETA engine's `eligible_events` helper enforces both event-time and ingestion-time cutoff.

## Priority 2 — multiple snapshots
Snapshots are emitted at shipment creation and at actual departure/arrival milestones and tracking event ingestion times. Each has `prediction_time` and `feature_cutoff_time`; the latter never exceeds the prediction time in clean rows. ETA IDs include the timestamp.

## Priority 3 — duplicates and route changes
Every 100th shipment receives an intentional duplicate scan (`is_duplicate=1`, `issue_type=DUPLICATE_EVENT`). Every 50th shipment receives an effective-dated route revision with a ground-truth label. Both are recorded in `ground_truth` and `data_quality_issues`.

## Priority 4 — calendars
`carrier_calendars` models effective-dated carrier capacity/service adjustments. `facility_disruptions` models facility closure, maintenance, capacity, or weather windows. Both are included in CSV generation and MySQL DDL.

## Priority 5 — validation
The validator checks table primary keys, foreign keys, enums, temporal ordering, point-in-time cutoffs, ETA arithmetic, snapshot uniqueness and creation anchors, duplicate labeling, lifecycle target states, route-change labels, and required calendar/disruption populations. Deliberate anomaly samples are expected only when labelled.

## Priority 6 — field dictionary
`docs/DATA_DICTIONARY.md` documents every persisted field, including SQL type, nullability, allowed values/units, uniqueness, and validation semantics.

## Reproducibility
Use a fixed `--seed`. `data/manifests/manifest.json` stores generated row counts and SHA-256 checksums. Re-run the validator after each generation.
