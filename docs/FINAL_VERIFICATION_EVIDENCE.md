# Final Verification Evidence

Evidence transcribed from the candidate's supplied Windows PowerShell execution log on 31 October 2026. This is a record of the output shared in the conversation, not an independent execution by the repository author.

| Check | Reported result |
|---|---:|
| Python | 3.13.1 |
| `pip check` | No broken requirements found |
| Data validation | 68 passed, 0 failed |
| Full pytest suite | 17 passed |
| Prediction correctness tests | 8 passed |
| FastAPI startup | Application startup complete |
| API responses | Shown requests returned HTTP 200 |

Commands shown in the supplied log:

```powershell
python -m validation.validate_data
python -m pytest -v
python -m pytest -v --junitxml=docs/test_report.xml
python -m pytest -v tests/test_prediction_correctness.py
uvicorn backend.app.main:app --reload
```

The log showed successful API requests to health, analytics overview, facilities, risk distribution, high-risk shipments, shipment detail, delay reasons, shipment list, metadata options and anomalies.

## Remaining evidence to capture before submission

- Screenshot of Streamlit overview with populated data.
- Screenshot of shipment details and ETA explanation.
- Evidence of manual shipment creation and CSV upload, if those workflows are part of the final demo.
- Evidence that exception and data-quality pages render correctly.
- Fresh-clone setup test (not just execution in the existing virtual environment).
