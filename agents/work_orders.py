"""Work Order agent (WO-006).

Reuses the agent pattern from WO-003 / WO-004 / WO-005:

    1. read the upstream artifact      (the Roadmap, projects/<p>/02-roadmap.md)
    2. load the matching template      (services.templates, "work-orders")
    3. build a prompt and call the LLM (services.llm)
    4. write the produced artifact     (services.artifacts, 03-work-orders.md)

Breaks the Roadmap into discrete, well-scoped Work Orders and nothing more — it
describes *what* to build, not *how* to code it, and does not execute anything.
"""

from __future__ import annotations

from pathlib import Path

from services import artifacts
from services.config import Config
from services.llm import LLMClient
from services.templates import get_template, template_body

_TEMPLATE_KEY = "work-orders"

SYSTEM_PROMPT = """\
You are the Work Order agent in Foundry, an AI CTO Office. You turn a Roadmap \
into a Work Orders artifact: discrete, well-scoped units of work precise enough \
to act on without re-deriving context.

Rules:
- Think like a CTO, not an engineer. A Work Order is a SHIPPABLE OUTCOME — \
something a founder or user can observe once done — not an implementation step. \
Optimize for leverage, not completeness.
- Derive the Work Orders from the Roadmap only.
- Describe *what* to build, not *how* to code it. Do NOT write code or execute \
anything.
- NEVER create a Work Order whose only purpose is selecting, settling, \
confirming, documenting, or testing. Instead:
    * a decision (which language/library/vendor/format) goes in the "## Decision \
List";
    * a thing taken as given goes in "## Assumptions";
    * tests, setup/scaffolding, and hardening/edge-cases fold into the "Done \
when" of the capability they belong to.
- Prefer capability-oriented Work Orders: one vertical, end-to-end outcome each, \
not horizontal layers (component A, then B, then C). Merge low-leverage Work \
Orders. If a Work Order has no observable founder/user outcome, merge it upward.
- Minimize the count: the fewest Work Orders that cover the Roadmap, typically a \
handful per phase. Name each by its outcome, not the module touched.
- Every Work Order must carry these fields, exactly: Goal, In scope, Out of \
scope, Depends on, Done when, Complexity (S/M/L), Risk (Low/Medium/High). No \
time estimates. In scope and Done when cover the whole capability end to end, \
tests included.
- Dependencies must point only at earlier Work Orders.
- Fill the provided template. Keep every "## " section header exactly as given, \
in the same order. Use the per-Work-Order field block once per outcome.
- Treat the upstream Non-Goals as hard limits. Do NOT invent work, commands, or \
capabilities beyond the stated Roadmap; respect "keep it simple".
- Maintain the canonical "## Decision List". Carry every upstream Decision List \
row forward VERBATIM — same IDs and same Status (never reopen a Decided/Assumed/\
Deferred row) — and set each row's "Blocks" field to the Work Order it gates (or \
"—"). Append any new decisions with fresh IDs, triaged by REVERSIBILITY and BLAST \
RADIUS, not Type label: reversible + obvious default -> Assumed (state the \
default); scope/target-user change, material/irreversible cost, or compliance/\
legal/data-safety risk -> Open; real but non-blocking -> Deferred. Never \
auto-decide compliance, legal, or genuinely strategic items. Do not put real \
unresolved decisions in "## Assumptions".
- Record what the breakdown takes as true under "## Assumptions".
- Output ONLY the finished markdown artifact, starting with the "# Work Orders" \
heading. No preamble, no explanation, no code fences.
"""

_USER_PROMPT = """\
ROADMAP
=======
{roadmap}

WORK ORDERS TEMPLATE (fill this skeleton; keep every header verbatim)
====================================================================
{template_skeleton}
"""


def build_prompt(roadmap_doc: str, project: str) -> str:
    """Assemble the user prompt from the Roadmap and the Work Orders skeleton.

    The template's ``{{ project }}`` token is substituted with the project name
    (a literal token, no logic, per `06-decisions.md` D-009).
    """
    skeleton = template_body(_TEMPLATE_KEY).replace("{{ project }}", project)
    return _USER_PROMPT.format(roadmap=roadmap_doc, template_skeleton=skeleton)


def generate_work_orders(
    config: Config,
    project: str,
    *,
    llm: LLMClient | None = None,
) -> Path:
    """Generate the Work Orders artifact for a project and write it to disk.

    Reads ``projects/<project>/02-roadmap.md``, fills the Work Orders template via
    the LLM, and writes ``projects/<project>/03-work-orders.md``. Returns the
    written path.

    ``llm`` is injectable so tests can supply a fake; when omitted a real
    :class:`LLMClient` is constructed from ``config``.

    Raises :class:`services.artifacts.ArtifactError` if the Roadmap is missing;
    no output is written in that case.
    """
    # 1. read upstream (Roadmap). Missing -> ArtifactError, before any LLM call.
    (roadmap_name,) = get_template(_TEMPLATE_KEY).upstream
    roadmap_doc = artifacts.read_artifact(config, project, roadmap_name)

    # 2. + 3. build prompt and call the LLM
    client = llm if llm is not None else LLMClient(config)
    prompt = build_prompt(roadmap_doc, project)
    work_orders_md = client.complete(prompt, system=SYSTEM_PROMPT)

    # 4. write the artifact
    output_filename = get_template(_TEMPLATE_KEY).output_filename
    return artifacts.write_artifact(config, project, output_filename, work_orders_md)
