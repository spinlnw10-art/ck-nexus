from __future__ import annotations

from .models import ExpertProfile


class ExpertRegistry:
    """Metadata-only mapping to the existing CK-NEXUS AI team roles."""

    def __init__(self, profiles: tuple[ExpertProfile, ...] = ()) -> None:
        self._profiles = {profile.expert_id: profile for profile in profiles}
        if len(self._profiles) != len(profiles):
            raise ValueError("expert ids must be unique")

    def get(self, expert_id: str) -> ExpertProfile:
        return self._profiles[expert_id]

    def all(self) -> tuple[ExpertProfile, ...]:
        return tuple(self._profiles[key] for key in sorted(self._profiles))

    def for_domain(self, domain: str) -> tuple[ExpertProfile, ...]:
        return tuple(profile for profile in self.all() if domain in profile.domains)


def default_registry() -> ExpertRegistry:
    """Reuse current AI-team agents; the verifier is a review role, not an executor."""
    profiles = (
        ExpertProfile(
            "director",
            "DirectorAgent",
            ("architecture", "business", "cross_domain"),
            ("repo_analysis", "subagents"),
        ),
        ExpertProfile(
            "engineer",
            "EngineerAgent",
            ("backend", "frontend", "data", "ai_ml", "devops", "provider", "multimodal"),
            ("code_edit", "repo_analysis", "test_fix"),
        ),
        ExpertProfile(
            "guardian",
            "GuardianAgent",
            ("security", "reliability", "compliance"),
            ("repo_analysis", "test_fix", "sandbox", "benchmark"),
        ),
        ExpertProfile(
            "analyst",
            "AnalystAgent",
            ("analysis", "data", "finance", "observability", "knowledge"),
            ("repo_analysis", "benchmark"),
        ),
        ExpertProfile(
            "researcher",
            "ResearcherAgent",
            ("research", "legal", "standards", "knowledge"),
            ("web", "repo_analysis"),
        ),
        ExpertProfile(
            "designer",
            "DesignerAgent",
            ("ux", "frontend"),
            ("code_edit", "repo_analysis"),
        ),
        ExpertProfile(
            "connector",
            "ConnectorAgent",
            ("integrations", "devops", "automation"),
            ("mcp", "workflow", "repo_analysis"),
        ),
        ExpertProfile(
            "independent_verifier",
            "IndependentVerifier",
            ("verification",),
            ("benchmark", "test_fix", "repo_analysis"),
            may_verify=True,
        ),
    )
    return ExpertRegistry(profiles)
