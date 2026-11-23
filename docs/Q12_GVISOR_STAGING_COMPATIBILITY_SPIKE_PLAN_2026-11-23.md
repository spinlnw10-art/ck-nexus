# Q12 gVisor Staging Compatibility Spike — Test Plan

Date: 2026-11-23
Status: PROPOSED — requires dedicated staging host and separate authorization
Related assessment: `docs/Q12_GVISOR_RUNTIME_ISOLATION_ASSESSMENT_2026-11-23.md`

## Purpose

Prove whether the existing CK-NEXUS development adapter can run under gVisor without weakening any existing sandbox boundary. This is a compatibility and defense-in-depth experiment. It is not a replacement for the canonical Q12 delegated cgroup v2 gate.

## Preconditions (all mandatory)

- Dedicated Linux staging runner is online and connected; record runner name, ID, labels, architecture, kernel, OS image and non-root service identity.
- Runner is isolated from production data and has no production credentials.
- Owner explicitly approves staging installation/configuration of gVisor and Docker runtime registration.
- Exact gVisor release, package/binary checksums, signature/provenance and sidecar layout are verified before installation.
- Existing Docker/Podman runtime remains available and unchanged as baseline.
- Exact CK-NEXUS source commit and tree, adapter image digest, plan/request digest and policy version are frozen.
- The canonical delegated cgroup v2 preflight succeeds as the non-root service identity.
- Network egress is blocked outside the test harness; no external write capability is present.

If any precondition fails, mark the spike BLOCKED and do not install or alter the host.

## Experiment design

Use one synthetic, non-sensitive adapter image and a harmless task in a disposable worktree. Run the same immutable image and task twice on the same staging host:

A. Existing approved default runtime (baseline).
B. gVisor `runsc` runtime (candidate).

Do not change the task, image digest, source SHA/tree, resource limits, or policy between runs. Record each run separately and correlate both to the same frozen experiment manifest.

## Required observations

| ID | Test | Expected result | Evidence |
|---|---|---|---|
| Q12-GV-01 | Runtime identity | Candidate reports actual `runsc` binary/version; not merely requested runtime name | Runtime inspection output + hash |
| Q12-GV-02 | OCI lifecycle | Create/start/exec/stop/delete all succeed; cleanup leaves no sandbox | Raw runtime logs and post-run inventory |
| Q12-GV-03 | Non-root | Workload UID/GID equals approved non-root identity | In-sandbox identity output |
| Q12-GV-04 | Network denial | No external DNS/TCP/UDP reachability; loopback-only behavior is documented | Negative connection tests and host-side capture |
| Q12-GV-05 | Read-only root | Writes outside approved workspace/tmpfs fail | Negative filesystem tests |
| Q12-GV-06 | Workspace boundary | Only the exact disposable worktree is writable; no host root or Docker socket mount | Mount inventory + negative path tests |
| Q12-GV-07 | Capabilities/privilege | No added Linux capabilities; privilege escalation attempts fail | `/proc` capability observations and negative tests |
| Q12-GV-08 | Host cgroup v2 | Child PID is attached to delegated child cgroup; exact CPU/memory/PID ceilings observed | Canonical Q12 gate JSON + cgroup files |
| Q12-GV-09 | Resource exhaustion | CPU, memory, PID and timeout limits stop the workload predictably | Bounded negative-test logs |
| Q12-GV-10 | Patch-only | Patch is bounded and returned as unverified; no apply/commit/push | Patch digest + repository status |
| Q12-GV-11 | Cleanup | Worktree, container, cgroup and temporary resources are removed after pass/fail/timeout | Before/after resource inventory |
| Q12-GV-12 | Fail-closed | Missing runtime, wrong version, digest mismatch or failed health check blocks execution; no fallback | Unit/negative-test output |
| Q12-GV-13 | Compatibility | Python/Node/subprocess/signal/temp-file/bind-mount behavior used by adapter works | Deterministic test results |
| Q12-GV-14 | Performance | Startup, wall time, CPU and I/O compared with baseline; no arbitrary threshold invented | Raw benchmark samples + methodology |

## Security-specific negative tests

The candidate must fail closed for:
- attempt to enable network or host networking;
- attempt to mount Docker socket, host root, or undeclared paths;
- privileged container or added capabilities;
- root UID/GID execution;
- unpinned or altered adapter image;
- runtime binary missing or changed after preflight;
- child process escaping the delegated cgroup;
- attempts to change `cpu.max`, `memory.max`, or `pids.max` from inside the workload;
- timeout, forced termination, or patch-size overflow;
- fallback from required gVisor profile to default runtime.

Do not run destructive host tests. All negative tests must be confined to the disposable staging workload and must not target the host service manager or production resources.

## Evidence envelope

Each run must emit a normalized, append-only evidence record containing:

- schema version and gate `Q12-GVISOR-SHADOW`;
- `status`: PASS, FAIL or BLOCKED (never infer PASS from missing fields);
- source commit SHA and Git tree SHA;
- runtime image digest and adapter image digest;
- execution-plan/request digest and policy version;
- runtime profile requested and runtime actually observed;
- runsc version, binary SHA-256, package source and signature/checksum verification result;
- runner identity, OS, architecture, kernel and service UID/GID;
- cgroup root identity, controller set, observed `cpu.max`, `memory.max`, `pids.max` and child PID membership;
- network, mount, capability, read-only and cleanup observations;
- test result counts and raw artifact digests;
- workflow run ID, artifact ID and independent verifier identity.

The raw evidence artifact must be preserved. Do not store credentials, tokens, or secret values in evidence.

## Decision rules

- PASS means the compatibility experiment passed its declared tests only. It does not mean Q12 production gate PASS.
- Q12 production gate PASS still requires the canonical `scripts/agnes_cgroup_v2_staging_gate.py` to pass on the exact candidate subject with a connected non-root delegated runner.
- Any discrepancy between requested and observed runtime, missing artifact, missing cgroup evidence, or unverified runtime provenance => BLOCKED.
- Any security boundary regression => FAIL and disable the candidate profile on staging.
- Do not change the default runtime, policy, Q12 state, release subject or Production status from this spike.
- Any later runtime-profile integration requires a separate implementation PR, code review, full unit/regression CI, and owner approval before staging execution.

## Stop conditions

Stop immediately if the staging host is not isolated, runtime provenance cannot be verified, the Docker daemon would need an unreviewed configuration change, cgroup delegation is not writable as non-root, or any test requires production credentials/data.

No install, merge, deployment or production promotion is authorized by this plan.
