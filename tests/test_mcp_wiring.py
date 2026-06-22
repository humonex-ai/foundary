"""Tests for the MCP adapter surface (MCP V1). No live transport, no network."""

import inspect

import mcp_server


EXPECTED_TOOLS = {
    "list_projects",
    "get_templates",
    "create_project",
    "submit_project",
    "show_project",
    "regenerate",
    "approve_project",
    "sync_github",
}


def test_tool_surface_is_exactly_the_expected_set():
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


def test_sync_github_tool_delegates_to_app_export(monkeypatch):
    # The MCP sync_github tool routes through the single shared export path.
    called = {}

    def fake_export(cfg, name, repo, *, via):
        called["export"] = (name, repo, via)
        return {"synced": True}

    monkeypatch.setattr(mcp_server.app, "export", fake_export)
    monkeypatch.setattr(mcp_server, "_cfg", lambda: object())
    mcp_server.sync_github("acme", "o/r")
    assert called["export"] == ("acme", "o/r", "mcp")


def test_cli_sync_delegates_to_app_export(monkeypatch):
    # The CLI sync-issues command routes through the same shared export path.
    import cli
    called = {}

    def fake_export(config, project, repo, *, gh, dry_run, reconcile, via):
        called["export"] = (project, repo, dry_run, reconcile, via)
        return {"synced": True, "summary": {}, "actions": []}

    monkeypatch.setattr(cli.app_projects, "export", fake_export)
    monkeypatch.setattr(cli, "Config", type("C", (), {"from_env": staticmethod(lambda: type("X", (), {"default_repo": "o/r"})())}))
    monkeypatch.setattr(cli, "_github", lambda c: None)
    args = type("A", (), {"project": "acme", "repo": "o/r", "dry_run": False, "reconcile": False})()
    cli.cmd_sync(args)
    assert called["export"] == ("acme", "o/r", False, False, "cli")
