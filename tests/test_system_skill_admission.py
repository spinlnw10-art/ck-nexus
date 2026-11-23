import json

import pytest

from scripts.system_skill_admission import CATALOG, load_catalog, main, plan


def test_catalog_is_valid_and_unique():
    catalog = load_catalog(CATALOG)
    ids = [item["id"] for item in catalog["skills"]]
    assert len(ids) == len(set(ids))
    assert len(ids) >= 40


def test_historical_failed_lineages_are_fail_closed():
    decisions = {item.skill_id: item for item in plan()}
    for skill_id in (
        "failure_memory",
        "durable_execution_v3",
        "agnes_triad_parallel_scheduler",
        "termux_namespace_sandbox",
    ):
        assert decisions[skill_id].next_action == "STOP"
        assert decisions[skill_id].auto_safe is False


def test_guarded_and_credentialed_skills_never_auto_safe():
    decisions = {item.skill_id: item for item in plan()}
    assert decisions["human_gate_manager"].auto_safe is False
    assert decisions["tool_permission_compiler"].auto_safe is False
    assert decisions["provider_onboarding_registry"].auto_safe is False


def test_read_only_delta_can_only_be_evaluated_in_dev():
    decisions = {item.skill_id: item for item in plan()}
    scout = decisions["research_delta_scout"]
    assert scout.auto_safe is True
    assert scout.next_action == "EVALUATE_IN_DEV"
    assert scout.auto_install is False
    assert scout.auto_activate is False
    assert scout.authority_scope == "NONE"


def test_paid_provider_work_requires_cost_and_core_approval():
    decisions = {item.skill_id: item for item in plan()}
    provider = decisions["provider_council"]
    assert provider.auto_safe is False
    assert provider.requires_cost_approval is True
    assert provider.requires_core_approval is True
    assert provider.next_action == "REVIEW_WITH_CORE_APPROVAL"


def test_canonical_components_are_reused_not_rebuilt():
    decisions = {item.skill_id: item for item in plan()}
    assert decisions["pattern_selection_router"].next_action == "REUSE_CANONICAL"
    assert decisions["expert_fabric"].next_action == "REUSE_CANONICAL"
    assert decisions["skill_foundry"].next_action == "REVIEW_WITH_CORE_APPROVAL"


def test_all_decisions_keep_install_and_activation_disabled():
    for decision in plan():
        assert decision.auto_install is False
        assert decision.auto_activate is False
        assert decision.authority_scope == "NONE"


def test_catalog_rejects_duplicate_ids_and_unsafe_policy_override(tmp_path):
    raw = json.loads(CATALOG.read_text())
    raw["skills"].append(dict(raw["skills"][0]))
    duplicate_path = tmp_path / "duplicate.json"
    duplicate_path.write_text(json.dumps(raw))
    with pytest.raises(ValueError, match="duplicate"):
        load_catalog(duplicate_path)

    raw = json.loads(CATALOG.read_text())
    raw["adoption_policy"]["auto_install"] = True
    unsafe_path = tmp_path / "unsafe.json"
    unsafe_path.write_text(json.dumps(raw))
    with pytest.raises(ValueError, match="auto_install=false"):
        load_catalog(unsafe_path)


def test_cli_does_not_accept_caller_selected_catalog_path(monkeypatch):
    import sys

    monkeypatch.setattr(sys, "argv", ["system_skill_admission", "--catalog", "/tmp/untrusted.json"])
    with pytest.raises(SystemExit) as error:
        main()
    assert error.value.code == 2
