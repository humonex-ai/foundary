"""Guard: the foundry-spec skill's bundled references must not drift.

`skills/foundry-spec/references/*.md` are generated snapshots of the repo's
authoritative sources (templates/, agents/*.py, docs/01-principles.md) by
`skills/build_references.py`. If those sources change and the bundle isn't
regenerated, the skill ships stale guidance silently. These tests fail when the
on-disk bundle differs from a fresh build — fix by running:

    python skills/build_references.py
"""

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
BUILD_SCRIPT = ROOT / "skills" / "build_references.py"
REFS = ROOT / "skills" / "foundry-spec" / "references"


def _load_builder():
    spec = importlib.util.spec_from_file_location("foundry_build_references", BUILD_SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def builder():
    return _load_builder()


def test_templates_bundle_is_current(builder):
    on_disk = (REFS / "templates.md").read_text(encoding="utf-8")
    fresh = builder.build_templates()
    assert on_disk == fresh, (
        "skills/foundry-spec/references/templates.md is stale. "
        "Run: python skills/build_references.py"
    )


def test_authoring_rules_bundle_is_current(builder):
    on_disk = (REFS / "authoring-rules.md").read_text(encoding="utf-8")
    fresh = builder.build_authoring_rules()
    assert on_disk == fresh, (
        "skills/foundry-spec/references/authoring-rules.md is stale. "
        "Run: python skills/build_references.py"
    )
