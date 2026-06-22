"""System-of-record ingest path (Model B milestone).

Accepts artifacts authored by the founder's client LLM (Claude/ChatGPT/Codex),
validates them deterministically against Foundry's templates + structural rules,
and stores them through the same state / fingerprint / approval machinery the
generator uses. No internal LLM is involved on this path.

This runs alongside the existing generator (`app.projects.create_project`) — it
does not replace or delete it. It exists to validate whether deterministic
validation is sufficient to guarantee plan quality without generation.
"""

from __future__ import annotations

import re

from app import state as state_mod
from execution.parse import ParseError, parse_decisions, parse_work_orders
from services import artifacts, product_input
from services.config import Config
from services.templates import body_sections, get_template, section_headers

# The four generated artifacts a complete plan must supply. Product Input is
# optional on ingest (it is the upstream intent, not a synced artifact).
REQUIRED_KEYS = ("vision", "architecture", "roadmap", "work-orders")
OPTIONAL_KEYS = ("product-input",)
ALL_KEYS = OPTIONAL_KEYS + REQUIRED_KEYS


class IngestError(RuntimeError):
    """Raised when submitted artifacts fail structural or coherence validation.

    Carries the full list of problems so the client can fix and resubmit.
    """

    def __init__(self, problems: list[str]):
        self.problems = problems
        super().__init__("Submitted artifacts failed validation:\n- " + "\n- ".join(problems))


def _expected_sections(key: str) -> list[str]:
    if key == "product-input":
        return list(product_input.REQUIRED_SECTIONS)
    return body_sections(key)


def artifact_filename(key: str) -> str:
    """Return the on-disk filename for an artifact key (e.g. ``00-vision.md``)."""
    if key == "product-input":
        return product_input.PRODUCT_INPUT_FILENAME
    return get_template(key).output_filename


# Backwards-compatible private alias (used within this module).
_filename = artifact_filename


def validate_artifacts(submitted: dict[str, str]) -> list[str]:
    """Validate a submission. Returns a list of problems ([] means valid).

    Checks: known keys; all required artifacts present; each artifact contains its
    template's required ``##`` sections; the Work Orders artifact parses; and
    Work Order dependencies / Decision blocks reference real Work Order ids.
    """
    problems: list[str] = []

    unknown = [k for k in submitted if k not in ALL_KEYS]
    if unknown:
        problems.append(f"unknown artifact key(s): {', '.join(sorted(unknown))}")

    for key in REQUIRED_KEYS:
        if key not in submitted:
            problems.append(f"missing required artifact: {key}")

    # Structural: required sections present in each provided artifact.
    for key, content in submitted.items():
        if key not in ALL_KEYS:
            continue
        present = set(section_headers(content))
        missing = [s for s in _expected_sections(key) if s not in present]
        if missing:
            problems.append(f"{key}: missing section(s): {', '.join(missing)}")

    # Work Orders must parse + be internally coherent.
    wo_md = submitted.get("work-orders")
    if wo_md is not None:
        try:
            work_orders = parse_work_orders(wo_md)
            decisions = parse_decisions(wo_md)
        except ParseError as exc:
            problems.append(f"work-orders: does not parse — {exc}")
        else:
            ids = {w.id for w in work_orders}
            for w in work_orders:
                for dep in w.depends_on:
                    if dep not in ids:
                        problems.append(f"work-orders: {w.id} depends on unknown {dep}")
            for d in decisions:
                for blocked in d.blocks:
                    if blocked not in ids:
                        problems.append(f"work-orders: decision {d.id} blocks unknown {blocked}")
            # Reject a Decision List that has entries but isn't in the parseable
            # pipe-table form (e.g. bullets like "- D1 — ..."), so decisions are
            # never silently invisible to the gates.
            if not decisions and _decision_list_has_entries(wo_md):
                problems.append(
                    "work-orders: Decision List has entries but none parsed — use the "
                    "pipe-table format with `D-NNN` ids (columns: ID | Decision | "
                    "Owner | Type | Status | Blocks | Rationale). See get_templates."
                )

    return problems


_DECISION_HEADER_RE = re.compile(
    r"^##\s+Decision List\s*$(.*?)(?=^##\s+|\Z)", re.MULTILINE | re.DOTALL
)
# Anything that looks like a decision id (D1, D-001, D 1) in the section body.
_LOOKS_LIKE_DECISION_RE = re.compile(r"\bD-?\s?\d")


def _decision_list_has_entries(wo_md: str) -> bool:
    """True if the Decision List section appears to contain decision entries
    (text resembling D-ids) — used to flag a present-but-unparseable list."""
    m = _DECISION_HEADER_RE.search(wo_md)
    if not m:
        return False
    return bool(_LOOKS_LIKE_DECISION_RE.search(m.group(1)))


def submit_project(config: Config, name: str, submitted: dict[str, str]) -> dict:
    """[PRIMARY] Validate and store client-authored artifacts as a project (Model B).

    The recommended entry point: the founder's client LLM authors the artifacts,
    Foundry validates + records them. No internal LLM; needs no Anthropic key.

    Validates the whole submission first (fails clearly, writes nothing on error),
    then writes each artifact and sets lifecycle: a new project becomes Draft; a
    previously Approved/Synced project re-validates its approval (Stale iff the
    sync-relevant plan changed).
    """
    problems = validate_artifacts(submitted)
    if problems:
        raise IngestError(problems)

    for key, content in submitted.items():
        artifacts.write_artifact(config, name, _filename(key), content)

    prior = state_mod.load_state(config, name)
    if prior.lifecycle == state_mod.APPROVED:
        st = state_mod.stale_if_changed(config, name)
    else:
        st = state_mod.mark_draft(config, name)

    return {
        "name": name,
        "state": st.lifecycle,
        "written": [_filename(k) for k in submitted],
        "validated": True,
    }
