# Candidate Walkthrough – Prepare in Your Own Words

This is a preparation worksheet, not a script to claim as personal experience. Fill it in after reviewing the implementation. You should be able to explain and modify the core logic yourself.

## 1. One-minute project explanation

Write a concise explanation of the logistics problem, what ShipSense accepts as input, what it predicts, and who uses the control tower.

**Candidate notes:**

[Write your explanation here.]

## 2. Walkthrough order

1. Show the architecture in `docs/ARCHITECTURE.md`.
2. Show the schema in `database/schema.sql` and explain shipment, legs, routes, tracking events and ETA snapshots.
3. Show deterministic data generation in `generator/generate.py`.
4. Explain event time versus ingestion time and the cutoff rule in `engine/eta_engine.py`.
5. Walk through each ETA adjustment and explain its source field and direction.
6. Show validation in `validation/validate_data.py`.
7. Run the focused prediction tests and the complete pytest suite.
8. Start FastAPI and demonstrate `/docs`.
9. Start Streamlit and demonstrate overview, shipment lookup, ingestion, exceptions and data quality where supported.
10. State limitations and next steps honestly.

## 3. Questions you should be able to answer

- Why are event time and ingestion time both required?
- How does the engine prevent a future event from influencing an earlier prediction?
- How are weather, facility queue, route and carrier adjustments derived?
- What is an ETA snapshot and why is it retained?
- How are duplicate events handled?
- Why is ground truth separated from prediction features?
- What happens when a source record arrives late?
- What does the rule-based ETA model not do?
- Which tests prove directionality and which tests prove temporal eligibility?
- What would you change to integrate real carrier/weather/facility feeds?

## 4. Personal AI-use reflection – candidate must complete

- AI tools used (list every tool):
- What AI accelerated:
- Where I relied heavily on AI:
- Code/design I personally inspected:
- Changes I personally made:
- Tests I personally ran and interpreted:
- Limitations or generated code I could not fully verify:
- What I can explain and modify independently:

Do not claim that AI-generated work was independently authored unless that is accurate. The FAQ allows AI assistance but requires individual ownership, understanding and validation.
