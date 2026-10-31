# Business rules and assumptions

- Service-level promise is created_at + configured service-level SLA hours in this starter implementation.
- Actual delivery is generated from a simulated transit duration and disruption impact, and delay outcome is calculated from actual vs promised time.
- Event and ingestion timestamps are distinct. A valid point-in-time feature must satisfy both cutoff conditions.
- ETA adjustment components are non-negative and individually recorded.
- LOW risk means predicted delay is 0–30 minutes; MEDIUM means 31–120 minutes; HIGH means more than 120 minutes. These are transparent business thresholds, not calibrated probabilities.
- The sample data generator is synthetic and deterministic for a given seed and scale.
- Ground truth is kept outside generated model-input CSVs.

- For delivered synthetic shipments, the final carrier event is a DELIVERED scan; its event_time is the shipment actual_delivery_at source timestamp. The delay label is derived by comparing that timestamp with promised_delivery_at.

- Manual-entry priority adjustment is non-negative: HIGH priority adds 0 minutes, MEDIUM adds 10 minutes, and LOW adds 20 minutes. This is a documented simulation assumption, not a measured carrier SLA.
