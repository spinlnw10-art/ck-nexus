from pathlib import Path


def test_workspace_has_safe_area_and_mobile_viewport_support():
    html = Path("creator_app/web/workspace.html").read_text()
    css = Path("creator_app/web/workspace.css").read_text()
    assert "viewport-fit=cover" in html
    assert "100svh" in css
    assert "safe-area-inset-bottom" in css
    assert "safe-area-inset-top" in css


def test_workspace_adapts_phone_tablet_and_landscape_layouts():
    css = Path("creator_app/web/workspace.css").read_text()
    assert "max-width:700px" in css
    assert "max-width:380px" in css
    assert "min-width:701px" in css
    assert "orientation:landscape" in css
    assert "grid-template-columns:repeat(7,minmax(0,1fr))" in css
    assert "grid-template-columns:minmax(0,1fr)" in css


def test_workspace_keeps_all_primary_mobile_navigation_destinations():
    html = Path("creator_app/web/workspace.html").read_text()
    for token in (
        'id="new-chat"',
        'data-panel="chat"',
        'data-panel="history"',
        'data-panel="functions"',
        'data-panel="connections"',
        'href="/development"',
        'id="settings-open"',
    ):
        assert token in html


def test_chat_workspace_removes_hero_copy_and_uses_fixed_viewport():
    html = Path("creator_app/web/workspace.html").read_text()
    css = Path("creator_app/web/workspace.css").read_text()
    assert "YOUR AI WORKSPACE" not in html
    assert "What can we" not in html
    assert "สั่งงาน CK-NEXUS ผ่านพื้นที่สนทนาเดียว" not in html
    assert "height:100dvh" in css
    assert "overflow-y:auto" in css
    assert "overscroll-behavior:contain" in css


def test_audio_panel_is_dismissible_and_has_no_url_input():
    html = Path("creator_app/web/workspace.html").read_text()
    js = Path("creator_app/web/workspace.js").read_text()
    assert 'id="music-close"' in html
    assert 'id="music-reopen"' in html
    assert 'id="music-url"' not in html
    assert 'id="music-form"' not in html
    assert "music-form" not in js
    assert '$("#music-reopen")' in js


def test_workspace_effects_respect_reduced_motion():
    css = Path("creator_app/web/workspace.css").read_text()
    assert "@keyframes coreBreathe" in css
    assert "@keyframes nexusSheen" in css
    assert "@media(prefers-reduced-motion:reduce)" in css


def test_workspace_exposes_verified_function_search_without_execute_controls():
    html = Path("creator_app/web/workspace.html").read_text()
    js = Path("creator_app/web/workspace.js").read_text()
    css = Path("creator_app/web/workspace.css").read_text()
    assert 'id="tool-search-form"' in html
    assert 'id="tool-search-query"' in html
    assert 'id="tool-search-results"' in html
    assert '"/api/tools/search?"' in js
    assert 'item.execution_available' not in js
    assert ".tool-result-card" in css
    assert "@media(max-width:700px)" in css


def test_workspace_separates_local_function_search_from_mcp_registry_discovery():
    html = Path("creator_app/web/workspace.html").read_text()
    js = Path("creator_app/web/workspace.js").read_text()
    assert 'id="mcp-registry-search"' in html
    assert '"/api/tools/discovery/mcp-registry?"' in js
    assert 'OBSERVED only' in js
    assert 'ยังไม่ติดตั้ง' in js


def test_workspace_supports_safe_mcp_registry_metadata_inspection():
    js = Path("creator_app/web/workspace.js").read_text()
    assert 'Inspect metadata' in js
    assert '/api/tools/discovery/mcp-registry/details?' in js
    assert 'ยังไม่ตรวจ License / Provenance / Security' in js
    assert 'execution_enabled' not in js
