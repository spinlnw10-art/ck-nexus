from creator_app.dev_assistants.orchestrator import DevAssistantFabric


def test_discovery_distinguishes_binary_presence_from_runtime_verification():
    fabric = DevAssistantFabric(
        path_lookup=lambda command: "/usr/bin/ollama" if command == "ollama" else None
    )
    rows = {row["assistant_id"]: row for row in fabric.discover()}
    ollama = rows["ollama"]
    assert ollama["available"] is True
    assert ollama["availability_basis"] == "binary_on_path_only"
    assert ollama["runtime_verified"] is False
    assert ollama["cost_gate"] == "LOCAL_RESOURCE_ONLY"
    assert rows["opencode"]["available"] is False
    assert rows["opencode"]["runtime_verified"] is False
    assert rows["opencode"]["cost_gate"] == "REQUIRES_EXPLICIT_APPROVAL"


def test_parallel_plan_is_non_executing_and_marks_paid_inference_gate():
    fabric = DevAssistantFabric(path_lookup=lambda _command: None)
    plan = fabric.build_parallel_plan(
        "Implement and test a bounded code change",
        {"engineer": ("code_edit", "repo_analysis", "test_fix")},
    )
    assert plan["execution_state"] == "PLANNED_NOT_EXECUTED"
    assert plan["runtime_verified"] is False
    assert plan["external_mutation_authorized"] is False
    assert plan["cost_authorization_required"] is True
    candidates = plan["workstreams"][0]["candidates"]
    assert candidates
    assert all("cost_gate" in item and "runtime_verified" in item for item in candidates)


def test_local_model_workstream_does_not_claim_cloud_cost_approval():
    fabric = DevAssistantFabric(path_lookup=lambda _command: None)
    plan = fabric.build_parallel_plan(
        "Use a local model only",
        {"local_model": ("local_model", "offline", "provider_backend")},
    )
    assert plan["cost_authorization_required"] is False
    candidate = plan["workstreams"][0]["candidates"][0]
    assert candidate["assistant_id"] == "ollama"
    assert candidate["inference_may_cost"] is False
