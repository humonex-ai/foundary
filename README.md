# Foundry

An **AI CTO Office** — a planning, decision, and delivery **system of record**.

You brainstorm and plan with your AI client (Claude / ChatGPT / Codex). When the
plan is clear, you hand it to Foundry. Foundry **validates, records, versions,
gates decisions, manages approval, and syncs Work Orders to GitHub Issues**. It is
the durable record of *what you're building, why, what's decided, and what's in
flight* — not another plan generator.

## How it works

Your client authors the artifacts; Foundry governs them:

```
Product Input → Vision → Architecture → Roadmap → Work Orders (+ Decision List)
        │
        ▼  (your chat authors these)
   submit_project  →  validate → store → approve → sync to GitHub
```

The artifacts are plain markdown. The four downstream artifacts each follow a
fixed section structure (see `templates/`), and Work Orders carry a consolidated
**Decision List** (decisions with status/owner/blocks) that gates execution.

## Interface

Foundry runs as an **MCP server** (`foundry-mcp`), exposing tools your client
calls in natural language. Primary tools:

- **`submit_project`** — **(primary)** store client-authored artifacts after
  validation. Needs no Anthropic key.
- `show_project`, `list_projects` — read state and artifacts.
- `approve_project` — record approval (gates sync).
- `sync_github` — sync Work Orders to GitHub Issues (guarded: only an approved,
  unchanged plan syncs).
- `create_project`, `regenerate` — **(legacy)** internal LLM generator, kept for
  compatibility, pending retirement. These require `ANTHROPIC_API_KEY`.

There are no slash commands — you drive Foundry by talking to your client, which
invokes the tools.

## Install

Requires [uv](https://docs.astral.sh/uv/). The primary (system-of-record) path
needs only a GitHub token; the legacy generator additionally needs an Anthropic
key.

### Claude Code (one command)

```
claude mcp add foundry \
  -e GITHUB_TOKEN=ghp_... \
  -- uvx --from git+https://github.com/humonex-ai/foundary.git foundry-mcp
```

### Codex CLI

Add to `~/.codex/config.toml`:

```toml
[mcp_servers.foundry]
command = "uvx"
args = ["--from", "git+https://github.com/humonex-ai/foundary.git", "foundry-mcp"]
env = { GITHUB_TOKEN = "ghp_..." }
```

### Environment variables

| Variable | When needed |
|---|---|
| `GITHUB_TOKEN` | for `sync_github` (repo / `issues:write` scope) |
| `FOUNDRY_DEFAULT_REPO` | optional default `owner/repo` |
| `ANTHROPIC_API_KEY` | **only** consumed by the legacy generator tools (`create_project`, `regenerate`) |
| `FOUNDRY_PROJECTS_DIR` | optional; output root (default `projects`) |

All variables are optional. The server starts and the **primary `submit_project`
path works with no `ANTHROPIC_API_KEY`** — it's needed only if you invoke the
legacy generator tools, which fail with a clear error if it's absent.

ChatGPT (remote/HTTP MCP) is not yet supported — the server runs over local
stdio. See `docs/` for the roadmap.

## Project data

Each project lives under `projects/<name>/` as plain markdown (Product Input + the
four artifacts) plus `record.json` — the authoritative project record (lifecycle
`Draft → Approved → Stale`, append-only approvals and exports). The record is
**git-tracked**; Foundry writes it but never runs git, so **commit after you
approve or export** to make the record durable. It never contains secrets. Share
projects with a team via this git repo (commit `projects/`, pull/push).

## Documentation

Foundry dogfoods its own format — see `docs/` for vision, principles,
architecture, roadmap, work orders, and the decision log (`06-decisions.md`,
notably D-013 on the system-of-record direction).

## Development

```
uv sync --extra dev
uv run pytest
```
