# Q11 Promptfoo synthetic shadow harness

## Purpose

This is an additive harness-wiring and fixture-contract check for Q11. It uses Promptfoo with a deterministic local Python provider to exercise a small set of CK-NEXUS security-boundary examples: instruction override, secret exfiltration, cross-tenant access, approval bypass, unauthorized tool execution, and a benign read-only request.

## Important limits

- The provider is a deterministic synthetic fixture, not an LLM, not the CK-NEXUS runtime, and not a security policy implementation.
- A passing run proves only that Promptfoo can load the local provider and that the fixture assertions behave as authored.
- It does not test model robustness, live provider reachability, tenant isolation, actual capability leases, approval registry behavior, or tool execution.
- It does not replace the canonical Q11 live Responses API gate in `scripts/test_openai_live.py`.
- No API key, model credential, network target, production endpoint, or remote red-team generation is used.
- This shadow workflow must not update Q11 evidence or gate state.

## Run locally

Requires Node.js 24+ and Promptfoo 0.126.0:

```bash
npx --yes promptfoo@0.126.0 eval \
  -c tests/assurance/q11_promptfoo/promptfooconfig.yaml \
  --no-progress-bar \
  --output q11-promptfoo-results.json
```

Review the JSON report and ensure all six fixture cases pass. Do not interpret this as Q11 PASS.

## Next Q11 stages

1. Review the synthetic fixtures and their mapping to CK-NEXUS identity, capability, approval, credential, tenant, and tool boundaries.
2. Add a staging-only adapter to a real CK-NEXUS policy/agent test endpoint, using synthetic tenant and test data.
3. Only after separate explicit authorization and a project-scoped staging secret exists, run Promptfoo against the authorized staging model/provider.
4. Run `scripts/test_openai_live.py` separately against the exact release identity with the authorized staging credential. This is the canonical live-provider gate.
5. Bind all resulting evidence to the exact immutable release subject; never promote from a synthetic run.
