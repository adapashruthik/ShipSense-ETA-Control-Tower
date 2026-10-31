# YottaFlex AI Submission Checklist

This checklist is based on the supplied *Candidate Project Submission Guidelines* and *Candidate Project FAQ*.

## 1. Executable project
- [x] Source code and dependency list included.
- [x] Local setup and run instructions included in `README.md`.
- [x] MySQL schema and `.env.example` included.
- [x] Synthetic starter data can be generated with a fixed seed.
- [x] Automated validation and tests included.
- [ ] Candidate performs a clean install/run from a fresh clone before submission.
- [ ] Candidate confirms all dashboard workflows on their own machine.

## 2. Public repository
- [ ] Create a new, dedicated **public** GitHub repository.
- [ ] Push this project to that repository.
- [ ] Use meaningful commits that accurately describe work actually performed. Do not manufacture historical commits or dates.
- [ ] Keep the repository available and editable until the stated 72-hour deadline.
- [ ] Submit the repository URL using the same email address used during recruitment.

## 3. AI transparency
- [x] `PROMPT_HISTORY.md` is included as a working record.
- [ ] Candidate adds every prompt sent to every AI tool used, including tools outside this ChatGPT conversation.
- [ ] Candidate checks that the prompt log is complete and accurate; the included record is explicitly marked as reconstructed/partial.
- [ ] Candidate explains what AI accelerated, where it was relied upon, and what the candidate personally reviewed, changed and validated.

## 4. Reasoning and ownership
- [x] Architecture, business rules, data dictionary, validation and limitations documents included.
- [ ] Candidate fills in the personal review and ownership statements in `docs/CANDIDATE_WALKTHROUGH.md` in their own words.
- [ ] Candidate can explain the point-in-time cutoff, ETA adjustments, data model, anomaly labels and test cases without reading a script.
- [ ] Candidate discloses any feature that is incomplete or simplified.

## 5. Security and repository hygiene
- [x] `.env` and `.venv` are ignored by Git.
- [x] `.env.example` contains placeholders, not credentials.
- [ ] Check for credentials, tokens, private data and unintended files before making the repository public.
- [ ] Do not upload personal or sensitive information or proprietary code that you are not authorized to publish.

## 6. Submission timing
- [ ] Confirm the exact timestamp and timezone when YottaFlex sent the project.
- [ ] Calculate the deadline as exactly 72 hours after that timestamp.
- [ ] Submit before the deadline. Artifact timestamps may be used to verify the window.

## Before clicking Submit
- [ ] Fresh-clone setup completed successfully.
- [ ] MySQL schema applied and data loaded.
- [ ] Validation command passed.
- [ ] Full test suite passed.
- [ ] API and Streamlit dashboard manually checked.
- [ ] Prompt history completed and truthful.
- [ ] Public GitHub URL opens in a logged-out/private browser window.
- [ ] Candidate is ready for a live walkthrough.
