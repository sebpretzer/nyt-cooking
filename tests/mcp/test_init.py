from __future__ import annotations

import importlib
import sys

import pytest


def test_missing_fastmcp_raises_an_actionable_import_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setitem(sys.modules, "fastmcp", None)
    monkeypatch.delitem(sys.modules, "nyt_cooking.mcp", raising=False)
    monkeypatch.delitem(sys.modules, "nyt_cooking.mcp.server", raising=False)
    with pytest.raises(ImportError, match=r"uv sync --group mcp"):
        importlib.import_module("nyt_cooking.mcp")


def test_client_imports_without_fastmcp(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(sys.modules, "fastmcp", None)
    for name in [m for m in sys.modules if m.startswith("nyt_cooking")]:
        monkeypatch.delitem(sys.modules, name)
    client = importlib.import_module("nyt_cooking.client")
    assert client.Client is not None
