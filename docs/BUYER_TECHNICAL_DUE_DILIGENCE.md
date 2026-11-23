# CK-NEXUS — Buyer Technical Due-Diligence Brief

**Evidence date:** 2026-11-23  
**Repository:** https://github.com/spinlnw10-art/ck-nexus  
**Review basis:** repository source, current handoff/work ledger, release contract, and linked test/evidence records. This is an internal evidence summary, not vendor certification, an independent audit, or a customer reference.

## Executive decision

**Development / Release Candidate — NO-GO for Production.**

The repository contains a substantial self-hosted AI orchestration and governed-execution codebase, user-facing workspace, provider/integration adapters, operational workflows, and release evidence. The repository does not establish production readiness, customer traction, revenue, a successful clean-machine installation of the current candidate, or a completed live-provider test.

PR #392 is the current review path into `main`. It remains open and blocked pending review. Do not treat this brief, a passing subset of CI, or candidate gate evidence as approval to merge, publish, deploy, or sell the system as production-ready.

## 1. Product and intended users

CK-NEXUS is described as one self-hosted platform for AI orchestration, governed tool execution, persistent knowledge, and evidence-based operations. Agnes is the orchestration/execution layer; Creator Workspace is the user-facing interface; `/development` is an internal evidence dashboard. They are components of one platform, not separate products.

The likely user groups inferred from the code and documentation are:
- developers and technical operators integrating AI models and tools;
- creators or teams building workflows with AI assistance;
- organizations that need approval, permission, audit, and evidence controls around agent actions.

These are intended audiences inferred from the repository. The repository does not prove market demand, paying customers, active-user counts, retention, or revenue.

## 2. Capabilities and evidence boundaries

| Area | What repository evidence supports | What it does not prove |
|---|---|---|
| Web/API and Creator Workspace | FastAPI application, documented local entry point, health/status/OpenAPI interfaces | Current-candidate clean install or public service availability |
| Agnes and Development Council | Orchestration/advisory roles, API contract, Mock Mode design | That advisory agents can independently perform production mutations |
| Governance and execution | Permission, approval, sandbox, verification, and evidence architecture documented in code/contracts | Complete production enforcement across every execution path |
| Memory and knowledge | Session/memory and local persistence paths are documented | Production durability, backup recovery, or tenant isolation |
| Provider routing | Provider adapters and opt-in safeguards; regression tests recorded as 32/32 for the named provider test subset | Free quota, successful live inference, or Q11 completion |
| Integrations | Adapters documented for GitHub, Slack, Drive, Gmail, OpenAI and database services | That every integration is configured, connected, or verified in the buyer's environment |
| Operations | CI workflows, release gates, evidence scripts and deployment definitions | Production deployment, independent certification, or operational SLA |

The Development Council is explicitly advisory. It must not be represented as an autonomous production operator or authority to mutate external systems. Integrations are adapters; an adapter in source is not proof of a live connection.

## 3. Demo and installation

The README documents a local Python quick start using Python 3.11+ and:

```bash
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install -e ".[dev]"
python3 -m creator_app.unified
```

The documented local address is `http://127.0.0.1:8000`. The acceptance checklist records Demo Mode without an API key and safe failure when a live key is missing.

Limits:
- The repository does not provide evidence in this review of a recorded end-to-end demonstration on the exact delivery commit.
- The live OpenAI Responses API test remains blocked by an invalid credential (HTTP 401 in the work ledger); no successful live generation is established.
- The historical `docs/TEST_REPORT.md` is for v0.2.0 dated 2026-08-05 and reports 26 tests. It is not the current candidate's full test result.
- The latest observed CI run for commit `bdf224b66e2798920f9fc3b3ae872086bb737ee5` had the `test` workflow fail during import/collection; other observed workflows in that batch passed. A correction was recorded in the work ledger, but a passing rerun is required before claiming the failure is resolved.

A buyer should require a live demonstration against the exact proposed delivery commit and independently perform the installation on a clean supported machine.

## 4. Security and release readiness

The normative requirements are in [Q10–Q16 Closure Contract](Q10_Q16_CLOSURE_CONTRACT.md). Current work-ledger status:

