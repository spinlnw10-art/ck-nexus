# SonarCloud PR #392 triage — baseline head 6a960b9c

**Evidence source:** workflow run 45093845262, PR head 6a960b9c2a56a7ddeecc610144c6c3316860f9f1.
**Status:** Historical baseline captured before the remediation changes in this working candidate. Raw API responses are retained in evidence/sonarcloud/pr392-6a960b9c/.

## Quality gate result

- 43 issues total.
- 1 CRITICAL vulnerability and 3 MAJOR vulnerabilities.
- 4 MAJOR reliability bugs.
- 35 code smells; maintainability rating did not fail the gate.
- 0 security hotspots.
- Quality gate failed: new Security Rating D and new Reliability Rating C.

## Blocking findings and remediation applied

| Finding | Location | Remediation |
|---|---|---|
| S4830 — TLS peer verification not explicit | scripts/collect_dev_status.py | Use SERVER_AUTH context and explicitly set CERT_REQUIRED plus check_hostname=True. |
| S8541 / S8544 — unsafe package installation/build path | .github/workflows/q10-evidence-gate.yml | Pin uv to 0.12.4, install the wheel only, use the frozen lock, require binary dependencies, and do not build/install the repository project in the scanner environment. |
| Unhandled async scan promise | creator_app/web/signup.js:13 | Await autoScan and handle initialization rejection at the entry point. |
| Unhandled provider scan promise | creator_app/web/signup.js:192 | Await scanProviders inside the existing try/catch. |
| Clipboard promise has no rejection handler | creator_app/web/signup.js:270 | Add an explicit catch and user-visible copy failure state. |
| Signup initialization promise has no handler | creator_app/web/signup.js:277 | Attach an explicit catch to init. |

The remediation is in the current working candidate but has not yet been pushed or re-analyzed at the time this report was written. The next SonarCloud PR analysis must confirm the Security and Reliability ratings improve. Do not mark Sonar PASS based only on the source edits.

## Non-gating findings

The remaining 35 code smells are retained for later cleanup. They are not being bulk-edited because the recorded gate failure was specifically Security and Reliability, and broad cleanup would expand the change set without improving the immediate release decision.
