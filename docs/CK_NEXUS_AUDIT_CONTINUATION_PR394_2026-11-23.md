# CK-NEXUS Audit Continuation — PR #394 — 2026-11-23

Status: read-only source/dependency review plus documentation-only audit update. No runtime files deleted or modified. No cleanup script, VPS command, merge, or deployment was executed.

## 1. PR state and validation at the inspected head

- PR: #394, Open, Draft, not merged.
- Head: `b557689c6605d00aba5e379a712a47e29207bdcf`.
- Base: `944d7cb70a5d59d53c8fb379752bbee2085f7c8c`.
- Branch comparison: 6 commits ahead, 0 behind.
- Changed tree: five documentation files added; 517 insertions, 0 deletions.
- The PR description still contains an earlier 5-commit / 485-insertion summary. That summary is stale and should be refreshed before review.

### Check runs

GitHub returned eight check runs for the exact head SHA; all eight were completed with conclusion `success`:
- test
- preflight
- attack-regression
- CodeQL
- SonarCloud Code Analysis
- Analyze (python)
- Analyze (javascript-typescript)
- Analyze (actions)

SonarCloud reported Quality Gate passed, 0 new issues, 0 accepted issues and 0 security hotspots. This is CI evidence for this documentation-only PR head only. It is not Q10–Q16 closure, production certification, or deployment approval.

## 2. SQL migration duplicate group — dependency findings

The three files remain byte-identical (2,484 bytes; Git blob SHA `a7c91587f2d3d461ae845a041cec21a59cb16789`):

1. `migrations/001_email_journal.sql`
2. `migrations/postgresql/001_email_gateway.sql`
3. `services/email_gateway/migrations/postgresql.sql`

Evidence found:
- `docker-compose.p0.yml` mounts `migrations/postgresql` and invokes `/migrations/001_email_gateway.sql`; this makes path 2 an active deployment contract for the P0 migration job.
- `services/email_gateway/repository.py` documents path 2 as the production PostgreSQL schema contract.
- `SHA256SUMS` records the same digest for paths 1, 2 and 3. Therefore the checksum manifest also binds all three path names into the integrity inventory.
- A GitHub code search for the exact basename returned path 2's Compose and Python references plus the checksum manifest. Search is not exhaustive for dynamically assembled paths, shell variables, packaging globs or external deployment repositories.

Disposition:
- KEEP path 2 as the canonical operational path for now.
- KEEP paths 1 and 3 until a complete checkout-based search establishes whether external tooling, package manifests, historical installers or consumers depend on them.
- Do not delete or rename any copy in this audit.
- Any later consolidation must update `SHA256SUMS`, migration packaging and tests atomically, and prove that the P0 migration job still consumes the intended file.

## 3. n8n — stronger evidence of retained operational coupling

The policy in `docs/INTEGRATION_HUB.md` says n8n was removed from the active runtime in R14 and no current compose service, API integration, P0 gate or deployment script may start or require it.

However, the default-branch source still contains concrete operational coupling, not only historical documents:
- Python modules under `creator_app/n8n_intelligence/` implement normalized execution events, read-only API client, bounded collection, analysis, task bridging, durable event storage, proactive task seeding and bounded auto-developer/AutoGitOps behavior.
- VPS entrypoints `ops/vps/scripts/cknexus_n8n_intelligence.py`, `cknexus_n8n_proactive.py`, `cknexus_n8n_auto_developer.py` and `cknexus_n8n_auto_gitops.py` import those modules.
- Matching systemd service/timer units invoke several of those entrypoints. The workflow UI systemd unit invokes an external path `/usr/local/libexec/cknexus_n8n_workflows_ui.py`.
- `config/operations_tool_registry.json` still registers an `n8n_health_report` capability with a source under `/opt/cknexus/storage/`.
- `ops/vps/systemd/cknexus-n8n-backup.service` and its timer refer to a separate backup script under `/opt/cknexus/storage/`.
- Tests explicitly cover the n8n intelligence package, CLI wrappers, workflow gateway and UI contract.
- `SHA256SUMS` contains entries for the n8n VPS scripts and evidence exporter.

Interpretation:
- The repository has a genuine policy-to-tree inconsistency. Some components may be retired, while others may still be installed or registered externally.
- The checked-in systemd units and registry entries prove that the repository describes installable/registered behavior; they do not prove those units are enabled or those files are present on the live VPS.
- The external gateway, backup and health-report paths cannot be validated from this repository alone.

Disposition:
- Do not bulk-delete the n8n package, scripts, systemd units, tests, registry entries or UI.
- First collect a read-only host inventory (unit files, enabled/active state, timers, installed external scripts, process list and n8n endpoint availability) without reading or printing API keys.
- Then decide whether to preserve a minimal compatibility adapter, migrate functionality behind the CK-NEXUS capability layer, or archive a fully retired subsystem. Update policy, registry, installer, tests, checksum manifest and rollback plan together.

