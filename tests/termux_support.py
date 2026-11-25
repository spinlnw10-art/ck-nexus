"""Test markers for capabilities unavailable in Android Termux."""

from __future__ import annotations

import os

import pytest

IS_TERMUX = os.environ.get("PREFIX", "").startswith("/data/data/com.termux")
skip_on_termux = pytest.mark.skipif(
    IS_TERMUX,
    reason="requires host Linux process execution / namespaces unavailable in Termux",
)
