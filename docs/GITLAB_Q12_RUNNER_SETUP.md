# GitLab Q12 delegated cgroup-v2 runner setup

## Purpose

The `cgroup_v2_staging` job is a release-evidence gate. It must run on a dedicated Linux runner that has a real delegated cgroup-v2 subtree. A GitLab SaaS shared runner, a read-only `/sys/fs/cgroup` mount, or a mocked cgroup check is not acceptable Q12 evidence.

## Required runner

- Dedicated Linux VM or host with unified cgroup v2.
- GitLab Runner registered to project `chokmantol/ck-nexus` (project ID `89477515`), with tag `cknexus-cgroup-v2`.
- Prefer a shell executor on a disposable, isolated runner host; do not mount the host cgroup filesystem into a general-purpose shared container runner.
- Runner must be locked to this project, must not run untrusted jobs from other projects, and must not receive production credentials or deployment secrets.
- Configure the runner service under systemd with controller delegation for `cpu`, `memory`, and `pids` (for example, a service drop-in using `Delegate=cpu memory pids`). Verify the resulting service subtree is writable by the runner identity and exposes all three controllers.
- Set `CKNEXUS_AGNES_CGROUP_ROOT` in the runner's protected local environment to the actual delegated subtree path. Do not set it to `/sys/fs/cgroup` unless that exact root is the writable delegated boundary. Do not store runner tokens or secrets in this repository.

## Register and validate

1. In GitLab project Settings → CI/CD → Runners, create a project runner using GitLab's current runner creation flow. Use the runner authentication token (`glrt-` token) only on the host during registration; do not use or publish a legacy registration token.
2. Apply the tag `cknexus-cgroup-v2`; disable untagged jobs; lock it to this project. Keep the host disposable and isolated because CI executes repository code.
3. On the runner host, verify unified cgroup v2, delegated write access as the runner service identity, and availability of `cpu`, `memory`, and `pids` in the configured subtree.
4. Run the MR pipeline. The job first executes `scripts/agnes_cgroup_v2_staging_gate.py`, which creates a disposable child cgroup, writes the exact CPU/memory/PID limits, attaches a child PID, reads back the effective values, and cleans up.
5. The job then runs all `cgroup_staging` tests. The evidence manifest requires the JSON gate result and validates the observed values; missing, BLOCKED, FAIL, malformed, or mismatched evidence fails closed.

## Exact Q12 PASS criteria

- `CKNEXUS_ENVIRONMENT=staging`.
- `unified_v2=true` and `delegated_writable=true`.
- Controllers include `cpu`, `memory`, and `pids`.
- `cpu.max=20000 100000`.
- `memory.max=67108864`.
- `pids.max=16`.
- The child PID is present in `cgroup.procs`.
- All marked staging tests pass.
- The exact-head evidence manifest validates the Q12 report hash and records Q12 PASS.

A runner being online, a pending job being assigned, or a test that only checks controller presence is not Q12 PASS.
