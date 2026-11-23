# Universal AI Operating Standard (UAOS) v1.0

Status: DESIGNED / DEVELOPMENT
Scope: model-agnostic, runtime-agnostic, tool-agnostic
Authority: Policy Kernel / authorized human governance
Canonical law: NO EVIDENCE → NO DONE

> Mainline integration baseline: post-security-remediation.

## 1. Purpose
One operating standard for GPT, OpenCode, Claude, OpenClaw, n8n, agents, runtimes, tools, and future systems. The required outcome and evidence quality stay fixed while multiple valid execution paths are allowed.

## 2. Core invariants
- DESIGNED ≠ IMPLEMENTED ≠ EXECUTED ≠ VERIFIED ≠ PRODUCTION.
- EXECUTED ≠ VERIFIED.
- TOOL FAILURE ≠ CAPABILITY FAILURE.
- METHOD FAILURE ≠ TASK FAILURE.
- ALTERNATIVE PATH ≠ STANDARD BYPASS.
- NO EVIDENCE → NO CLAIM.
- NO EXECUTION EVIDENCE → NO VERIFIED.
- NO VERIFIED → NO PASS.
- NO PASS → NO DONE.
- Production status requires production evidence.
- Models and agents propose; policy and authorization decide.
- Fail closed on missing identity, authority, scope, required evidence, or verification.

## 3. Standard lifecycle
HUMAN INTENT → IDENTIFY → CAPABILITY → POLICY → RISK VERDICT → LEASE / AUTHORIZATION → PLAN → PRIMARY PATH → ALTERNATIVE PATH if required → EXECUTION → VERIFICATION → EVIDENCE → CANONICAL STATUS

## 4. Failure-to-alternative rule
1. Capture the failure and preserve state.
2. Classify tool, environment, capability, authorization, data, or task failure.
3. Select the safest valid alternative that preserves the required outcome.
4. Apply the same or stronger evidence and verification requirements.
5. Execute only within authorized capability and risk scope.
6. Record lineage from the failed attempt to the alternative.
7. Verify independently.
8. Promote status only from evidence.
Repeated identical failures must trigger a method change or escalation rather than endless retries.

## 5. Evidence levels
E0 none; E1 design; E2 source/artifact; E3 execution; E4 independent verification; E5 release/candidate; E6 production.
A lower evidence level must never be silently promoted to a higher level.

## 6. Risk tiers
L0 informational/read-only; L1 development/local mutation; L2 internal execution; L3 important/shared mutation; L4 security/credential/external effect; L5 production/irreversible/high-impact.
Higher-risk actions require stronger authorization, isolation, evidence, and verification.

## 7. Alternative-path constraints
An alternative is valid only when capability is equivalent or explicitly approved, authorization remains valid, policy permits the target, risk is equal/lower or explicitly approved, evidence requirements are preserved/strengthened, independent verification remains possible, and provenance links the alternative to the failed attempt.

## 8. Deadlock prevention
BLOCK_PATH means the current route is blocked; it does not automatically mean the overall task is impossible. The controller must distinguish BLOCK_PATH from BLOCK_TASK and inspect registered alternatives when policy permits.
No alternative may override a hard policy prohibition.

## 9. Universal adapter minimum
Every connected AI/system should map: agent identity, model identity, capability, policy, risk verdict, authorization/lease, tool, target, runtime, execution ID, verifier, evidence reference, parent execution for delegated work, and final status.
Adapters translate native fields; they must never invent missing evidence.

## 10. Canonical statuses
DESIGNED, IMPLEMENTED, EXECUTED, VERIFIED, RELEASE_CANDIDATE, PRODUCTION, BLOCKED, FAILED, UNVERIFIED, NOT_APPLICABLE.
Use the strongest status directly supported by evidence.

## 11. External standards
External standards/frameworks are reference/crosswalk inputs unless independently implemented and verified. They do not automatically constitute CK-NEXUS compliance evidence.

## 12. Audit question
For every completed task, the system must answer: who did what, to what, using which capability and authorization, under which policy and risk decision, by which path, what failed, which alternative was used, how it was verified, and where the evidence is stored.

## 13. Completion, publication, and duplicate-work lock

For every authorized repository task, the agent MUST perform a prior-work lookup before acting: inspect the work ledger, current branch/commit, remote refs, existing CI results, and saved evidence. A new chat or session is not a reason to repeat completed work.

When a task is complete and its evidence is verified, the agent MUST, in the same work session:
1. Update the canonical work ledger with task ID/fingerprint, scope, exact source SHA, result, evidence paths and hashes, and timestamp.
2. Commit the completed change on its designated task branch.
3. Push that commit to the authorized GitHub remote immediately.
4. Read back the remote branch SHA and verify it exactly matches the local commit.
5. Mark the task `PUBLISHED` only after that remote-SHA check succeeds. If commit or push fails, record `BLOCKED` with the exact error; never claim publication.

A task with current, valid completion evidence is `REUSE — DO NOT REPEAT`. Do not rerun its scans, tests, edits, or documentation updates merely because the session changed. Reopen it only when a source/workflow/requirement change affects the result, evidence expires or is proven defective, or a new concrete failure is observed. Any justified rerun must state the changed input, why prior evidence is invalid, and the smallest affected check; link the new result to the original task instead of creating a duplicate.

This rule does not authorize merge, deployment, force-push, destructive changes, or permission changes. Those remain separate actions requiring their own authorization.

## 14. Promotion
DONE is derived from evidence, not asserted. Production remains prohibited unless production-specific gates are satisfied.