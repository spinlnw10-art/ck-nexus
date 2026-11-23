# CK-NEXUS Seller Checklist — Current Candidate

**Evidence date:** 2026-11-23  
**Decision: DEVELOPMENT / RELEASE CANDIDATE — NO-GO FOR PRODUCTION CLAIMS.**

This checklist supersedes the older checklist snapshot below. Historical checkmarks bound to runtime subject `96dcd0f0f93b1aaa69e88da30fedcce1b786b51b83f36b72baf7ac910d02b04f` and the old 55-distribution inventory are not acceptance evidence for the current candidate.

## Candidate identity

- [x] Repository: `spinlnw10-art/ck-nexus`.
- [x] Review path: PR #392, base `main`, head branch `ops/provider-free-go-clean`.
- [x] Latest candidate commit inspected for this update: `bdf224b66e2798920f9fc3b3ae872086bb737ee5`.
- [x] Canonical Q10–Q16 runtime manifest recorded in the current work ledger: `370f8a8f405e9b960e8b41722d0f61a4269237d137b94c014a1c2598e75e08de`.
- [ ] Final production commit/tag recorded.
- [ ] Final delivery archive SHA-256 recorded and independently verified.
- [ ] Final internal `SHA256SUMS` verified against the delivered archive.

## Current technical acceptance

| Item | Current status | Required next evidence |
|---|---|---|
| Frozen dependency install and CI | NOT VERIFIED for final candidate | Successful CI rerun on exact candidate commit |
| Provider-focused regression subset | 32/32 PASS (subset only) | Full required test suite on exact candidate |
| Q10 security/dependency assurance | NOT_VERIFIED; no-repeat lock until 2026-11-24 07:50 ICT | After lock expiry, exact-subject scan, finding dispositions, owner/independent review |
| Q11 live OpenAI Responses API | BLOCKED; previous probe returned 401 invalid_api_key | Valid owner-authorized project key and required sentinel smoke |
| Q12 delegated cgroup v2 | NOT_VERIFIED | Successful non-root delegated kernel-enforcement evidence |
| Q13 PostgreSQL backup/restore | PASS_CANDIDATE only | Exact-subject provenance and required review |
| Q14 observability/operator alerts | Prior candidate pass; rerun required under corrected installer policy | New exact-subject failure-injection and alert receipt evidence |
| Q15 clean-machine install | NOT_VERIFIED; prior attempt failed before tests | Successful fresh-host install and runtime smoke |
| Q16 production image | PASS_CANDIDATE only | Final combined-tree image checks after Q10–Q15 |
| Q16 runtime licenses | PASS_CANDIDATE only | Inventory bound to the final delivery subject |

Candidate evidence must not be promoted to production PASS. Evidence from a different source SHA or runtime manifest cannot be combined to close a gate.

## Security and credentials

- [x] Repository policy requires credentials to remain out of source, reports, and chat.
- [x] Provider routing candidate requires explicit opt-in for hosted/billable providers.
- [ ] Q10 whole security gate and independent review accepted.
- [ ] Q11 buyer/seller-authorized live-provider smoke passed.
- [ ] Q12 delegated cgroup v2 kernel enforcement verified.
- [ ] Authentication, session ownership, and tenant isolation independently tested for the delivery candidate.
- [ ] Final repository-wide security alerts reviewed with exact alert state and affected branch.

## Commercial package

- [ ] Select assignment vs perpetual source license in an executed agreement.
- [ ] Identify seller and buyer legal entities.
- [ ] State price, currency, taxes, and payment milestones.
- [ ] State delivery format, acceptance period, rejection/remediation procedure, and refund terms.
- [ ] State support/warranty period, exclusions, and update policy.
- [ ] Define delivery channel and buyer backup responsibility.
- [ ] Complete legal review where required.

## Final decision

**Current: source-code development/release candidate only; production readiness is NOT VERIFIED.**

Do not label the artifact Production Ready or SELLABLE FOR PRODUCTION until all mandatory gates pass against one exact release subject, independent reviews are complete, final package checks pass, the PR is reviewed and merged through the approved process, and immutable release/archive hashes are recorded.

See [Buyer Technical Due-Diligence Brief](BUYER_TECHNICAL_DUE_DILIGENCE.md), [Release Status](../RELEASE_STATUS.md), and [Q10–Q16 Closure Contract](Q10_Q16_CLOSURE_CONTRACT.md).
