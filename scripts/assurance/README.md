# Q10–Q16 Evidence Adapter Prototype (read-only)

This prototype validates metadata binding for a supplied JSON report. It is intentionally not a scanner, gate evaluator, workflow action, credential broker or deployment tool.

## Safety properties

- Reads one local JSON report and writes one normalized JSON envelope.
- Does not execute the named tool or contact external services.
- Does not read or request secrets.
- Requires exact source SHA, source tree, runtime-subject digest and artifact digest.
- Marks missing, stale or incomplete evidence as `INCOMPLETE`.
- A complete report is labelled `EVIDENCE_READY_FOR_GATE_EVALUATION`, never `PASS`.
- Explicitly records that gate state was not changed and gate PASS was not claimed.

## Local synthetic-only test

```bash
python -m unittest discover -s tests/assurance -p 'test_*.py' -v
```

No real gate evidence should be fed into this prototype until the schema and provenance contracts are reviewed. It is not wired into GitHub Actions or production.
