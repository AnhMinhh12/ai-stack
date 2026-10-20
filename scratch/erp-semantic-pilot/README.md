# ERP catalog SQL agent: offline pilot

This harness reads the 18 questions from `sales_question.xlsx`, retrieves up to four of the 82 existing report definitions using the local model, supplies the retrieved manifests/SQL and live PostgreSQL column metadata, and asks the same model to generate a new SELECT. It bypasses all existing intent handlers. One repair is allowed on SQL execution failure. Empty results are not automatically rewritten.

It is an operator-run experiment, **not a production endpoint**. It uses the configured read-only database account, READ ONLY transactions, a 20-second statement timeout, and a 200-row fetch cap. The lightweight SQL guard is only a pilot sanity check; it is not a complete SQL sandbox. It does not implement application user row-level permissions and must not be exposed to chat users. Baseline prompts say not to use `userinfo`; that instruction alone is not access enforcement. The improved harness rejects that table outright to prevent invented user identities in this audit. Production must instead inject trusted scope outside the model. No production configuration was changed.

Run from repository root:

```bash
python3 scratch/erp-semantic-pilot/build_bundle.py
docker exec -i open-webui python - < /tmp/erp-semantic-pilot-run.py > docs/evidence/ERP-SEMANTIC-PILOT-20261020/results.jsonl
docker exec -i open-webui python - < scratch/erp-semantic-pilot/reference.py > docs/evidence/ERP-SEMANTIC-PILOT-20261020/reference.jsonl
```

`build_bundle.py` uses only Python's standard library to read XLSX. It reads question text, not the suggested source/answer notes in the spreadsheet. Existing report SQL is retrieval context, so this measures reuse of known ERP knowledge, not zero-shot schema discovery. Report validation labels are preserved. The model uses the first configured internal endpoint; no external model endpoint is called.

The first pilot deliberately uses the same supplied entity pool across cases: material QC7-5146-000, customer KH0034, mold K_QC5-0980-000-V2, date window 2026-10-01..2026-10-20. These entities are individually real but not necessarily related. This is a limitation of the fixture: incorrect cross-application of these parameters must not be treated as evidence of missing DB data. Date defaults can also bias “latest” questions. The questions are templates; they are not fully specified end-user requests.

Evidence distinction:

- `executed`: PostgreSQL ran the generated SQL, not evidence of business correctness.
- Reference probes: independently written read-only checks. They establish specific facts under stated filters, not full ERP UI parity.
- Human review: compare grain, joins, document status, effective dates, requested filters, and result meaning. Numeric matches alone do not establish correctness on other entities or dates.
- Live DB changes during the run can affect comparisons. No shared snapshot spans all connections.

No training, fine tuning, deployment, or universal coverage claim is part of this experiment.

Improved selected-case pass (same local model, generic semantic notes, JSON mode, no full UI SQL in the prompt):

```bash
ERP_PILOT_NOTES=scratch/erp-semantic-pilot/semantic-notes.txt python3 scratch/erp-semantic-pilot/build_bundle.py
docker exec -e ERP_PILOT_JSON_MODE=1 -e ERP_PILOT_CASES=1,2,4,7,14,17 -i open-webui python - < /tmp/erp-semantic-pilot-run.py > docs/evidence/ERP-SEMANTIC-PILOT-20261020/improved.jsonl
```

`run_baseline.py` preserves the original harness. `run.py` is the improved version. The improved pass is an in-sample refinement based on observed failures, not an independent holdout evaluation. It does not justify a general accuracy rate.
