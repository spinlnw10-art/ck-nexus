# Q13 PostgreSQL Disaster-Recovery Assessment — 2026-11-23

Status: READ-ONLY DESIGN ASSESSMENT — NO DATABASE OR HOST OPERATIONS
Base commit: `944d7cb70a5d59d53c8fb379752bbee2085f7c8c`

## Executive finding

CK-NEXUS already has a guarded PostgreSQL logical backup/restore drill:
- `scripts/postgres_dr.py` creates a custom-format `pg_dump`, calculates SHA-256, writes a checksum manifest, verifies the checksum before restore, restores into a separately configured target, checks required tables and measures restore duration against an RTO threshold.
- `scripts/gate_postgres_dr.py` requires staging environment, isolated-DR target classification and an explicit destructive-restore acknowledgement; it rejects a source and target with the same parsed host/port/database identity.
- `.github/workflows/candidate-automated-gates.yml` provisions an ephemeral PostgreSQL 16 service, seeds synthetic tables/data, creates a separate restore database, runs the gate and checks a sentinel round-trip.
- Existing Q13 evidence is historical and bound to source SHA `4cf17cd3befaafeaf64cd4c149739133aa220f73`, tree `dfe3888bb6adc9aebbb0351efe4a06006f4e0a48`, and manifest `96dcd0f0f93b1aaa69e88da30fedcce1b786b51b83f36b72baf7ac910d02b04f`. It is not current-candidate evidence.

## Verified strengths

1. Destructive restore is guarded by explicit staging, isolated-target class and acknowledgement environment variables.
2. A basic source/target database identity comparison prevents the obvious same-database restore case.
3. Backup integrity is checked using a locally generated SHA-256 manifest before restore.
4. Restore verifies required application table names and a separate workflow sentinel round-trip.
5. Restore duration is compared with a configurable RTO target.
6. Workflow uses synthetic ephemeral database content, not production records, and uploads candidate evidence.

## Gaps and risks

1. **RPO is not measured.** The backup function records a configured `rpo_target_seconds`, but the current drill does not calculate the age of the recovered data or prove a recovery point relative to a known write timestamp.
2. **PITR is not tested.** The workflow uses a logical `pg_dump`/restore. It does not exercise WAL archiving, base backups, timeline selection or point-in-time recovery.
3. **RTO coverage is incomplete.** The restore helper measures the restore phase, not the complete incident timeline from recovery request through service health and application-level verification.
4. **Application consistency is shallow.** The current CI fixture creates four empty tables and one sentinel row. It does not verify foreign keys, indexes, sequences, extensions, roles/grants, schema migrations, large objects or representative application invariants.
5. **Database identity comparison is syntactic.** Host aliases, DNS changes, proxies, multi-host URLs and different credentials resolving to the same server may defeat a host/port/database string comparison. It is a safety check, not proof of physical isolation.
6. **Credential handling needs review.** PostgreSQL URLs are passed as command-line arguments to client processes. Avoid real credentials in command-line arguments/process listings; use ephemeral CI-only credentials and evaluate a protected libpq service/passfile or carefully scoped environment-based connection configuration for any future staging integration.
7. **Evidence lacks full artifact provenance.** The gate output includes backup digest, but the outer evidence should also bind the backup metadata, PostgreSQL server/client versions, sanitized topology identity, test fixture digest, workflow run and raw logs.
8. **No retention/restore-point policy is validated.** A one-off dump does not prove scheduled backup frequency, retention, off-host/off-account storage, encryption, immutable retention or restore-point discoverability.
9. **No production topology is established.** pgBackRest, Barman, native WAL archiving or managed-provider PITR cannot be selected responsibly until the actual PostgreSQL hosting topology, storage, permissions, RPO/RTO and network boundaries are known.
10. **Historical documentation can mislead.** `RELEASE_STATUS.md` marks Q13 NOT_VERIFIED / STALE SUBJECT for the current release line. Older checklists and candidate runs do not override this.

