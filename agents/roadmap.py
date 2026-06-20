"""Roadmap agent (WO-005).

Reuses the agent pattern from WO-003 / WO-004:

    1. read the upstream artifacts     (Vision + Architecture)
    2. load the matching template      (services.templates, "roadmap")
    3. build a prompt and call the LLM (services.llm)
    4. write the produced artifact     (services.artifacts, 02-roadmap.md)

Derives the Roadmap from the Vision and Architecture and nothing more — no work
orders, no orchestration.
"""

from __future__ import annotations

from pathlib import Path

from services import artifacts
from services.config import Config
from services.llm import LLMClient
from services.templates import get_template, template_body

_TEMPLATE_KEY = "roadmap"

SYSTEM_PROMPT = """\
You are the Roadmap agent in Foundry, an AI CTO Office. You turn a Vision and an \
Architecture into a Roadmap artifact: the sequence of work that delivers them.

Rules:
- Think like a CTO, not an engineer. Phases are founder-visible outcomes — \
usable increments of the product a founder would recognize — not buckets of \
engineering tasks.
- Derive the Roadmap from the Vision and Architecture only.
- Produce the Roadmap only. Do NOT produce work orders.
- Describe the CAPABILITY each phase delivers, not how it is built. Do NOT list \
files, modules, classes, tests, libraries, or implementation tasks inside a \
phase. If you are naming build steps, you are at the wrong altitude.
- Prefer 2–4 phases for a typical V1. Minimize phase count while preserving \
clarity. Each phase must leave the product usefully more complete than before.
- Every phase must trace back to the Vision. Order phases so each is worth doing \
before the next begins; nothing in a later phase may be required by an earlier \
one.
- Fill the provided template. Keep every "## " section header exactly as given, \
in the same order. Do not add or rename sections.
- Keep deferred work visible under "## Deferred" rather than dropping it or \
pulling it forward.
- Treat the upstream Non-Goals as hard limits. Do NOT invent features, commands, \
or capabilities beyond the stated Goals; respect "keep it simple".
- Maintain the "## Decision List". Carry the upstream Decision List forward \
VERBATIM — same IDs and same Status (never reopen a Decided/Assumed/Deferred row). \
Append any new sequencing decisions with fresh IDs, triaged by REVERSIBILITY and \
BLAST RADIUS, not Type label: reversible + obvious default -> Assumed (state the \
default); changes scope/target-users, material/irreversible cost, or compliance/\
legal/data-safety risk -> Open; real but non-blocking -> Deferred. Never \
auto-decide compliance, legal, or genuinely strategic items. Do not put real \
unresolved decisions in "## Assumptions".
- Record what the sequencing takes as true under "## Assumptions".
- Output ONLY the finished markdown artifact, starting with the "# Roadmap" \
heading. No preamble, no explanation, no code fences.
"""

_USER_PROMPT = """\
VISION
======
{vision}

ARCHITECTURE
============
{architecture}

ROADMAP TEMPLATE (fill this skeleton; keep every header verbatim)
================================================================
{template_skeleton}
"""


def build_prompt(vision_doc: str, architecture_doc: str, project: str) -> str:
    """Assemble the user prompt from the Vision, Architecture, and Roadmap skeleton.

    The template's ``{{ project }}`` token is substituted with the project name
    (a literal token, no logic, per `06-decisions.md` D-009).
    """
    skeleton = template_body(_TEMPLATE_KEY).replace("{{ project }}", project)
    return _USER_PROMPT.format(
        vision=vision_doc,
        architecture=architecture_doc,
        template_skeleton=skeleton,
    )


def generate_roadmap(
    config: Config,
    project: str,
    *,
    llm: LLMClient | None = None,
) -> Path:
    """Generate the Roadmap artifact for a project and write it to disk.

    Reads ``projects/<project>/00-vision.md`` and
    ``projects/<project>/01-architecture.md``, fills the Roadmap template via the
    LLM, and writes ``projects/<project>/02-roadmap.md``. Returns the written
    path.

    ``llm`` is injectable so tests can supply a fake; when omitted a real
    :class:`LLMClient` is constructed from ``config``.

    Raises :class:`services.artifacts.ArtifactError` if either upstream artifact
    is missing; no output is written in that case.
    """
    # 1. read upstream (Vision, then Architecture). Missing -> ArtifactError,
    #    before any LLM call. Upstream filenames come from the template registry.
    vision_name, architecture_name = get_template(_TEMPLATE_KEY).upstream
    vision_doc = artifacts.read_artifact(config, project, vision_name)
    architecture_doc = artifacts.read_artifact(config, project, architecture_name)

    # 2. + 3. build prompt and call the LLM
    client = llm if llm is not None else LLMClient(config)
    prompt = build_prompt(vision_doc, architecture_doc, project)
    roadmap_md = client.complete(prompt, system=SYSTEM_PROMPT)

    # 4. write the artifact
    output_filename = get_template(_TEMPLATE_KEY).output_filename
    return artifacts.write_artifact(config, project, output_filename, roadmap_md)
