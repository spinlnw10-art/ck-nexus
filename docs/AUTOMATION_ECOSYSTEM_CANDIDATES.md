# CK-NEXUS Automation Ecosystem — Discovery Candidates

Status: RESEARCHED CANDIDATES — NOT INSTALLED, NOT TRUSTED, NOT ENABLED.

This document maps external systems that could extend CK-NEXUS. It is a discovery shortlist, not an approval to install or execute them. Every candidate must pass license, supply-chain, endpoint, data-flow, security, resource and independent-review checks before adoption.

## Recommended integration architecture

CK-NEXUS Core remains the control plane. External engines may provide execution mechanics, connectors or workflow editing, but they must not become policy authorities.

- **MCP Registry:** discover public MCP server metadata through the authenticated read-only /api/tools/discovery/mcp-registry route; use latest active versions and opaque cursor pagination; treat all records as untrusted observations. Verify publisher identity, package provenance, version, license and server transport before registration.
- **Connector Fabric:** the only supported adapter boundary for MCP/OpenAPI tool schemas, endpoint validation, credential brokering, risk classification and connector evidence.
- **Workflow Engine:** deterministic orchestration, bounded retries, idempotency, cancellation, durable checkpoints and evidence correlation.
- **AI Router:** may rank and propose tools; cannot authorize or bypass policy.
- **Core Policy Authority:** authorizes each operation with least-privilege scope and expiry. Writes/destructive actions require explicit scoped approval.
- **Evidence Graph:** records discovery source, candidate version, schema hash, review decision, policy decision, invocation correlation and verification outcome.

## Candidate systems

| System | Best fit | What it can add | Integration position |
|---|---|---|---|
| Activepieces | App-to-app automation and AI/MCP pieces | Visual flows, TypeScript pieces, retries, human approval, MCP exposure | High-priority connector/workflow adapter candidate; review CE vs EE boundary |
| n8n | Broad SaaS automation | Large node ecosystem, visual workflows, agent/tool nodes, sub-workflows | High-priority interoperability candidate; source-available Sustainable Use License, not OSI open source |
| Node-RED | Event, device and IoT automation | Visual event flows, timers, message routing, custom nodes | High-priority optional event adapter; isolate runtime and restrict nodes |
| Windmill | Script-first internal tools | Python/TypeScript/Go/Bash/SQL scripts, flows, schedules, webhooks, workers | Strong code-execution candidate; AGPLv3 and worker sandbox/resource model need review |
| Kestra | Declarative data and operations workflows | YAML flows, tasks, plugins, schedules, webhooks, event and MCP triggers | Strong workflow adapter candidate; validate plugin versions and secret handling |
| Temporal | Long-running durable business processes | Event history, replay, retry policies, recovery after worker/process failure | Best durable-execution candidate if CK-NEXUS outgrows its current task store |
| Apache Airflow | Batch/data/ML pipelines | Python DAGs, scheduling, backfills, providers and monitoring | Use for data pipelines, not as the general-purpose interactive tool router |
| Huginn | Web monitoring and event agents | RSS/IMAP/webhook/MQTT monitoring, event graphs and notifications | Candidate for watch/alert automations; outbound actions need policy mediation |
| StackStorm | Infrastructure and incident automation | Sensors, triggers, rules, actions, workflows, packs and audit trail | Candidate for operations automation; high-risk actions remain Core-gated |
| Flowise | Visual LLM and agent workflows | Visual builders, agent flows, MCP client/server nodes, tracing and evaluations | Optional AI prototyping/interop adapter; do not duplicate CK-NEXUS Core routing |
| LangGraph | Stateful multi-agent orchestration | Graph state, durable execution, streaming and human-in-the-loop | Reuse selected orchestration patterns or SDK; avoid a second authority plane |
| Dify | AI apps, workflows and knowledge pipelines | Visual AI workflows, tools, MCP publishing, triggers and traces | Candidate for knowledge/AI workflow interoperability; inspect modified license and deployment tier |

## Discovery sources

- Official MCP Registry API: https://github.com/modelcontextprotocol/registry/blob/main/docs/reference/api/official-registry-api.md
- Activepieces repository and license: https://github.com/activepieces/activepieces
- n8n workflow automation overview: https://blog.n8n.io/open-source-workflow-automation/
- Node-RED user guide: https://nodered.org/docs/user-guide/
- Windmill platform: https://www.windmill.dev/platform
- Kestra plugin catalog: https://kestra.io/docs/workflow-components/plugins
- Temporal durable execution: https://docs.temporal.io/durable-execution
- Apache Airflow docs: https://airflow.apache.org/docs/apache-airflow/
- Huginn repository: https://github.com/huginn/huginn
- StackStorm overview: https://docs.stackstorm.com/overview.html
- Flowise docs: https://docs.flowiseai.com/
- LangGraph overview: https://docs.langchain.com/oss/python/langgraph/overview
- Dify Workflow Studio: https://www.dify.ai/workflows

## Phased adoption order

1. **Discovery first:** integrate read-only MCP Registry search; persist candidates as OBSERVED with source/version/time. Never auto-install.
2. **Low-risk local catalog:** search registered, schema-verified Connector Fabric tools. Keep raw schemas and endpoints out of public search responses.
3. **Adapter pilots:** evaluate Activepieces, Node-RED and Kestra in disposable isolated environments with synthetic data. No production credentials.
4. **Durable orchestration:** compare existing CK task store against Temporal; adopt only if measured recovery/concurrency requirements justify the added service.
5. **AI workflow interoperability:** evaluate Flowise, LangGraph and Dify as optional adapters, not replacement authorities.
6. **Operations automation:** evaluate StackStorm/Huginn only with strict action allowlists, scoped credentials and human approval for side effects.
7. **Independent review:** review code, dependencies, license, image digest/provenance, SBOM, network egress, secret boundaries, resource limits, evidence export and rollback before any integration is enabled.

## Acceptance gates

- Candidate source and version are recorded; duplicate servers and versions are deduplicated.
- Registry descriptions and package metadata are treated as untrusted data, never as instructions.
- No install or runtime launch occurs during discovery.
- No credential values are stored in candidate records or logs.
- Every candidate has a license and dependency review.
- Connector endpoints are validated against SSRF/private-network policy.
- Unknown/write/destructive tools remain denied without a scoped Core grant.
- Every approved execution has correlation IDs and Evidence Graph references.
- Failure, timeout, cancellation, retry and replay behavior are tested.
- Independent review is completed before merge or deployment.

### MCP Registry behavior to preserve

The official MCP Registry is currently documented as a preview and its API may change before general availability. Its server search is a case-insensitive name substring search (minimum three characters), not semantic search. Use version=latest to avoid returning every historical version, then check the official registry metadata status and package provenance. Paginate with the returned cursor while preserving the original filters. Discovery records remain OBSERVED until CK-NEXUS review completes.
