# GUAC Shadow Intake — Offline Prototype

**Upstream:** [GUAC](https://github.com/guacsec/guac), currently evaluated at release v1.1.0.  
**Scope:** local JSON SBOM/attestation preflight only.  
**Status:** prototype; not connected to a GUAC service and not a CK-NEXUS gate.

## Why GUAC

GUAC ingests CycloneDX, SPDX, in-toto/DSSE and SLSA metadata into a graph and exposes GraphQL queries. The supported persistent backend is PostgreSQL through the Ent backend; the in-memory key-value backend is suitable for a disposable evaluation. See the [supported inputs and backends](https://github.com/guacsec/guac), [component architecture](https://docs.guac.sh/guac/guac-components/), [SBOM ingestion guide](https://docs.guac.sh/guac/ingesting-sboms/) and [GraphQL API](https://docs.guac.sh/guac/graphql/).

GUAC's GraphQL schema documentation warns that schema definitions may evolve. Pin the server and client versions together and verify the actual schema from the deployed instance before writing a production adapter.

## Run the offline validator

No third-party package is required:

```bash
python scripts/assurance/guac_shadow_intake.py \
  --candidate-sha <40-character-git-commit-sha> \
  --input sbom.cdx.json \
  --input provenance.intoto.json \
  --output guac-shadow-intake.json
```

The tool:
- accepts CycloneDX, SPDX and in-toto statement JSON documents;
- requires a candidate commit SHA and at least one SBOM;
- hashes the exact local input bytes;
- rejects malformed, unknown, non-object and symlink inputs;
- refuses to overwrite an existing output file;
- emits `READY_FOR_GUAC_INGESTION`, never PASS.

It does not start containers, download tools, make network calls, verify signatures, inspect runtime artifacts, invoke GUAC, or mutate CK-NEXUS state.

## Next integration stage

1. Run the official GUAC v1.1.0 Compose stack only in a disposable isolated environment after image digests, signatures, ports, volumes and resource limits are reviewed.
2. Begin with the in-memory backend and synthetic SBOM/attestation fixtures; do not persist real repository or production data.
3. Use the documented `guacone collect files` ingestion route and query the GraphQL endpoint to verify nodes/relationships. Preserve the original input reports and hashes.
4. Test that the graph can answer candidate-to-component, component-to-vulnerability, and artifact-to-provenance queries without treating graph presence as proof of policy compliance.
5. Only after successful staging evaluation, design a read-only CK-NEXUS GraphQL client. GUAC results remain advisory; CK-NEXUS independently verifies evidence and retains gate authority.

## Security and correctness boundaries

- Do not expose the GUAC GraphQL endpoint publicly. Restrict it to a private staging network and authenticated operators.
- Do not use GUAC's heuristic package linking as a substitute for exact artifact digest verification.
- A valid SBOM does not prove it describes the deployed runtime image.
- An in-toto/SLSA document is not trusted merely because it parses; signature identity, issuer, subject digest, predicate type and trust roots require independent verification.
- Do not ingest secrets, environment dumps, private logs or production data.
- The offline intake manifest is a convenience record, not a signed attestation and not gate evidence.

## Release and license review

The upstream v1.1.0 release publishes a Compose bundle; its release asset digest must be verified before use. Re-check the upstream license, advisories, image digests and release signatures at the time of staging deployment. No version or digest in this prototype is an approved production pin.
