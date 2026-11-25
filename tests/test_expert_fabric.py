from creator_app.expert_fabric import ExpertRouter, RiskClass, default_registry


def test_registry_maps_existing_ai_team_roles_and_verifier_is_not_executor():
    registry = default_registry()
    assert registry.get("engineer").agent_id == "EngineerAgent"
    assert registry.get("guardian").agent_id == "GuardianAgent"
    assert registry.get("connector").agent_id == "ConnectorAgent"
    assert registry.get("independent_verifier").may_verify is True


def test_unknown_task_routes_to_director_and_research_before_execution():
    route = ExpertRouter().route("Investigate a completely novel capability")
    assert route.primary_expert == "director"
    assert "researcher" in route.supporting_experts
    assert route.needs_discovery is True
    assert route.approval_required is False


def test_security_task_requires_guardian_and_independent_verification():
    route = ExpertRouter().route("Audit security vulnerability in authentication")
    assert route.primary_expert == "guardian"
    assert route.risk_class is RiskClass.HIGH
    assert "independent_verifier" in route.supporting_experts
    assert route.approval_required is True
    assert route.independent_verifier_required is True


def test_production_deploy_is_fail_closed():
    route = ExpertRouter().route("Deploy backend API to production")
    assert route.risk_class is RiskClass.PRODUCTION
    assert route.approval_required is True
    assert route.independent_verifier_required is True
    assert "guardian" in route.supporting_experts
    assert "independent_verifier" in route.supporting_experts


def test_multidomain_routes_add_director_without_duplicate_experts():
    route = ExpertRouter().route("Design Nuxt UI and FastAPI backend integration")
    assert {"frontend", "backend", "integrations"}.issubset(set(route.domains))
    assert "director" in route.supporting_experts
    assert len(route.supporting_experts) == len(set(route.supporting_experts))


def test_multimodal_and_provider_work_are_classified():
    multimodal = ExpertRouter().route("Route image audio and video artifacts")
    provider = ExpertRouter().route("Configure Gemini provider for CK-NEXUS")
    assert "multimodal" in multimodal.domains
    assert "provider" in provider.domains
    assert multimodal.primary_expert == "engineer"
    assert provider.primary_expert == "engineer"


def test_thai_security_request_is_high_risk():
    route = ExpertRouter().route("ตรวจสอบความปลอดภัยของระบบ")
    assert "security" in route.domains
    assert route.risk_class is RiskClass.HIGH
    assert route.independent_verifier_required is True


def test_router_never_encodes_execution_or_permission_grant():
    data = ExpertRouter().route("Connect MCP integration").as_dict()
    assert data["execution_performed"] is False
    assert data["authority_scope"] == "NONE"
    assert "permission_granted" not in data
    assert "verified" not in data
