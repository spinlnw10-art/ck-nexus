# CK-NEXUS evidence graph bridge — shadow

This offline adapter links Q14 Collector and Q16 license-scan evidence to one exact
CK-NEXUS candidate commit. It emits a deterministic JSON graph and an in-toto Statement v1
with a CK-NEXUS custom predicate type.

## Graph model

- Candidate node: exact 40-character Git commit SHA.
- Evidence nodes: content-addressed SHA-256 of the Q14/Q16 evidence manifest.
- Tool nodes: versioned OpenTelemetry Collector, ORT and ScanCode identities.
- Artifact nodes: SHA-256 references to Q16 scan outputs.
- Edges: `SUBJECT_OF`, `PRODUCED_BY`, and `EMITS`.

The bridge accepts only the Q14/Q16 manifest fields needed for graph linkage. It does not
copy raw telemetry, source code, prompt values, user identifiers, tenant identifiers,
credentials, or scan report contents into the graph.

## Trust and authority

- Evidence must bind to the same exact candidate commit.
- Q14 must report trace, metric and secret-redaction tests as passing, with no external exporter.
- Q16 must provide valid SHA-256 references and explicitly deny gate/legal authority.
- The graph is unsigned by this bridge; it is a signing-ready evidence statement, not proof
  of signer identity or provenance.
- No GUAC endpoint is contacted and no GUAC ingestion is performed by this bridge.
- External tools remain advisory. Only CK-NEXUS Core can decide policy, approvals, gates,
  credentials, merge, or deployment.

## GUAC integration boundary

The output statement uses the in-toto Statement v1 envelope and a CK-NEXUS-specific
predicate URI. Before actual GUAC ingestion, validate that the deployed GUAC version accepts
this predicate and confirm how its graph model represents custom predicates. Then sign the
statement through the CK-NEXUS-approved attestation identity and ingest it using a
read-only, least-privilege adapter. The current prototype deliberately does neither.

## Run offline

```bash
python -m unittest tests.assurance.test_evidence_graph_bridge -v
python scripts/assurance/evidence_graph_bridge.py \
  --candidate-sha "$CANDIDATE_SHA" \
  --otel-evidence otel-collector-evidence.json \
  --q16-evidence q16-evidence.json \
  --output-graph evidence-graph.json \
  --output-statement evidence-graph.intoto.json
```