| Gate | Evidence status | Buyer interpretation |
|---|---|---|
| Q10 Security/dependencies | NOT_VERIFIED; no-repeat lock remains until 2026-11-24 07:50 ICT | Prior scanner output is not whole-gate closure or independent sign-off |
| Q11 Live OpenAI | BLOCKED; previous Responses API probe returned 401 invalid_api_key | Live-provider acceptance has not passed |
| Q12 Delegated cgroup v2 | NOT_VERIFIED; prior setup attempt failed; revised systemd delegation method awaits successful run | Kernel enforcement is not established |
| Q13 PostgreSQL recovery | PASS_CANDIDATE only | Not production promotion evidence |
| Q14 Observability | Prior candidate pass requires a rerun under the corrected installer policy | Not accepted as final current release evidence |
| Q15 Clean-machine install | NOT_VERIFIED; prior attempt failed before test execution | No clean-machine acceptance yet |
| Q16 Image/licenses | PASS_CANDIDATE only for prior candidate evidence | Not final release convergence or production approval |

The canonical manifest is intended to bind Q10–Q16 evidence to one runtime subject. Evidence from a different manifest or source subject must not be combined to claim closure.

The no-repeat lock is an execution restriction: do not rerun Q10/Bandit/secret scans before the stated expiry. Q12–Q16 must be run only through their approved workflows and evidence rules. Q11 requires a valid owner-authorized OpenAI project credential; do not share the secret in chat or source control.

## 5. CI, code quality, and known limitations

- Provider-focused regression subset: 32 tests passed, as recorded in the work ledger. This is not the full suite.
- Latest observed commit CI batch: preflight, attack regression, and universal-system workflows passed; the main test workflow failed during import/collection. The corrective change still needs a successful rerun.
- SonarCloud issue export/triage is still required; an aggregate Quality Gate result alone does not close every issue.
- Historical Bandit findings and their AI-assisted source-context review are not independent human sign-off.
- The repository contains multiple dated reports and snapshots. Use the newest handoff/work-ledger entries and exact subject hashes; do not combine old reports into one current pass claim.

## 6. Deployment, customers, and costs

The README documents a local runtime. Production guidance references Linux, Docker/Compose, persistent storage, and external provider credentials. The current evidence set does not establish that the exact candidate has been deployed and operated as a production service.

No verified repository evidence was identified for:
- paying customers, active-user counts, revenue, or customer case studies;
- a production uptime/SLA history;
- a final monthly hosting/provider cost;
- a final executed commercial license, price, warranty, refund terms, or support agreement.

Costs depend on the buyer's hosting, database, storage, email/OAuth, and model-provider choices. A provider key does not prove free quota. Hosted calls are guarded by explicit opt-in in the documented provider candidate, but the buyer must verify billing and quota in their own provider account.

## 7. Required buyer acceptance before payment or production use

1. Identify the exact source commit, tree, runtime manifest, and delivered archive SHA-256.
2. Perform a clean-machine installation on the buyer's target OS.
3. Demonstrate Mock Mode and live mode separately; label which external services are actually used.
4. Verify authentication, session ownership, tenant isolation, and permissions with separate test accounts.
5. Review Q10 findings and obtain the required independent security sign-off.
6. Close Q11–Q16 against the same release subject under the closure contract.
7. Agree in a signed transaction document on license type, price, taxes, delivery, acceptance period, support, warranty, updates, and refund/remediation terms.

## Source documents

- [README / quick start](../README.md)
- [Release Status](../RELEASE_STATUS.md)
- [AI Handoff / Current Truth](ops/AI_HANDOFF_CURRENT_TRUTH.md)
- [CK-NEXUS Work Ledger](ops/CKNEXUS_WORK_LEDGER.md)
- [Q10–Q16 Closure Contract](Q10_Q16_CLOSURE_CONTRACT.md)
- [Development Council](DEVELOPMENT_COUNCIL.md)
- [Integration Hub](INTEGRATION_HUB.md)
- [MVP Acceptance Criteria](ACCEPTANCE_CRITERIA.md)
- [Historical v0.2.0 Test Report](TEST_REPORT.md)
- [Seller Checklist](SELLER_CHECKLIST.md)
