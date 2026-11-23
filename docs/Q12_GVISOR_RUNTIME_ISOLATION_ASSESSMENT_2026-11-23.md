# Q12 Runtime Isolation — gVisor / Kata Adoption Assessment

Date: 2026-11-23
Status: ARCHITECTURE EVALUATION ONLY — NOT INSTALLED, NOT Q12 EVIDENCE
Base: `944d7cb70a5d59d53c8fb379752bbee2085f7c8c`

## Executive decision

Adopt **gVisor (`runsc`) as the first optional runtime-isolation compatibility target** for CK-NEXUS development workloads, subject to a real staging compatibility spike. Keep the existing Docker/Podman sandbox path as the default until the spike passes.

Keep **native delegated cgroup v2 enforcement mandatory and independent**. gVisor is an additional kernel attack-surface boundary; it does not replace the Q12 requirement to prove non-root delegated `cpu`, `memory`, and `pids` controls on the actual staging runner.

Treat **Kata Containers as a conditional second-stage option**, not the default: it provides a hardware-virtualized guest-kernel boundary, but requires a compatible virtualization-capable host (or nested virtualization), a supported containerd/CRI/Docker integration, and additional operational capacity.

No runtime installation, daemon configuration, host mutation, Q12 gate change, or production promotion is authorized by this assessment.

## Current CK-NEXUS baseline

The existing `creator_app/sandbox_executor/executor.py`:
- accepts Docker or Podman only;
- refuses root execution;
- requires an immutable `@sha256:` adapter image;
- uses `--pull=never`, `--network=none`, `--read-only`, `--cap-drop=ALL`, `no-new-privileges`, PID/memory/CPU limits and a non-root UID/GID;
- creates a disposable Git worktree, captures a bounded patch, and never applies/commits/pushes it;
- returns `EXECUTED_UNVERIFIED`; it does not create release evidence.

The existing Phase 3 kernel hardening includes namespace/chroot, seccomp and cgroup v2 support. Its recorded validation states seccomp PASS but live delegated cgroup v2 BLOCKED because the environment's cgroup tree was read-only/not delegated.

The canonical Q12 staging gate is `scripts/agnes_cgroup_v2_staging_gate.py`. It must observe:
- delegated writable cgroup v2 owned by the non-root service identity;
- `cpu`, `memory`, and `pids` controllers;
- `cpu.max=20000 100000`, `memory.max=67108864`, `pids.max=16`;
- a child process attached to the child cgroup.

The current `RELEASE_STATUS.md` says Q12 is NOT_VERIFIED/BLOCKED because the registered `cknexus-q12` runner is offline and there is no current-subject delegated-cgroup evidence. Historical `evidence/Q12_CGROUP_V2.json` is bound to an older source SHA/tree and manifest; it must not be reused as current-subject PASS evidence.

## Standards and runtime comparison

| Candidate | Isolation model | Integration fit | Key constraints | Decision |
|---|---|---|---|---|
| Existing Docker/Podman + Linux namespaces/seccomp/cgroups | Shared host kernel with Linux isolation primitives | Already integrated | Current path; Q12 still needs real delegated cgroup evidence | Keep default |
| gVisor `runsc` | Userspace application kernel intercepts workload syscalls; OCI runtime | OCI runtime; Docker and Kubernetes integration documented | Linux ABI is not complete; workload compatibility/performance must be tested; outer host cgroups still needed for enforced resource ceilings | First optional spike |
| Kata Containers | Each container/pod runs inside a lightweight VM with guest kernel | OCI-compatible; containerd shim v2, CRI-O, Kubernetes and Docker paths documented | Hardware virtualization/nested virtualization and VM lifecycle requirements; greater operational/resource cost | Conditional second spike |
| Firecracker / microVM | MicroVM boundary | Would require a separate integration and image/workspace lifecycle adapter | Not justified before gVisor/Kata compatibility evidence | Defer |

### Why gVisor first

gVisor provides a distinct isolation layer from namespaces/seccomp and exposes `runsc` as an OCI runtime. Docker's documented integration uses an explicit `--runtime=runsc` selection. This makes it a plausible opt-in backend without replacing CK-NEXUS's executor contract.

However, gVisor's own compatibility documentation explicitly notes unimplemented Linux features and workload-specific compatibility testing. It also documents that in-sandbox cgroup CPU/memory controls do not enforce resource limits between competing processes. Therefore CK-NEXUS must retain host-side delegated cgroup v2 as the authoritative resource-enforcement mechanism.

### Why Kata is not the first choice

Kata creates a hardware-virtualized guest kernel boundary and implements OCI/containerd shim interfaces. Its current installation guidance requires virtualization support on the host (or nested virtualization in a VM) and recommends a modern containerd path. The current CK-NEXUS staging runner is offline, and its hardware/virtualization capabilities have not been verified. Kata should not be selected until those prerequisites and operational costs are proven.

## Target integration architecture

Preserve the existing authority and executor flow:

`Human Principal -> Agent Identity -> Capability Lease -> Policy/Reversibility -> Approval Registry -> Credential Reference Broker -> Deny-by-default Sandbox -> Execution Envelope/Journal -> Executor -> Independent Effect Verification -> Evidence Record`

