# ShipSense – Logistics ETA Prediction & Delay Intelligence

A local-first logistics control tower that combines synthetic carrier events, multi-leg routes, weather disruptions and facility queues to produce traceable ETA estimates, delay outcomes and data-quality exceptions.

## What is included

- MySQL relational schema with primary/foreign keys and history tables.
- Deterministic synthetic data generator: starter (1,000), medium (10,000), full (50,000) shipments.
- 100 facilities, 1,000 weather disruption windows, tracking events and facility queue snapshots.
- Separate ground-truth JSON/CSV for deliberately injected anomaly scenarios.
- Point-in-time event eligibility helper and explainable ETA rule engine. Shared ETA risk policy: LOW (0–30 min late), MEDIUM (31–120 min late), HIGH (>120 min late).
- FastAPI REST API and Streamlit dark ETA control tower with manual shipment entry, CSV bulk import and synthetic dataset generation.
- Data validation, reproducibility check and Pytest unit tests.

## Technology

Python 3.11+, MySQL 8, FastAPI, SQLAlchemy, PyMySQL, Pandas, Streamlit, Plotly and Pytest.

## 1. Configure

Create a virtual environment (Windows PowerShell):

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env
```

Edit `.env` and set your MySQL password. Create the database and tables:

```powershell
mysql -u root -p < database/schema.sql
```

If the `mysql` command is not on PATH, open MySQL Workbench, connect to your local MySQL server and execute `database/schema.sql`.

## 2. Generate starter data

```powershell
python -m generator.generate --size starter --seed 20261022
python -m validation.validate_data
```

Available scales:

```powershell
python -m generator.generate --size medium --seed 20261022
python -m generator.generate --size full --seed 20261022
```

The generator exports CSV files under `data/generated/`, and separate ground-truth files under `data/ground_truth/`. The full dataset writes approximately 300,000 tracking events. Start with starter scale before using full scale.

## 3. Load generated CSV files into MySQL

```powershell
python scripts/load_data.py
```

The loader uses `INSERT IGNORE`; for a clean regeneration, clear the database tables first or use a fresh database. Ground truth is intentionally not loaded into the prediction input tables.

## 4. Start the API

Open PowerShell terminal 1:

```powershell
uvicorn backend.app.main:app --reload
```

API health: http://127.0.0.1:8000/api/health  
Swagger documentation: http://127.0.0.1:8000/docs

## 5. Start the dashboard

Open PowerShell terminal 2:

```powershell
streamlit run dashboard/app.py
```

Open the local URL shown by Streamlit, normally http://localhost:8501.

## 6. Run tests and reproducibility

```powershell
pytest -v
python -m validation.reproducibility
```

Reproducibility runs the starter generator twice with the same seed and compares SHA-256 checksums. It rewrites starter CSV exports.

## API examples

- `GET /api/analytics/overview`
- `GET /api/shipments?limit=100`
- `GET /api/shipments/SHP-2026-000001`
- `GET /api/shipments/SHP-2026-000001/events`
- `GET /api/shipments/SHP-2026-000001/eta`
- `GET /api/delays`
- `GET /api/anomalies`
- `GET /api/facilities`
- `GET /api/carriers/performance`

## Important modelling notes and limitations

1. Synthetic data is generated with a fixed seed. It is not real carrier or weather data.
2. The ETA rule engine is an explainable baseline. It is not a trained production model.
3. The generator preserves event time and ingestion time separately. The point-in-time helper requires both to be at or before the prediction cutoff.
4. The generator creates labelled anomaly cases. Ground-truth exports must not be joined into model input features.
5. The sample dashboard reads from MySQL through FastAPI. ETA prediction logic is separately unit-tested; production prediction persistence and online inference can be extended.
6. Some disruption/route relationships are simplified for a self-contained candidate project. Document any additional assumptions made during review.

## Project structure

- `database/`: MySQL DDL
- `generator/`: deterministic synthetic data generation
- `engine/`: ETA, delay and anomaly logic
- `backend/`: FastAPI endpoints
- `dashboard/`: Streamlit UI
- `validation/`: integrity and reproducibility checks
- `tests/`: automated tests
- `docs/`: PRD, architecture, data dictionary and reports

## GitHub submission

Create a dedicated public repository. Do not commit `.env`, passwords or personal information. Commit code in meaningful stages and include `PROMPT_HISTORY.md` with the prompts used with AI tools. Be prepared to explain and modify every important component yourself.


## Interactive dashboard inputs (v2)

The dashboard now follows the uploaded ETA control-tower reference and includes:
- **New Shipment**: manual shipment creation with facility/carrier/service-level validation and saved ETA snapshot.
- **CSV Upload**: bulk ingestion with a downloadable template and per-row validation results.
- **Synthetic Data**: starter/medium/full deterministic generation. Loading a generated dataset replaces the current database contents and requires explicit confirmation.
- **Overview**: network KPIs, facility queue schematic, high-risk shipment list and delay-driver analysis.

Install the updated requirements after replacing the project files:

```powershell
python -m pip install -r requirements.txt
```

Read `docs/INTERACTIVE_INPUTS.md` for required CSV columns, ETA assumptions and destructive-operation details. The online ETA is an explainable rule-based baseline, not a trained ML model or live external feed.


## Audited ETA integration (v3.0)

The generator now creates point-in-time ETA snapshots at shipment creation, visible departure/arrival milestones, and carrier update ingestion times. Each snapshot is computed from eligible source rows only:
- tracking events require both event time and ingestion time at/before cutoff; duplicates are retained but excluded;
- weather impacts are derived from active regional weather records;
- facility delay is derived from latest eligible queue snapshots and active disruption windows;
- route delay is derived from effective-dated route-change history;
- carrier delay is derived from reliability and effective-dated carrier calendars.

Additional generated tables: `carrier_calendars.csv`, `facility_disruptions.csv`, and `route_change_history.csv`. Deliberate duplicate events and route changes are labelled in `ground_truth.csv/json` and `data_quality_issues.csv`.

### Generate and validate
```powershell
python -m generator.generate --size starter --seed 20261022
python -m validation.validate_data
pytest -q
```
The validator writes `docs/VALIDATION_REPORT.json`. Use `starter` first; `medium` and `full` generate larger datasets.


## Prediction correctness and point-in-time regression tests

A focused regression suite verifies that weather, facility queue snapshots,
route plans, route changes and eligible carrier tracking events affect ETA in
the expected direction. It also verifies that future-dated source records and
late-ingested events cannot leak into an earlier prediction.

Run:

```powershell
python -m pytest -v tests/test_prediction_correctness.py
```

See `docs/PREDICTION_CORRECTNESS_TESTS.md` for coverage and interpretation.