## Tool selection

| Requirement | Candidate | Selection guidance |
|---|---|---|
| Existing logical backup/restore | PostgreSQL `pg_dump` / `pg_restore` | Keep for portable logical restore and schema/data smoke |
| Physical backup + WAL/PITR | pgBackRest | Preferred candidate for self-managed PostgreSQL when its repository, WAL archive and topology fit |
| Physical backup + WAL/PITR | Barman | Compare where centralized backup management and existing operational expertise favor it |
| Managed PostgreSQL | Provider-native backup/PITR | Prefer native supported mechanism if database is managed; validate export/restore constraints |
| Integrity | SHA-256 + independent artifact manifest | Retain; include backup, metadata and config digests |
| Recovery verification | SQL invariants + application smoke | Extend beyond table existence and one sentinel |

Do not install pgBackRest or Barman as a dependency in the CK-NEXUS application runtime. They belong in the backup/operations plane, behind explicit least-privilege credentials and deployment-specific adapters. Do not select a product before confirming the real database topology and recovery objectives.

## Proposed staged plan

| Stage | Deliverable | Exit criteria |
|---|---|---|
| 0 | Existing drill assessment | Current strengths, historical evidence and limitations documented (this PR) |
| 1 | Offline unit tests | Same-target, missing acknowledgement, host/port/database mismatch, checksum tamper, missing required tables, RTO breach |
| 2 | Synthetic integration matrix | Seed representative relational schema/data, sequences, indexes, constraints and app-level invariants; restore only to disposable local/CI DB |
| 3 | RPO/PITR design spike | Define timestamped write markers and measurable recovery-point age; test WAL/PITR only in isolated disposable topology |
| 4 | Backup-engine comparison | Compare pgBackRest/Barman/provider-native mechanism against documented topology, RPO/RTO, storage, restore time and operator skill |
| 5 | Staging drill | Separate explicit authorization, isolated target, scoped credentials, encrypted backup repository, alerting and complete raw evidence |
| 6 | Q13 gate evaluation | Re-run on exact release candidate; independent verification; no automatic promotion |

Stages 1–2 may use local disposable databases and synthetic data. Stages 3–5 require isolated infrastructure and separate authorization. No production database access, backup, restore, credential use or infrastructure mutation is authorized by this assessment.

## Required Q13 evidence bundle

- exact source commit SHA and Git tree SHA;
- deployment/runtime subject and configuration digest;
- database engine/version and client tool versions;
- sanitized source/target topology identities and proof of isolation;
- backup start/end timestamps, measured backup duration and recovery-point marker;
- backup file digest, metadata digest and independent checksum verification;
- WAL archive continuity and selected recovery target for PITR, where applicable;
- restore start/end timestamps and measured end-to-end recovery duration;
- schema, constraints, indexes, sequences, extensions and application invariant checks;
- post-restore application health/smoke result;
- RPO/RTO targets and measured values, with explicit pass/fail calculations;
- raw logs, artifact hashes, workflow run ID and independent verifier identity;
- cleanup confirmation for disposable resources.

A logical dump/restore PASS is a component result, not proof of PITR, scheduled-backup resilience, production recoverability or Q13 PASS. Q13 PASS applies only to complete evidence bound to the same exact release candidate. Production remains NO-GO until all Q10–Q16 gates pass on that candidate and owner authorization is separately recorded.

## Primary references

- PostgreSQL SQL dump: https://www.postgresql.org/docs/current/backup-dump.html
- PostgreSQL continuous archiving and PITR: https://www.postgresql.org/docs/current/continuous-archiving.html
- pgBackRest documentation: https://pgbackrest.org/user-guide.html
- Barman documentation: https://docs.pgbarman.org/

## Non-claims

This assessment does not claim PITR has been tested, that a physical backup engine is installed, that production topology is known, that production backups are protected, or that Q13 passes on current main. No database operation, runtime code, dependency, workflow, gate state, secret or infrastructure was changed.
