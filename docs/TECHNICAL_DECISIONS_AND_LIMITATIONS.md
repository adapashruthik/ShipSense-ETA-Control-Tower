# Technical Decisions, Assumptions and Limitations

This document records the current design as implemented/documented in the repository. The candidate should review it against the code and revise any statement that does not match their final version.

## Architecture

The local workflow is:

`Synthetic data generator -> CSV/JSON -> validation -> MySQL -> FastAPI -> Streamlit`

The ETA rules are isolated under `engine/`. The relational database preserves shipment, route-leg, tracking-event, ETA-snapshot and history records separately.

## Key decisions

1. **Local-first stack:** Python, MySQL, FastAPI and Streamlit can run locally. This avoids requiring a paid cloud service for the candidate demonstration.
2. **Deterministic synthetic data:** a fixed seed supports repeatable generation and reproducibility checks. Synthetic records are not represented as real carrier or weather feeds.
3. **Separate event and ingestion times:** point-in-time event eligibility uses both timestamps. A record is eligible only when its event time and ingestion time are at or before the prediction cutoff.
4. **Append-only ETA history:** snapshots preserve what the system predicted at a particular cutoff instead of replacing earlier predictions.
5. **Explainable baseline:** ETA is calculated using explicit source-derived adjustments and a rule version. It is not a trained machine-learning model.
6. **Ground-truth separation:** labelled anomalies and outcome data are kept separate from prediction inputs to reduce leakage risk.
7. **Validation before use:** generated data is checked for key integrity, allowed values, chronology, lifecycle rules, duplicate labels and ETA snapshot constraints.

## Assumptions and simplifications to disclose

- The supplied dataset is synthetic and fixed-seed; it is not evidence of performance on production carrier data.
- External carrier APIs, live weather providers and live facility systems are not integrated in this local demonstration.
- ETA logic is a deterministic, explainable baseline. Passing rule tests does not establish real-world ETA accuracy or a measured MAE on representative production data.
- Route, weather, queue and carrier effects are represented through the project's generated fields and rules. Explain the specific formulas from `engine/eta_engine.py` during the walkthrough.
- The current verification log demonstrates automated checks and successful API responses. Manual dashboard workflows must also be checked before claiming complete end-to-end verification.
- MySQL schema upgrades may require migrations when an older database already exists; `CREATE TABLE IF NOT EXISTS` alone does not add columns to existing tables.

## Testing evidence available

The candidate's supplied Windows PowerShell log reports:
- Python 3.13.1 and `pip check` with no broken requirements.
- Data validation: 68 checks passed, 0 failed.
- Pytest: 17 passed.
- Prediction correctness suite: 8 passed.
- FastAPI application startup completed.
- Multiple API requests returned HTTP 200, including health, overview, facilities, risk distribution, high-risk shipments, shipment detail, delay reasons, anomalies and metadata options.

This evidence does not, by itself, confirm a fresh-clone install or every manual dashboard workflow. Keep that distinction clear.
