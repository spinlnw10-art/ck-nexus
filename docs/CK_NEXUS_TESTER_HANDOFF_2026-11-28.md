# CK-NEXUS tester handoff — 2026-11-28

## Candidate under review

- Repository: [spinlnw10-art/ck-nexus](https://github.com/spinlnw10-art/ck-nexus)
- Pull request: [#421 — GitLab Duo Dispatcher V1](https://github.com/spinlnw10-art/ck-nexus/pull/421)
- Branch: `feat/gitlab-duo-dispatcher-20261126`
- Evidence subject at the time of this snapshot: `86cd16b3c910dc71d19bbdcc954a4cbeae2a619b`
- Base: `main` at `944d7cb70a5d59d53c8fb379752bbee2085f7c8c`

This is a tester handoff for the code in the pull request, not a release or Production approval. Test the PR branch in an isolated, non-production environment. Do not merge or deploy based only on this document.

## What can be tested

The PR adds the GitLab Duo dispatcher adapter, Core-authority integration, Credential Broker binding, SQLite dispatch ledger, protected-branch checks, and MCP status/start/status-poll tool registration. The adapter is deliberately fail-closed. The MCP tools must not perform a live dispatch unless CK-NEXUS Core supplies the trusted authority, verified caller identity, task-bound approval verifier, broker-backed credential provider, project configuration, and explicit workflow/privilege allowlists.

For safe validation, run the local unit tests and inspect redacted status/tool registration. Do not attempt a live GitLab dispatch with guessed IDs, a personal token, or an unapproved identity.

## Isolated setup and focused tests

Requirements: Python 3.11+ and the repository development dependencies.

```bash
git fetch origin pull/421/head:refs/remotes/pr/421
git switch --detach refs/remotes/pr/421
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install -e ".[dev]"
python3 -m pytest -q tests/agnes/test_gitlab_duo_dispatcher.py tests/agnes/test_gitlab_duo_mcp.py
```

Run the full repository test and security workflows using the documented project/CI procedures before proposing a merge. Keep all credentials in the approved secret/credential store; never paste them into shell arguments, source, issues, or logs.

## Evidence snapshot for the exact subject above

GitHub check-runs returned 13 entries:

- PASS: `test`, `preflight`, `attack-regression`, `universal-system`, both `verify` checks, `Block deleted files`, `CodeQL`, and the three `Analyze` language jobs.
- BLOCKED/UNRESOLVED: `SonarCloud Code Analysis` completed with conclusion `cancelled`; its output title says the last analysis failed, but GitHub reports zero annotations. This does not identify a source line or a confirmed code defect. Inspect the [SonarCloud PR analysis](https://sonarcloud.io/dashboard?id=spinlnw10-art_ck-nexus&pullRequest=421) and rerun analysis after the external integration/configuration issue is understood. Do not suppress or bypass this check.
- SKIPPED: CodeRabbit reports that manual review is required for this OSS repository.

These results apply only to the exact commit above. Any new commit requires fresh checks. A passing CI subset is not an approval to merge.

## Activation prerequisites — not yet satisfied

The adapter is not a live, production-connected dispatcher. Before a controlled non-production canary, CK-NEXUS Core must provide and approve the actual policy grant, dedicated service identity, verified caller, task-bound approval verifier, Credential Broker credential binding, target project, workflow-definition allowlist, and discovered numeric privilege allowlist. The target GitLab project previously inspected was empty, so its workflow and privilege IDs were not available to validate. Keep external mutation authorization disabled until these prerequisites and independent review are complete.

## Current release decision

**NO-GO for Production and live dispatch.** No merge, deployment, protected-branch change, scanner bypass, or live GitLab Duo dispatch is authorized by this handoff.
