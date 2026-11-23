from pathlib import Path

from creator_app.agnes_skills import AgnesSkillRegistry


def test_ecosystem_acceleration_skill_is_discoverable_for_tooling_tasks():
    skill_file = (
        Path(__file__).resolve().parents[1]
        / "creator_app"
        / "skills"
        / "agnes"
        / "SKILL.md"
    )
    registry = AgnesSkillRegistry.load(skill_file)

    selected = registry.select(
        "discover benchmark fast coding tools plugins browser integrations design",
        limit=6,
    )

    assert any(skill.id == "ecosystem.accelerate" for skill in selected)