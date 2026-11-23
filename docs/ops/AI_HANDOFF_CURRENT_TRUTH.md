# CK-NEXUS — AI Handoff / Current Truth

**Purpose:** First file every incoming AI/agent must read. It prevents duplicate work, false completion claims, stale SHA use, and confusion between similarly named documents.

**Last verified:** 2026-11-23 (ICT)  
**Repository:** spinlnw10-art/ck-nexus  
**Production decision:** **NO-GO**  
**Canonical task ledger:** [CKNEXUS_WORK_LEDGER.md](CKNEXUS_WORK_LEDGER.md)

## 1. Read this before doing anything

1. Read this handoff.
2. Read CKNEXUS_WORK_LEDGER.md for completed tasks, evidence, locks, and next actions.
3. Read only the current top snapshot of RELEASE_STATUS.md for release status.
4. Read Q10_Q16_CLOSURE_CONTRACT.md for what each production gate requires.
5. Inspect current GitHub refs and evidence only when the task requires a fresh state check.

Do not start from chat history, old reports, README text, or a remembered SHA. They are not the source of task state.

## 2. Exact repository identity — do not mix these SHAs

| Identity | Exact value | Meaning |
|---|---|---|
| PR | https://github.com/spinlnw10-art/ck-nexus/pull/392 | Current review path into main |
| Moving PR head | Must be read live from GitHub | Never treat a SHA stored in this document as the current branch head |
| Previous observed PR head | 0944ffd179e3789838185412dbcf2944caafb7e2 | Head before the handoff document was pushed |
| Code candidate SHA | efbb2ee157fcfdedfde054508fafaf21cbaf88fa | Application source subject for the current Q10 report |
| Main branch SHA | 944d7cb70a5d59d53c8fb379752bbee2085f7c8c | Main has not received PR #392 |
| Remote branches | fix/q10-attachment-hardening-20261123, ops/provider-free-go-clean | Both were verified equal before the handoff update; query live refs for the current head. |

Commits after the code candidate through the handoff update are documentation-only. Verified changed files between efbb2ee... and 0944ffd...:
- README.md
- RELEASE_STATUS.md
- docs/UNIVERSAL_AI_OPERATING_STANDARD_V1.md
- docs/ops/CKNEXUS_WORK_LEDGER.md
- docs/ops/AI_HANDOFF_CURRENT_TRUTH.md

Therefore: **Q10 report source SHA remains efbb2ee, while current PR head is 0944ffd.** Never rewrite the report's source SHA to the PR head. No application source change is represented by these documentation commits.

## 3. Current GitHub state (verified 2026-11-23)

- PR #392: **OPEN**
- Merge state: **BLOCKED**
- Review decision: **REVIEW_REQUIRED**
- Latest PR head: read live with gh pr view 392; do not use a stored SHA as current
- The complete check set last observed on the previous head 0944ffd...:
  - PASS: CodeQL, Analyze Actions, Analyze JavaScript/TypeScript, Analyze Python, attack-regression, preflight, test, universal-system
  - FAIL: SonarCloud Code Analysis
  - SKIPPING: CodeRabbit
- No merge and no deployment occurred.
- README on the PR branch is not the public main landing-page README until the PR is merged.

## 4. Verified completed work — do not redo

| Task / artifact | What it means | Evidence / status |
|---|---|---|
| 288ff29b59b6740e2c9245521ef4d0f226a54286 | Hardened Office-archive attachment scanning | Code commit pushed to PR branches |
| efbb2ee157fcfdedfde054508fafaf21cbaf88fa | Removed user-controlled security-evidence output path | Code commit pushed; Q10 scan subject |
| Q10 run 45088376317 | Layered open-source scanner execution for code candidate efbb2ee... | Scanner PASS; report SHA-256 71dab5d573b4f2bf1bf0e31cf794c13b0be17c08e8f317b580b9f8bb4626b192 |
| Q10 report | Dependency audit 0 vulnerabilities; Bandit High 0 / Medium 0 / Low 541; secret scan PASS (872 tracked files); attack regression 22/22 | Scanner PASS only; independent security review still REQUIRED; production_promotion_allowed=false |
| Provider-focused tests | Prior history reports 37/37 PASS and commits 8eb52e86, 177b35e2160e9e8fd3559ea323db4b725471bd7f | Historical outcome; exact test subject must be recovered before treating as current release evidence |
| README / Release Status / Work Ledger | Repository status and work-record documentation updated | Pushed on PR branches; do not repeat without a factual change |
| Complete-publish-no-repeat policy | Requires prior-work lookup, immediate commit/push, remote SHA read-back, and no duplicate work | Commit 0944ffd179e3789838185412dbcf2944caafb7e2; both remote branch refs verified equal |

