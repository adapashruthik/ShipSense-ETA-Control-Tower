# ShipSense — Start here (Windows / VS Code)

## First-time setup

1. Open this folder in VS Code and create/open a PowerShell terminal.
2. `py -3.11 -m venv .venv`
3. `\.venv\Scripts\Activate.ps1`
4. `python -m pip install --upgrade pip`
5. `python -m pip install -r requirements.txt`
6. Copy `.env.example` to `.env`; set your local MySQL password.
7. Start MySQL Server using the Windows Services app if it is not already running.
8. In MySQL Workbench, execute `database/schema.sql`.
9. Generate starter data: `python -m generator.generate --size starter --seed 20261022`
10. Validate: `python -m validation.validate_data`
11. Load once: `python scripts/load_data.py`

## Every normal launch

- VS Code Terminal 1: activate `.venv`, then `uvicorn backend.app.main:app --reload`
- VS Code Terminal 2: activate `.venv`, then `python -m streamlit run dashboard/app.py`
- Open `http://localhost:8501`

## Dashboard input options

- `New Shipment`: manual entry and immediate ETA calculation.
- `CSV Upload`: download the template, fill rows using valid IDs from your database, then upload.
- `Synthetic Data`: choose starter/medium/full and a fixed seed. The load action replaces existing database data and must be used only on a development database after confirming the warning.

## Useful checks

- `http://127.0.0.1:8000/api/health`
- `http://127.0.0.1:8000/docs`
- `pytest -v`

If the MySQL service cannot be started from the non-admin terminal, use Windows Services or MySQL Workbench to confirm the server is running; do not run FastAPI or Streamlit as Administrator.


## Updated data generation and audit
Run `python -m generator.generate --size starter --seed 20261022`, then `python -m validation.validate_data`, then `pytest -q`. See `docs/DATA_DICTIONARY.md` for field-level definitions and `docs/PRIORITY_IMPLEMENTATION.md` for the six requested upgrades.
