"""Tests for the MCP adapter surface (MCP V1). No live transport, no network."""

import inspect

import mcp_server


EXPECTED_TOOLS = {
    "list_projects",
    "create_project",
    "show_project",
    "regenerate",
    "approve_project",
    "sync_github",
}


def test_tool_surface_is_exactly_the_six():
    assert set(mcp_server.TOOLS) == EXPECTED_TOOLS
    assert all(callable(fn) for fn in mcp_server.TOOLS.values())


def test_no_update_decision_tool():
    assert "update_decision" not in mcp_server.TOOLS


def test_build_server_registers_without_error():
    server = mcp_server.build_server()
    assert server is not None  # FastMCP built with the six tools registered


def test_tools_delegate_to_app(monkeypatch):
    # Each tool is a thin pass-through to app.projects; verify delegation.
    called = {}

    def fake_create_project(cfg, name, product_input):
        called["create"] = (name, product_input)
        return {"name": name, "state": "Draft", "artifacts": []}

    monkeypatch.setattr(mcp_server.app, "create_project", fake_create_project)
    monkeypatch.setattr(mcp_server, "_cfg", lambda: object())
    out = mcp_server.create_project("acme", "PI")
    assert called["create"] == ("acme", "PI")
    assert out["state"] == "Draft"
