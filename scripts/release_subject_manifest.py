#!/usr/bin/env python3
"""Print the one canonical CK-NEXUS Q10-Q16 release-subject manifest SHA-256."""
from __future__ import annotations

import argparse
import hashlib
import re
import subprocess  # nosec B404 - fixed read-only Git tree query; no shell
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATHS = (
    "app",
    "creator_app",
    "services",
    "scripts",
    "gateway",
    "orchestration",
    "idea_engine",
    "migrations",
    "deploy",
    "observability",
    "Dockerfile",
    "docker-compose.prod.yml",
    "main.py",
    "pyproject.toml",
    "uv.lock",
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tree", default="HEAD", help="Git tree-ish; HEAD by default")
    args = parser.parse_args()
    if args.tree != "HEAD" and not re.fullmatch(r"[0-9a-f]{40,64}", args.tree):
        parser.error("--tree must be HEAD or a full hexadecimal Git object ID")
    result = subprocess.run(
        ["git", "-C", str(ROOT), "ls-tree", "-r", args.tree, "--", *PATHS],
        check=True,
        capture_output=True,
    )  # nosec B603 - fixed argv, validated tree-ish, no shell or user command
    print(hashlib.sha256(result.stdout).hexdigest())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
