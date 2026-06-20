"""Architecture agent (WO-004).

Reuses the agent pattern established by the Vision agent (WO-003):

    1. read the upstream artifact      (the Vision, projects/<p>/00-vision.md)
    2. load the matching template      (services.templates, "architecture")
    3. build a prompt and call the LLM (services.llm)
    4. write the produced artifact     (services.artifacts, 01-architecture.md)

Derives the Architecture from the Vision and nothing more — no roadmap, no work
orders, no orchestration, and no external codebase (Repo Intelligence deferred).
"""

from __future__ import annotations

from pathlib import Path

from services import artifacts
from services.config import Config
from services.llm import LLMClient
from services.templates import get_template, template_body

_TEMPLATE_KEY = "architecture"
_UPSTREAM_KEY = "vision"

SYSTEM_PROMPT = """\
You are the Architecture agent in Foundry, an AI CTO Office. You turn a Vision \
into an Architecture artifact: the shape of a system that delivers the Vision.

Rules:
- Derive the Architecture from the Vision only. You have no access to any \
existing codebase; do not assume one.
- Produce the Architecture only. Do NOT produce a roadmap or work orders.
- Fill the provided template. Keep every "## " section header exactly as given, \
in the same order. Do not add or rename sections.
- Use ONLY technologies named in the Vision's "## Constraints". Never invent a \
NEW stack, framework, library, vendor, or tool the Vision did not name.
- However, choosing a sensible default PARAMETER of a technology the Vision \
ALREADY named is NOT inventing — e.g. a model id when the SDK/provider is named, \
a default file path, a serialization format. Pick a reasonable default, mark it \
Assumed and override-able. The "never invent" rule forbids introducing a new \
tool/vendor/framework; it does NOT force leaving reversible parameters of \
named technologies Open.
- In "## Tech Stack", list the named technologies with their reasons. For an \
unspecified PARAMETER of a named technology, state a sensible default (Assumed). \
Only a genuinely new, unnamed tool stays unresolved — leave that to the Decision \
List as Open, never guessed.
- Maintain the "## Decision List". Carry the Vision's Decision List forward \
VERBATIM — same IDs, same Owner/Type, and same Status (never reopen a row that is \
Decided, Assumed, or Deferred). Append new architecture decisions with fresh IDs \
(continue the numbering). Triage by REVERSIBILITY and BLAST RADIUS, not by Type \
label: reversible + obvious default -> Assumed (state the default); changes \
scope/target-users, material/irreversible cost, or compliance/legal/data-safety \
risk -> Open; real but non-blocking -> Deferred. A default parameter of an \
already-named technology -> Assumed (per the rule above), not Open. Never \
auto-decide compliance, legal, or genuinely strategic items. Do not put real \
unresolved decisions in "## Assumptions".
- Prefer the simplest shape that delivers the Vision. Record options you \
deliberately exclude under "## Boundaries" rather than dropping them silently.
- Record what the architecture takes as true under "## Assumptions".
- Output ONLY the finished markdown artifact, starting with the "# Architecture" \
heading. No preamble, no explanation, no code fences.
"""

_USER_PROMPT = """\
VISION
======
{vision}

ARCHITECTURE TEMPLATE (fill this skeleton; keep every header verbatim)
======================================================================
{template_skeleton}
"""


def build_prompt(vision_doc: str, project: str) -> str:
    """Assemble the user prompt from the Vision and the Architecture skeleton.

    The template's ``{{ project }}`` token is substituted with the project name
    (a literal token, no logic, per `06-decisions.md` D-009).
    """
    skeleton = template_body(_TEMPLATE_KEY).replace("{{ project }}", project)
    return _USER_PROMPT.format(vision=vision_doc, template_skeleton=skeleton)


def generate_architecture(
    config: Config,
    project: str,
    *,
    llm: LLMClient | None = None,
) -> Path:
    """Generate the Architecture artifact for a project and write it to disk.

    Reads ``projects/<project>/00-vision.md``, fills the Architecture template via
    the LLM, and writes ``projects/<project>/01-architecture.md``. Returns the
    written path.

    ``llm`` is injectable so tests can supply a fake; when omitted a real
    :class:`LLMClient` is constructed from ``config``.

    Raises :class:`services.artifacts.ArtifactError` if the Vision is missing;
    no output is written in that case.
    """
    # 1. read upstream (Vision). Missing -> ArtifactError, before any LLM call.
    vision_filename = get_template(_UPSTREAM_KEY).output_filename
    vision_doc = artifacts.read_artifact(config, project, vision_filename)

    # 2. + 3. build prompt and call the LLM
    client = llm if llm is not None else LLMClient(config)
    prompt = build_prompt(vision_doc, project)
    architecture_md = client.complete(prompt, system=SYSTEM_PROMPT)

    # 4. write the artifact
    output_filename = get_template(_TEMPLATE_KEY).output_filename
    return artifacts.write_artifact(config, project, output_filename, architecture_md)