## 4. Next audit actions

1. Finish a complete path/reference scan for the three SQL migration copies, including packaging, workflow YAML, shell scripts and deployment manifests.
2. Inventory every file in `ops/vps/scripts/` and classify its filesystem, service, Docker, database, credential and network effects. Static inspection only.
3. Resolve n8n runtime truth with a read-only VPS inventory before removing any n8n component.
4. Build an ACTIVE / HISTORICAL / EVIDENCE-IMMUTABLE / UNVERIFIED documentation index with source commit and superseding-document links.
5. Obtain exact tracked file and line counts from a checkout at the stated commit; do not infer line counts from language byte statistics.

## 5. Safety decision

No file is approved for deletion by this continuation. The apparent duplicates are still referenced by deployment contracts, checksum inventory, runtime tests or external host paths. The next safe reduction should be a reviewed deprecation/migration PR with tests and rollback evidence, not an immediate deletion.

Production remains NO-GO until exact-candidate Q10–Q16 gates pass.


## 6. VPS script inventory — first static pass

A recursive Git tree at base commit `944d7cb70a5d59d53c8fb379752bbee2085f7c8c` returned **46 tracked files** under `ops/vps/scripts/`. The tree response was not truncated. This is an inventory of repository files, not a statement about what is installed on any VPS.

Static inspection has covered a subset of the 46 scripts so far. Important findings:

| Script | Observed behavior from source | Risk / disposition |
|---|---|---|
| `ck-cleanup.sh` | Removes named files in `/root`, matching `nano.*.save`, empty top-level directories and `/tmp/{sbx,q10,codex,check}-*` | Destructive and pattern-based; do not run without target preview and owner confirmation |
| `ck-v9.sh` | Removes matching temporary directories and issues a remote Sandbox CLI delete for a specific sandbox ID | High risk: remote resource deletion; preserve as historical until ownership and sandbox state are verified |
| `ck-q16.sh` | Contains `rm -rf ~/work/ck-nexus`, then performs Docker build/test and writes a checksum manifest | High risk: deletes a named working clone; do not run on a host that may hold unique work |
| `ck-q11q16.sh` | Installs PostgreSQL client packages, creates/uses a protected environment file, makes HTTP requests and writes `SHA256SUMS` | Mutating setup/verification script, not a read-only audit |
| `ck-push.sh` | Executes `git push origin main` | Release-affecting; do not run under this audit authorization |
| `cknexus-final-cleanup.sh` | Deletes old temp files, Python caches/bytecode and a selected temporary clone; vacuums journal; runs `docker system prune -f` | High risk to rollback caches/images and audit history; do not run |
| `cknexus-safe-cleanup.sh` | Cleans apt/npm caches, deletes temp files older than seven days and Mesa shader cache, vacuums journal | Destructive despite “safe” name; requires per-target preview and log-retention decision |
| `quick-reclaim.sh` | Cleans uv cache, apt cache, vacuums journal, removes selected Docker images and can recursively delete sandbox directories older than three days after prompt | High risk: sandbox state and rollback images may be lost |
| `reclaim2.sh` | Can purge Google Cloud CLI packages and run autoremove | Can remove operational tooling; require explicit package-ownership review |
| `cknexus-reboot-cycle.sh` | Captures n8n DB/service and Docker state around a reboot; probes n8n and Docker | Mutates host by rebooting; also demonstrates retained n8n operational assumptions |
| `cknexus-rm-audit.sh`, `cknexus-disk-audit.sh`, `cknexus-cleanup-target-check.sh` | Primarily inspect files, large objects, Docker usage, running services and cleanup candidates | Candidate read-only audit tools; still require full review before execution because shell side effects and external commands must be checked |
| `cknexus-q11-rootcause.sh` | Creates protected temporary probe/API/output files, calls HTTP endpoints, then removes temporary files | Diagnostic with temporary filesystem writes/deletes; not strictly read-only |
| `cknexus-postboot-verify.sh` | Checks n8n, Docker and reboot state, captures service/database state | Writes recovery-capture files; not strictly read-only |

Other scripts in the 46-file inventory include Q10/Q11/Q16 test/signoff/handover helpers, GitHub helpers, setup scripts, n8n wrappers, model/API probes and Pangolin setup. Their names alone are not enough to classify them.

### Immediate controls
- Do not run any script whose name contains cleanup, reclaim, fix, push, reboot, setup, Q10/Q16 or signoff until its full source and exact target host/state are reviewed.
- The word “safe” in a script name is not a safety guarantee.
- No script has been executed in this audit.
- No host service state, package inventory, sandbox ownership, Docker image usage or backup status has been verified live.
- The next pass must inspect the remaining scripts and build a command-level capability matrix, then separate genuinely read-only probes from scripts with filesystem, package, service, network, Docker, Git or reboot effects.
