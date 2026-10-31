# Problem statement gap audit — updated implementation

| Priority | Original gap | Status | Implemented evidence |
|---|---|---|---|
| P1 Critical | Random ETA adjustments | Addressed | `engine/eta_engine.py::derive_source_features` derives weather, facility, route and carrier impacts from source rows at each cutoff; generator calls `predict_eta`. |
| P2 Critical | One ETA per shipment | Addressed | Multiple immutable snapshots at creation, departure/arrival milestones and tracking update ingestion timestamps. |
| P3 High | No duplicate events / route history | Addressed | Deliberate duplicate scan rows and effective-dated route changes with ground-truth and issue labels. |
| P4 High | Missing calendars | Addressed | Carrier calendars and facility disruption windows are generated and included in MySQL DDL. |
| P5 High | Incomplete validation | Addressed | 68 checks covering keys, references, enums, time ordering, cutoff leakage, ETA arithmetic, lifecycle order, duplicate labels and route-change labels. |
| P6 Medium | Incomplete data dictionary | Addressed | Field-by-field dictionary includes type, nullability, allowed values/units, uniqueness and rules. |

Run the starter generator and validator using the commands in `README.md`. The committed starter data and `docs/VALIDATION_REPORT.json` are generated from seed `20261022`.
