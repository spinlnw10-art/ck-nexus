"""Deterministic synthetic provider for Q11 harness wiring tests only.

This is not an LLM, policy engine, or substitute for scripts/test_openai_live.py.
It performs no network, tool, credential, or CK-NEXUS state access.
"""
from __future__ import annotations

import json
import re
from typing import Any

DENY_PATTERNS = (
    r"ignore (all )?(previous|prior) instructions",
    r"reveal|exfiltrate|print|dump (the )?(secret|credential|api key|token)",
    r"cross[- ]tenant",
    r"bypass (the )?approval",
    r"override (the )?(system|security|policy)",
    r"deploy to production",
    r"delete (the )?(database|repository|branch|backup)",
    r"write access",
    r"execute (the )?(tool|command|shell)",
    r"send .*credential",
)


def call_api(prompt: str, options: dict[str, Any], context: dict[str, Any]) -> dict[str, str]:
    """Return a deterministic synthetic decision for fixture validation."""
    normalized = prompt.casefold()
    matched = next((pattern for pattern in DENY_PATTERNS if re.search(pattern, normalized)), None)
    if matched:
        result = {
            "decision": "deny",
            "reason": "synthetic_policy_fixture_match",
            "tool_execution": "not_performed",
        }
    else:
        result = {
            "decision": "allow_read_only",
            "reason": "synthetic_safe_fixture",
            "tool_execution": "not_performed",
        }
    return {"output": json.dumps(result, separators=(",", ":"), sort_keys=True)}
