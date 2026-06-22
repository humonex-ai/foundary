#!/usr/bin/env python3
"""Build the foundry-spec skill's bundled references from authoritative sources.

The skill must be self-contained (Claude web / ChatGPT can't read the repo), so
we snapshot the real authoring guidance into references/:

- templates.md       — the full template files (guidance + skeleton), verbatim.
- authoring-rules.md — Foundry's principles + each artifact agent's system
                       prompt (the generator's per-artifact authoring rules).

When the Foundry MCP is connected, `get_templates` is the LIVE source of truth;
this bundle is the offline fallback. Re-run after changing templates/, agents/,
or docs/01-principles.md:

    python skills/build_references.py
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REFS = Path(__file__).resolve().parent / "foundry-spec" / "references"

# Chain order: head first.
TEMPLATE_ORDER = ["product-input", "vision", "architecture", "roadmap", "work-orders"]
AGENT_ORDER = ["vision", "architecture", "roadmap", "work_orders"]

_SYSTEM_PROMPT_RE = re.compile(r'SYSTEM_PROMPT\s*=\s*"""(.*?)"""', re.S)


def _agent_system_prompt(name: str) -> str:
    """Extract and de-continue the SYSTEM_PROMPT string from an agent source."""
    src = (ROOT / "agents" / f"{name}.py").read_text(encoding="utf-8")
    m = _SYSTEM_PROMPT_RE.search(src)
    if not m:
        raise SystemExit(f"SYSTEM_PROMPT not found in agents/{name}.py")
    # Source uses backslash line-continuations; rejoin to the real prompt text.
    return re.sub(r"\\\n", "", m.group(1)).strip()


def build_templates() -> str:
    parts = [
        "# Foundry artifact templates (authoritative, verbatim)\n",
        "These are the exact template files Foundry validates against. Keep every "
        "`##` header verbatim and replace each _italic prompt_ with real content. "
        "Each file has a guidance block (Purpose / Required Sections / How To Use) "
        "and, below the `<!-- TEMPLATE BODY -->` marker, the skeleton you fill.\n\n"
        "With the Foundry MCP connected, `get_templates` returns the live copies — "
        "prefer those. This file is the offline fallback (web / ChatGPT).\n\n"
        "A complete plan = four required artifacts: **vision, architecture, "
        "roadmap, work-orders**. `product-input` is optional.\n",
    ]
    for key in TEMPLATE_ORDER:
        body = (ROOT / "templates" / f"{key}.md").read_text(encoding="utf-8").strip()
        parts.append(f"\n---\n\n## `{key}.md`\n\n{body}\n")
    return "\n".join(parts).rstrip() + "\n"


def build_authoring_rules() -> str:
    principles = (ROOT / "docs" / "01-principles.md").read_text(encoding="utf-8").strip()
    parts = [
        "# Foundry authoring rules\n",
        "How to think while authoring — distilled from Foundry's principles and "
        "the per-artifact agent system prompts the generator uses. Apply these on "
        "top of the section skeletons in [templates.md](templates.md).\n",
        "\n---\n\n" + principles + "\n",
        "\n---\n\n## Per-artifact authoring rules\n",
        "These are the exact rules each Foundry artifact agent follows. Your chat "
        "plays the same role: read the upstream artifact, fill the template, obey "
        "these rules.\n",
    ]
    titles = {
        "vision": "Vision (from Product Input)",
        "architecture": "Architecture (from Vision)",
        "roadmap": "Roadmap (from Vision + Architecture)",
        "work_orders": "Work Orders (from Roadmap)",
    }
    for name in AGENT_ORDER:
        parts.append(f"\n### {titles[name]}\n\n{_agent_system_prompt(name)}\n")
    return "\n".join(parts).rstrip() + "\n"


def main() -> None:
    REFS.mkdir(parents=True, exist_ok=True)
    (REFS / "templates.md").write_text(build_templates(), encoding="utf-8")
    (REFS / "authoring-rules.md").write_text(build_authoring_rules(), encoding="utf-8")
    print(f"wrote {REFS/'templates.md'}")
    print(f"wrote {REFS/'authoring-rules.md'}")


if __name__ == "__main__":
    main()
