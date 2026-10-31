# ShipSense data dictionary — field-level reference

All timestamps are UTC in `YYYY-MM-DD HH:MM:SS` format (MySQL `DATETIME`). IDs are immutable strings. CSV blank values map to SQL `NULL` where nullable. Numeric minute fields are minutes; distance is kilometres; transit is hours; queue length/capacity are shipment/processing units per hour.

| Entity | Field | Type | Nullable | Allowed values / units | Unique | Validation / meaning |
|---|---|---|---|---|---|---|
| carriers | carrier_id | VARCHAR(30) | No | ID | Yes (PK) | Stable carrier key |
| carriers | carrier_name | VARCHAR(120) | No | Text | No | Display name |
| carriers | service_type | ENUM | No | ROAD, AIR, RAIL, SEA, MULTIMODAL | No | Supported transport mode |
| carriers | reliability_score | DECIMAL(5,2) | No | 0–100 percent | No | Carrier reliability percentage |
| carriers | active | BOOLEAN | No | 0/1 | No | Whether carrier is active |
| facilities | facility_id | VARCHAR(30) | No | ID | Yes (PK) | Stable facility key |
| facilities | facility_name | VARCHAR(120) | No | Text | No | Facility display name |
| facilities | city | VARCHAR(80) | No | Text | No | City |
| facilities | state | VARCHAR(80) | No | Text | No | State/region |
| facilities | region | VARCHAR(40) | No | NORTH, SOUTH, EAST, WEST | No | Weather matching region |
| facilities | capacity_per_hour | INT | No | >0 units/hour | No | Nominal processing capacity |
| facilities | operating_start | TIME | No | UTC local operating time | No | Daily opening time |
| facilities | operating_end | TIME | No | Later than start | No | Daily closing time |
| service_levels | service_level_id | VARCHAR(30) | No | ID | Yes (PK) | SLA key |
| service_levels | service_name | VARCHAR(80) | No | Text | No | Standard, Express, Priority |
| service_levels | sla_hours | INT | No | Positive hours | No | Promised delivery window |
| service_levels | priority | INT | No | Positive integer | No | Lower number is higher priority |
| routes | route_id | VARCHAR(30) | No | ID | Yes (PK) | Route master key |
| routes | origin_facility_id | VARCHAR(30) | No | facilities.facility_id | No | FK to origin facility |
| routes | destination_facility_id | VARCHAR(30) | No | facilities.facility_id | No | FK to destination facility |
| routes | distance_km | DECIMAL(10,2) | No | km, >0 | No | Planned route distance |
| routes | base_transit_hours | DECIMAL(8,2) | No | hours, >0 | No | Planned transit duration |
| shipments | shipment_id | VARCHAR(30) | No | ID | Yes (PK) | Shipment business key |
| shipments | carrier_id | VARCHAR(30) | No | carriers.carrier_id | No | Assigned carrier FK |
| shipments | service_level_id | VARCHAR(30) | No | service_levels.service_level_id | No | SLA FK |
| shipments | origin_facility_id | VARCHAR(30) | No | facilities.facility_id | No | Origin FK |
| shipments | destination_facility_id | VARCHAR(30) | No | facilities.facility_id | No | Destination FK |
| shipments | created_at | DATETIME | No | UTC | No | Shipment creation timestamp |
| shipments | promised_delivery_at | DATETIME | No | Later than created_at | No | SLA deadline |
| shipments | actual_delivery_at | DATETIME | Yes | UTC, >= created_at | No | Actual delivery time, if delivered |
| shipments | status | ENUM | No | CREATED, PICKED_UP, IN_TRANSIT, OUT_FOR_DELIVERY, DELIVERED, DELAYED, EXCEPTION, CANCELLED | No | Current lifecycle state |
| shipments | total_distance_km | DECIMAL(10,2) | No | km, >0 | No | Planned shipment distance |
| shipments | issue_type | VARCHAR(60) | Yes | Label or blank | No | Ground-truth anomaly label |
| shipment_legs | leg_id | VARCHAR(60) | No | ID | Yes (PK) | Leg key |
| shipment_legs | shipment_id | VARCHAR(30) | No | shipments.shipment_id | No | Shipment FK |
| shipment_legs | route_id | VARCHAR(30) | No | routes.route_id | No | Planned route FK |
| shipment_legs | carrier_id | VARCHAR(30) | No | carriers.carrier_id | No | Leg carrier FK |
| shipment_legs | sequence_no | INT | No | 1..N | Unique per shipment | Ordered leg sequence |
| shipment_legs | planned_departure_at | DATETIME | No | UTC | No | Planned departure |
| shipment_legs | planned_arrival_at | DATETIME | No | After planned departure | No | Planned arrival |
| shipment_legs | actual_departure_at | DATETIME | Yes | UTC | No | Actual departure |
| shipment_legs | actual_arrival_at | DATETIME | Yes | UTC | No | Actual arrival |
| shipment_legs | leg_status | VARCHAR(30) | No | PLANNED, IN_PROGRESS, COMPLETED, INVALID_ORDER | No | Leg lifecycle label |
| tracking_events | event_id | VARCHAR(60) | No | ID | Yes (PK) | Unique row ID, including duplicates |
| tracking_events | shipment_id | VARCHAR(30) | No | shipments.shipment_id | No | Shipment FK |
| tracking_events | leg_id | VARCHAR(60) | Yes | shipment_legs.leg_id | No | Related leg FK |
| tracking_events | carrier_id | VARCHAR(30) | No | carriers.carrier_id | No | Reporting carrier FK |
| tracking_events | event_type | VARCHAR(40) | No | PICKED_UP, DEPARTED_FACILITY, ARRIVED_FACILITY, IN_TRANSIT, OUT_FOR_DELIVERY, DELIVERED | No | Carrier scan type |
| tracking_events | event_location | VARCHAR(120) | No | Text | No | Scan location |
| tracking_events | event_time | DATETIME | No | UTC | No | When event occurred |
| tracking_events | ingestion_time | DATETIME | No | UTC | No | When event became available to platform |
| tracking_events | source_system | VARCHAR(50) | No | Text | No | Originating event system |
| tracking_events | is_duplicate | BOOLEAN | No | 0/1 | No | Duplicate rows are retained but excluded from ETA features |
| tracking_events | issue_type | VARCHAR(60) | Yes | DUPLICATE_EVENT or anomaly label | No | Explicit quality label |
| facility_queues | queue_id | VARCHAR(60) | No | ID | Yes (PK) | Queue snapshot key |
| facility_queues | facility_id | VARCHAR(30) | No | facilities.facility_id | No | Facility FK |
| facility_queues | queue_time | DATETIME | No | UTC | No | Snapshot timestamp |
| facility_queues | queue_length | INT | No | >=0 shipments | No | Queue size |
| facility_queues | processing_capacity | INT | No | >0 units/hour | No | Queue throughput capacity |
| facility_queues | average_processing_minutes | DECIMAL(8,2) | No | minutes | No | Average processing time |
| facility_queues | estimated_wait_minutes | DECIMAL(8,2) | No | >=0 minutes | No | Queue-derived wait estimate |
| weather_events | weather_event_id | VARCHAR(40) | No | ID | Yes (PK) | Weather record key |
| weather_events | region | VARCHAR(40) | No | NORTH, SOUTH, EAST, WEST | No | Geographic region |
| weather_events | weather_type | VARCHAR(40) | No | HEAVY_RAIN, FOG, STORM, HEATWAVE, FLOODING | No | Weather category |
| weather_events | severity | ENUM | No | LOW, MODERATE, HIGH, SEVERE | No | Severity |
| weather_events | start_time | DATETIME | No | UTC | No | Impact window start |
| weather_events | end_time | DATETIME | No | After start_time | No | Impact window end |
| weather_events | travel_impact_minutes | INT | No | >=0 minutes | No | Travel impact applied only while active |
| route_weather_impacts | route_id | VARCHAR(30) | No | routes.route_id | Composite PK | Route-weather mapping FK |
| route_weather_impacts | weather_event_id | VARCHAR(40) | No | weather_events.weather_event_id | Composite PK | Weather FK |
| eta_estimates | eta_id | VARCHAR(100) | No | ID | Yes (PK) | Immutable snapshot ID |
| eta_estimates | shipment_id | VARCHAR(30) | No | shipments.shipment_id | No | Shipment FK |
| eta_estimates | prediction_time | DATETIME | No | UTC | Unique with shipment_id | Snapshot creation/cutoff time |
| eta_estimates | feature_cutoff_time | DATETIME | No | <= prediction_time | No | Point-in-time feature cutoff |
| eta_estimates | baseline_eta | DATETIME | No | UTC | No | ETA before adjustments |
| eta_estimates | predicted_eta | DATETIME | No | >= baseline_eta | No | Baseline plus source-derived adjustments |
| eta_estimates | predicted_delay_minutes | INT | No | >=0 minutes | No | max(0, predicted ETA - promised ETA) |
| eta_estimates | risk_level | ENUM | No | LOW, MEDIUM, HIGH | No | Derived delay risk |
| eta_estimates | weather_adjustment_minutes | INT | No | >=0 minutes | No | Active weather records at cutoff |
| eta_estimates | facility_adjustment_minutes | INT | No | >=0 minutes | No | Latest eligible queue + active disruptions |
| eta_estimates | route_adjustment_minutes | INT | No | >=0 minutes | No | Effective route change history |
| eta_estimates | carrier_adjustment_minutes | INT | No | >=0 minutes | No | Reliability + effective carrier calendar |
| eta_estimates | eligible_event_count | INT | No | >=0 rows | No | Eligible, nonduplicate tracking events |
| eta_estimates | rule_version | VARCHAR(30) | No | Version string | No | ETA rule version |
| eta_estimates | used_future_data | BOOLEAN | No | 0/1 | No | Labelled anomaly field; must be 0 for clean snapshots |
| delay_reasons | delay_reason_id | VARCHAR(30) | No | ID | Yes (PK) | Delay reason key |
| delay_reasons | reason_code | VARCHAR(40) | No | WEATHER, FACILITY_QUEUE, CARRIER_VARIANCE | Yes | Controlled reason code |
| delay_reasons | description | VARCHAR(255) | No | Text | No | Human-readable explanation |
| shipment_delay_assessments | assessment_id | VARCHAR(40) | No | ID | Yes (PK) | Assessment key |
| shipment_delay_assessments | shipment_id | VARCHAR(30) | No | shipments.shipment_id | No | Shipment FK |
| shipment_delay_assessments | delay_reason_id | VARCHAR(30) | Yes | delay_reasons.delay_reason_id | No | Reason FK |
| shipment_delay_assessments | actual_delay_minutes | INT | No | >=0 minutes | No | Actual delay |
| shipment_delay_assessments | outcome | VARCHAR(20) | No | DELAYED, ON_TIME, PENDING | No | Outcome |
| shipment_delay_assessments | assessed_at | DATETIME | No | UTC | No | Assessment timestamp |
| shipment_status_history | history_id | VARCHAR(50) | No | ID | Yes (PK) | History key |
| shipment_status_history | shipment_id | VARCHAR(30) | No | shipments.shipment_id | No | Shipment FK |
| shipment_status_history | previous_status | VARCHAR(30) | Yes | Lifecycle enum | No | Prior state |
| shipment_status_history | new_status | VARCHAR(30) | No | Lifecycle enum | No | New state |
| shipment_status_history | changed_at | DATETIME | No | UTC | No | Transition timestamp |
| shipment_status_history | source_event_id | VARCHAR(60) | Yes | tracking_events.event_id | No | Trigger event FK |
| data_quality_issues | issue_id | VARCHAR(50) | No | ID | Yes (PK) | Quality issue key |
| data_quality_issues | shipment_id | VARCHAR(30) | No | shipments.shipment_id | No | Shipment FK |
| data_quality_issues | record_id | VARCHAR(100) | No | Source record ID | No | Offending record |
| data_quality_issues | issue_type | VARCHAR(60) | No | Controlled issue label | No | Issue classification |
| data_quality_issues | severity | VARCHAR(20) | No | LOW, MEDIUM, HIGH, CRITICAL | No | Severity |
| data_quality_issues | detected_at | DATETIME | No | UTC | No | Detection timestamp |
| data_quality_issues | description | VARCHAR(255) | No | Text | No | Explanation |
| carrier_calendars | calendar_id | VARCHAR(40) | No | ID | Yes (PK) | Carrier calendar row |
| carrier_calendars | carrier_id | VARCHAR(30) | No | carriers.carrier_id | No | Carrier FK |
| carrier_calendars | effective_from | DATETIME | No | UTC | No | Inclusive effective start |
| carrier_calendars | effective_to | DATETIME | No | After effective_from | No | Exclusive effective end |
| carrier_calendars | adjustment_minutes | INT | No | >=0 minutes | No | Capacity/service adjustment |
| carrier_calendars | reason | VARCHAR(255) | No | Text | No | Calendar reason |
| facility_disruptions | disruption_id | VARCHAR(40) | No | ID | Yes (PK) | Disruption window key |
| facility_disruptions | facility_id | VARCHAR(30) | No | facilities.facility_id | No | Facility FK |
| facility_disruptions | start_time | DATETIME | No | UTC | No | Inclusive disruption start |
| facility_disruptions | end_time | DATETIME | No | After start_time | No | Exclusive disruption end |
| facility_disruptions | disruption_type | ENUM | No | CAPACITY_REDUCTION, CLOSURE, MAINTENANCE, WEATHER | No | Disruption class |
| facility_disruptions | disruption_minutes | INT | No | >=0 minutes | No | ETA impact |
| facility_disruptions | description | VARCHAR(255) | No | Text | No | Description |
| route_change_history | route_change_id | VARCHAR(60) | No | ID | Yes (PK) | Route revision key |
| route_change_history | shipment_id | VARCHAR(30) | No | shipments.shipment_id | No | Shipment FK |
| route_change_history | old_route_id | VARCHAR(30) | No | routes.route_id | No | Previous route FK |
| route_change_history | new_route_id | VARCHAR(30) | No | routes.route_id | No | Replacement route FK |
| route_change_history | effective_at | DATETIME | No | UTC | No | When change becomes visible |
| route_change_history | transit_adjustment_minutes | INT | No | >=0 minutes | No | Route revision impact |
| route_change_history | change_reason | ENUM | No | WEATHER_REROUTE, FACILITY_CLOSURE, CARRIER_CHANGE, PLANNING_UPDATE | No | Controlled change reason |
| route_change_history | ground_truth_label | VARCHAR(30) | No | ROUTE_CHANGED | No | Label for deliberate route-change sample |
| generation_runs | run_id | VARCHAR(40) | No | ID | Yes (PK) | Generator execution key |
| generation_runs | seed_value | BIGINT | No | Integer | No | Reproducibility seed |
| generation_runs | dataset_size | VARCHAR(20) | No | starter, medium, full | No | Dataset scale |
| generation_runs | shipment_count | INT | No | >=0 rows | No | Generated shipments |
| generation_runs | event_count | INT | No | >=0 rows | No | Generated events |
| generation_runs | generated_at | DATETIME | No | UTC | No | Generation timestamp |
| generation_runs | manifest_json | JSON | No | Valid JSON | No | File counts and checksums |

## Point-in-time and quality rules

- A tracking event is eligible only when **both** `event_time <= feature_cutoff_time` and `ingestion_time <= feature_cutoff_time`; duplicates are retained for audit but excluded from feature calculation.
- Weather contributes only while `start_time <= cutoff < end_time` and its region intersects the shipment's active route region.
- Facility adjustment uses the latest queue record at/before cutoff plus disruption windows active at cutoff.
- Carrier adjustment uses reliability plus an effective-dated carrier calendar active at cutoff.
- Route-change adjustment is applied only when `effective_at <= cutoff`.
- ETA rows are immutable snapshots, unique by `(shipment_id, prediction_time)`. Required anchors include creation, departure, intermediate arrival, and later tracking update ingestion times.
- Deliberate anomaly rows must have a matching `ground_truth` record and `data_quality_issues` label. Never silently deduplicate or silently repair source history.
