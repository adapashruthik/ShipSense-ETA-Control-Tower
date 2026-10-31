# Architecture

Synthetic data generator -> CSV/JSON -> validation -> MySQL -> FastAPI -> Streamlit.

The ETA engine is an isolated, explainable rule module. It accepts point-in-time eligible feature values and emits a prediction with baseline, adjustments, risk and rule version. Event selection must use both event_time and ingestion_time cutoffs.

MySQL is the source of truth. Shipment status history, tracking events and ETA estimates are separate records to preserve traceability.
