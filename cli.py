"""Foundry CLI (Execution V1).

Two read-or-sync commands over GitHub Issues. Plain argparse, no framework
(`06-decisions.md` D-010).

    foundry sync-issues  <project> --repo owner/repo [--dry-run] [--reconcile]
    foundry issue-status <project> --repo owner/repo
"""

from __future__ import annotations

import argparse
import sys

from execution import parse
from execution import sync as sync_mod
from services.artifacts import read_artifact
from services.config import Config

WORK_ORDERS_FILE = "03-work-orders.md"


def _load(config: Config, project: str):
    md = read_artifact(config, project, WORK_ORDERS_FILE)
    return parse.parse_work_orders(md), parse.parse_decisions(md)


def _github(config: Config):
    from services.github import GitHubClient

    return GitHubClient(config.github_token)


def _repo(args, config: Config) -> str:
    repo = args.repo or config.default_repo
    if not repo:
        raise SystemExit("error: --repo owner/name required (or set FOUNDRY_DEFAULT_REPO)")
    return repo


def cmd_sync(args) -> int:
    config = Config.from_env()
    repo = _repo(args, config)
    work_orders, decisions = _load(config, args.project)
    report = sync_mod.sync(
        args.project, repo, work_orders, decisions, _github(config),
        dry_run=args.dry_run, reconcile=args.reconcile,
    )
    prefix = "[dry-run] " if args.dry_run else ""
    for a in report.actions:
        num = f"#{a.number}" if a.number else "(new)"
        print(f"{prefix}{a.action:15} {a.wo_id or '-':8} {num:6} {a.note}")
    counts = {}
    for a in report.actions:
        counts[a.action] = counts.get(a.action, 0) + 1
    print("summary:", ", ".join(f"{k}={v}" for k, v in sorted(counts.items())) or "nothing")
    return 0


def cmd_status(args) -> int:
    config = Config.from_env()
    repo = _repo(args, config)
    work_orders, decisions = _load(config, args.project)
    rows = sync_mod.status(args.project, repo, work_orders, decisions, _github(config))
    for r in rows:
        num = f"#{r.number}" if r.number else "-"
        flag = "READY" if r.ready else "BLOCKED"
        print(f"{r.wo_id:8} {num:6} {r.state:11} {flag:8} {r.detail}")
    ready = sum(1 for r in rows if r.ready)
    print(f"summary: {ready}/{len(rows)} ready")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="foundry", description="Foundry CLI")
    sub = p.add_subparsers(dest="command", required=True)

    s = sub.add_parser("sync-issues", help="Sync Work Orders to GitHub Issues")
    s.add_argument("project")
    s.add_argument("--repo", default="")
    s.add_argument("--dry-run", action="store_true")
    s.add_argument("--reconcile", action="store_true")
    s.set_defaults(func=cmd_sync)

    st = sub.add_parser("issue-status", help="Authoritative readiness view")
    st.add_argument("project")
    st.add_argument("--repo", default="")
    st.set_defaults(func=cmd_status)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv if argv is not None else sys.argv[1:])
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
