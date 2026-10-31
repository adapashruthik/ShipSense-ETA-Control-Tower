# ShipSense interactive ingestion and ETA workflow

## Three input modes

1. **Manual entry** in the Streamlit `New Shipment` page. The UI obtains valid facility, carrier and service-level IDs from `GET /api/meta/options`. `POST /api/shipments` creates a shipment, one initial leg, a `CREATED` tracking event, a status-history row, optional weather/queue records, and an immutable ETA snapshot.
2. **CSV bulk import** in the `CSV Upload` page. Download the template, populate rows, and upload. Required columns: `origin_facility_id`, `destination_facility_id`, `carrier_id`, `service_level_id`, `promised_delivery_at`, `total_distance_km`. Optional: `weather_condition`, `facility_wait_minutes`, `priority`. Each valid row is committed independently; invalid rows are returned with row number and error.
3. **Synthetic dataset generation** in the `Synthetic Data` page. Select starter/medium/full and a fixed seed. Loading into MySQL requires explicit confirmation because it replaces existing synthetic/master/transaction tables, including manually entered shipments. For file-only generation use `python -m generator.generate --size starter --seed 20261022`.

## ETA calculation

The current online inference is an explainable deterministic baseline, not a trained ML model or live carrier/weather feed. Baseline transit time is distance divided by a service-level speed assumption. Adjustments are applied for selected weather, entered facility queue wait and carrier reliability. The prediction, feature cutoff, rule version and individual adjustments are persisted in `eta_estimates`. The initial event time and ingestion time are recorded separately.

Weather assumptions (minutes): CLEAR 0, LIGHT_RAIN 10, HEAVY_RAIN 35, FOG 25, STORM 75, FLOODING 120. Carrier adjustment is `max(0, round((100 - reliability_score) * 2))`. Risk is HIGH when predicted delay exceeds 120 minutes, MEDIUM when predicted delay is positive, otherwise LOW.

## Run

Install `python-multipart` with the requirements, apply `database/schema.sql`, generate/load starter data once, then start FastAPI and Streamlit in separate terminals. See README.md for full commands.

## Safety / operational note

The synthetic replacement endpoint is destructive and is protected by an explicit UI checkbox. Do not use it against production data. Use a separate development database for the hackathon. Times entered in the UI are interpreted as UTC for this candidate project.