**Important corrections:**
- ChatGPT ↔ Fireflies account/meeting reads were verified. This does not mean Fireflies is integrated with CK-NEXUS.
- Provider tests 37/37 were reported in history, but without the exact tested SHA in the available record they are not proof of current production readiness.
- A scanner PASS is not a security-review PASS, whole Q10 closure, PR merge, deployment, or Production GO.

## 5. What is still open — do not label as done

1. Q10 independent security review and finding dispositions. Review the saved Bandit JSON; 107 LOW findings are outside test paths. Do not rerun Bandit just to inspect them.
2. SonarCloud FAIL: inspect its actual issues and separate actionable defects from quality-only findings.
3. Issue #66: attachment acceptance criteria are not verified as fully closed.
4. Q11–Q16: exact-current-candidate runtime/deployment evidence is not established.
5. PR #392: review is required; merge is not authorized by this handoff.
6. Production verification and deployment have not occurred.

Follow the exact gate requirements in Q10_Q16_CLOSURE_CONTRACT.md. Never infer a gate PASS from a file existing, a test subset, a green CI check, or an older SHA.

## 6. File map — which document means what

| File | Authority / meaning | How to use it |
|---|---|---|
| docs/ops/AI_HANDOFF_CURRENT_TRUTH.md | **AI session handoff and current identity map** | Read first; explains truth, boundaries, and document roles |
| docs/ops/CKNEXUS_WORK_LEDGER.md | **Single task-state ledger** | Read before every action; record outcomes, hashes, locks, and next steps |
| RELEASE_STATUS.md | Current release decision plus retained dated history | Trust only its first/current snapshot for current state; lower sections are historical |
| docs/Q10_Q16_CLOSURE_CONTRACT.md | Normative definition of Q10–Q16 requirements | Defines what evidence each gate needs; it is not a live status report |
| README.md | Product overview and entry-point guide | Not security evidence and not release approval |
| docs/UNIVERSAL_AI_OPERATING_STANDARD_V1.md | Cross-agent operating rules | Mandatory execution discipline; does not replace the task ledger |
| docs/ACCEPTANCE_CRITERIA.md | MVP functional/security/commercial acceptance checklist | Not the Q10–Q16 Production closure checklist |
| docs/PRODUCTION_CLOSURE_Q10_Q12_RUNBOOK.md | Runbook bound to older frozen subject ad2fac7... / runtime subject 772662ac... | Historical/frozen instructions only; do not run against current candidate without deliberate re-baselining |
| evidence/q10/Q10_STATUS_2026-10-04.md | Dated Q10 historical status | Historical evidence only; not current candidate status |
| evidence/q10/Q10_STANDARDIZED_CLOSURE_FRAMEWORK_2026-10-04.md | Dated Q10 framework/history | Historical reference; not a current pass certificate |
| R-series / Agnes phase validation reports | Individual implementation-phase records | Useful technical history; not independent Production certification |

### Known sources of confusion — keep, do not silently delete

- RELEASE_STATUS.md intentionally contains old snapshots below the current section. Older SHA values in those dated sections are historical, not competing current SHAs.
- docs/PRODUCTION_CLOSURE_Q10_Q12_RUNBOOK.md contains frozen hashes from an older closure line. It must not be mistaken for the current candidate runbook.
- docs/ACCEPTANCE_CRITERIA.md describes MVP acceptance; its checkboxes do not close Q10–Q16.
- Dated evidence/q10/*2026-10-04* files are preserved history, not live status.
- Multiple architecture, R-series, and Agnes documents describe different phases or views of one platform. Do not treat each as a separate runtime or a new implementation task.

These files are retained for traceability. Do not delete, rename, or mass-edit historical evidence just to make the repository look simpler. If a historical document must be changed, add an explicit superseded/historical notice and preserve its hashes and provenance.

## 7. Mandatory no-repeat execution protocol

For every proposed task:
1. Search this handoff, the work ledger, Git history, remote refs, saved evidence, and existing CI results for the same task fingerprint.
2. If valid evidence already exists for the same subject, mark **REUSE — DO NOT REPEAT**.
3. If new evidence invalidates old evidence, state exactly what changed and rerun only the smallest affected check.
4. When an authorized task is actually complete: update the ledger, commit, push to the designated branch, read back the remote SHA, and verify it equals the local SHA in the same work session.
5. Status words have fixed meanings: DONE = outcome verified; PUBLISHED = pushed and remote SHA read back; BLOCKED = action or verification failed.
6. Never merge, deploy, force-push, delete evidence, or change permissions without separate explicit authorization.

**Next work order:** review SonarCloud issues and the saved 107 non-test Bandit findings; verify Issue #66 acceptance criteria; then close only the missing exact-subject Q11–Q16 evidence. Do not repeat completed Q10 scanner, dependency, secret, attack-regression, or test runs while their evidence remains valid.