Add a runtime-selection adapter **inside the existing sandbox executor**, not a new authority plane:

1. CK-NEXUS policy chooses a named isolation profile; agents cannot self-select or downgrade it.
2. The execution plan binds the runtime profile, runtime binary/version, image digest, source SHA/tree, and resource ceilings.
3. The executor checks that the selected runtime is installed, registered, allowlisted, and at the expected version; missing or mismatched runtime => BLOCKED.
4. Docker `runsc` is opt-in and must preserve the existing `--pull=never`, `--network=none`, read-only rootfs, capability drop, no-new-privileges, non-root UID/GID, resource limits and bounded output.
5. Host cgroup v2 remains mandatory for CPU/memory/PID ceilings; the runtime must not be allowed to relax or replace those limits.
6. Runtime identity/version and actual observed isolation mode are captured in execution evidence. A requested `runsc` profile is not proof that `runsc` actually executed.
7. Independent verification confirms the runtime identity, cgroup values, network denial, filesystem constraints, and patch-only behavior.
8. Any failure or missing evidence fails closed; no fallback to runc/Podman default is allowed for a request that required gVisor.

The runtime profile must be included in the approved request digest. It must not be injected as an unbound environment variable or silently chosen by an agent.

## Compatibility and security risks to test

- Docker engine/runtime registration and `runsc` version identity.
- Linux architecture and host kernel compatibility (do not assume x86_64 or arm64 support from another runner).
- Adapter image behavior under gVisor: Python/Node toolchains, subprocess, signals, temporary files, bind-mounted worktree and patch capture.
- Network denial remains effective; no host networking, Docker socket, privileged mode, or credential forwarding.
- Read-only root filesystem and writable `/workspace` mount behavior.
- Outer cgroup v2 enforcement: actual child PID must be attached and limits observed from the host.
- Runtime startup/shutdown cleanup after success, failure, timeout and worker termination.
- Performance and filesystem I/O overhead measured against the current default runtime.
- Runtime binary and sidecar/package provenance, pinned version, checksums/signatures, update/rollback procedure.
- Host daemon changes are staged and reversible; no global Docker daemon mutation without separate approval.

## Rollout gates

| Stage | Work | Exit criteria | State |
|---|---|---|---|
| 0 | Read-only baseline and source review | Existing executor and Q12 requirements mapped | Completed in this assessment |
| 1 | Runtime adapter design + unit tests | Profile bound to approval digest; command builder tests; fail-closed tests | Not started |
| 2 | Isolated staging host preflight | Dedicated non-root runner online; Docker/runsc versions and host capabilities recorded | Blocked pending host |
| 3 | gVisor shadow execution | Same pinned image and task tested in default runtime and runsc; no external network; exact observed runtime identity | Not started |
| 4 | Security regression | Negative tests for network, mounts, capabilities, privilege, cgroup escape, timeout, cleanup and fallback | Not started |
| 5 | Independent evidence review | Raw artifacts, hashes, source SHA/tree, runtime version, cgroup observations and verifier identity reconciled | Not started |
| 6 | Optional profile proposal | Separate owner approval for any default/profile policy change | Not authorized |

## Acceptance and rollback rules

- Existing default sandbox behavior must remain byte-for-byte equivalent unless a separately reviewed change is required.
- gVisor is optional; a missing or unhealthy gVisor runtime must block only requests whose approved profile requires gVisor. It must never silently fall back.
- A gVisor smoke test does not satisfy Q12 unless the canonical delegated cgroup v2 gate independently passes on the same exact staging subject.
- A Q12 PASS requires current-subject raw evidence, not this document or historical evidence.
- No production enablement, branch merge, deployment, or gate-status mutation is part of this work.
- Rollback means disabling the optional profile in staging and returning to the existing approved default; preserve all logs/evidence and do not delete runtime artifacts until separately reviewed.

## Primary references

- gVisor overview and OCI runtime `runsc`: https://gvisor.dev/docs/
- gVisor application compatibility: https://gvisor.dev/docs/user_guide/compatibility/
- gVisor production guidance: https://gvisor.dev/docs/user_guide/production/
- gVisor Docker quick start/runtime selection: https://gvisor.dev/docs/user_guide/quick_start/docker/
- gVisor networking and network isolation options: https://gvisor.dev/docs/user_guide/networking/
- Kata Containers overview and isolation model: https://kata-containers.github.io/kata-containers/
- Kata installation prerequisites: https://github.com/kata-containers/kata-containers/blob/main/docs/installation.md
- Kata current architecture and containerd shim v2: https://github.com/kata-containers/kata-containers/blob/main/docs/design/architecture/README.md
- CK-NEXUS Q12 cgroup deployment contract: `docs/PHASE3_CGROUP_DEPLOYMENT.md`
- CK-NEXUS Q12 production closure contract: `docs/PRODUCTION_CLOSURE_Q10_Q12_RUNBOOK.md`

## Non-claims

This assessment does not claim gVisor or Kata is installed, available on the current runner, compatible with CK-NEXUS adapter images, independently audited, or production-ready. It does not claim Q12 PASS. Production remains NO-GO.
