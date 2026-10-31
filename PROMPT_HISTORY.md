# AI Prompt History and Usage Disclosure

## 1. Introduction

I used ChatGPT and claude ai  as an AI-assisted development and learning tool during the development of the **ShipSense – ETA Control Tower** project.

My objective was to build a local-first logistics intelligence platform that combines carrier tracking events, route plans, weather conditions, and facility queues to predict shipment arrival times and identify potential delays.

AI assistance was used for project planning, architecture discussions, implementation guidance, debugging, testing strategies, documentation, and technical explanations.

I reviewed and executed the implementation locally and used the resulting validation and test outputs to verify the application.

**Transparency note:** This document contains a reconstructed record of the prompts available from my ChatGPT project conversations. It is not a complete verbatim export of every interaction. I have not included prompts from other AI tools unless explicitly documented below.

## 2. AI Tool Used

| Tool | Purpose |
|---|---|
| ChatGPT | Project planning, architecture guidance, implementation assistance, debugging, testing, documentation, and technical explanations |

Other AI tools: None declared in this record. I will update this disclosure if I used additional tools during the project.

## 3. Project Planning and Architecture Prompts

The following prompts summarize my initial project requirements and planning discussions.

**Prompt 1 – Project architecture and planning**

> Design a local-first logistics ETA prediction and delay intelligence platform that combines carrier events, route plans, weather conditions, and facility queues. Include database entities, deterministic synthetic data generation, temporal leakage prevention, labelled anomaly scenarios, a REST API, dashboard, automated tests, documentation, and reproducibility.

**Prompt 2 – Technology stack and implementation**

> Create a complete runnable project using Python and MySQL as the backend. Use suitable frameworks for the REST API and dashboard. Avoid paid AWS services and prefer free, locally executable technologies.

**Prompt 3 – ETA prediction improvements**

> Improve the ETA prediction engine so that weather, facility queue, route, and carrier adjustments are calculated from their actual source records and eligible tracking events instead of randomly generated adjustment values.

## 4. Data Engineering and Business Logic Prompts

**Prompt 4 – Multiple ETA snapshots**

> Implement multiple ETA prediction snapshots at defined shipment lifecycle stages and prediction timestamps. Ensure that each prediction uses only information available at its prediction cutoff.

**Prompt 5 – Temporal data correctness**

> Prevent future-information leakage in ETA predictions. Use event timestamps, ingestion timestamps, and effective timestamps to determine whether information is eligible for a prediction.

**Prompt 6 – Data quality and anomaly handling**

> Include deliberately duplicated tracking events, route-change history, effective-dated carrier calendars, facility disruption windows, labelled ground truth, and comprehensive data validation.

**Prompt 7 – Data dictionary**

> Create a field-level data dictionary documenting the database entities, attributes, meanings, and relationships.

## 5. Prediction Engine and Testing Prompts

**Prompt 8 – Prediction correctness testing**

> Verify that changing weather conditions, facility queues, route plans, and carrier tracking events changes the predicted ETA appropriately, without using future information.

**Prompt 9 – Point-in-time validation**

> Create automated tests to verify that future tracking events, future weather records, future facility queues, future route changes, and late-ingested events do not affect historical ETA predictions.

**Prompt 10 – Automated testing**

> Create automated tests for ETA adjustments, prediction risk levels, shipment lifecycle anomalies, duplicate events, and temporal data correctness.

## 6. Execution and Debugging Prompts

I used ChatGPT to troubleshoot issues encountered while executing the application locally on Windows.

The main assistance requests included:

1. Troubleshooting Python version compatibility and virtual environment activation in Windows PowerShell.
2. Correcting MySQL connection configuration and authentication errors.
3. Resolving database schema mismatches, including the missing `eligible_event_count` column.
4. Troubleshooting CSV-to-MySQL data loading.
5. Running the FastAPI backend and Streamlit dashboard.
6. Preparing step-by-step PowerShell execution instructions.
7. Investigating API errors and database connectivity problems.

## 7. Validation and Verification Prompts

I requested guidance to verify the complete application against the original problem statement.

The verification work included:

- Database table and relationship validation.
- Primary-key and foreign-key checks.
- Enum and timestamp validation.
- Shipment lifecycle validation.
- Duplicate event identification.
- Multiple ETA snapshot verification.
- Prediction sensitivity testing.
- Future-information leakage testing.
- API endpoint verification.
- Dashboard workflow verification.

## 8. How AI Assisted My Development

ChatGPT helped accelerate the development process in the following areas:

| Area | AI assistance |
|---|---|
| Project planning | Requirements analysis and architecture suggestions |
| Backend | Implementation guidance and debugging |
| Database | MySQL schema design and troubleshooting |
| ETA engine | Prediction logic discussions and implementation assistance |
| Data engineering | Synthetic data generation and validation guidance |
| Testing | Test scenario design and automated test assistance |
| Documentation | README, architecture, data dictionary, and submission documentation |
| Execution | Windows PowerShell and environment troubleshooting |

## 9. My Implementation and Verification Work

I executed the project locally on Windows using Python 3.13.1 and MySQL.

I personally ran the following verification commands:

```powershell
python -m validation.validate_data
```

```powershell
python -m pytest -v
```

```powershell
python -m pytest -v tests/test_prediction_correctness.py
```

I also started the FastAPI backend and verified the API requests through the local application logs.

