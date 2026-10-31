# Prediction correctness tests

These tests exercise the real `engine.eta_engine.derive_source_features()` and
`predict_eta()` functions using controlled source-record fixtures. They do not
connect to MySQL and do not modify generated CSV files.

## What is tested

- An active weather event increases ETA by its configured travel impact.
- The latest eligible facility queue snapshot changes ETA in the expected direction.
- Changing a route plan's base transit time changes ETA.
- An effective route-change record changes ETA.
- A newly ingested, eligible carrier tracking event advances the shipment's
  remaining route and changes ETA.
- Future tracking events, weather, queues, route changes, carrier calendars and
  facility disruptions do not affect a prediction made before they become valid.
- An event with an old event timestamp but a later ingestion timestamp is
  excluded (prevents late-arriving data leakage).

## Run on Windows PowerShell

From the project root (the folder containing `requirements.txt`):

```powershell
.\.venv\Scripts\Activate.ps1
python -m pytest -v tests/test_prediction_correctness.py
```

Run the complete suite:

```powershell
python -m pytest -v
```

Expected result for the supplied project version: **17 tests passed**.

## Important interpretation

The tests validate the current rule engine's behaviour against controlled
fixtures. They are regression tests, not proof of predictive accuracy against
real-world delivery outcomes. They also assume the current engine's model:
`leg_status == "COMPLETED"` plus an eligible event for that leg marks the leg
as completed. If the business rule changes, update the fixture and assertions
alongside the engine.
