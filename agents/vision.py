"""Vision agent (WO-003) — the first agent, establishing the agent pattern.

The pattern every artifact agent follows (`07-agent-catalog.md`):

    1. read + validate the upstream artifact(s)   (services.product_input here)
    2. load the matching template skeleton          (services.templates)
    3. build a prompt and call the LLM              (services.llm)
    4. write the produced artifact to the project   (services.artifacts)

The Vision agent turns a Product Input into a Vision artifact and nothing more —
no architecture, roadmap, or work orders, and no orchestration (those are other
work orders). Kept deliberately simple; WO-004..006 reuse this shape.
"""

from __future__ import annotations

from pathlib import Path

from services import artifacts, product_input
from services.config import Config
from services.llm import LLMClient
from services.templates import get_template, template_body

_TEMPLATE_KEY = "vision"

SYSTEM_PROMPT = """\
You are the Vision agent in Foundry, an AI CTO Office. You turn a Product Input \
into a Vision artifact: a clear statement of what is being built and why.

Rules:
- Produce the Vision only. Do NOT propose architecture, a roadmap, or work orders.
- Fill the provided template. Keep every "## " section header exactly as given, \
in the same order. Do not add or rename sections.
- Derive every section from the Product Input. Do not invent facts that \
contradict it.
- Preserve the Product Input's "## Constraints" faithfully in the Vision's \
"## Constraints" section. Carry hard limits — technology/stack, interface, \
storage, budget, team, regulatory — through verbatim in substance. Never drop \
them; the Architecture stage depends on them surviving.
- Build the "## Decision List" — the single home for decisions (an Open Question \
is a Decision with Status = Open). Seed it from the Product Input's "## Open \
Questions", one triaged row each, with stable IDs (D-001, D-002, …). For every \
row set: ID, Decision, Owner (Founder/Product/Architect/Engineer/Compliance/\
Legal), Type (Product/Technical/Compliance/Legal/Operational), Status, Blocks \
(WO id or —), Rationale. Triage rules:
    * Triage by REVERSIBILITY and BLAST RADIUS, not by the Type label. If a \
decision is reversible, low-cost to change later, and has an obvious sensible \
default, mark it Assumed and state the default in Rationale — EVEN IF its Type \
is Product. Keep it Open only when it changes scope or target users, incurs \
material or irreversible cost, or carries compliance/legal/data-safety risk. \
"Major product strategy" means high blast radius, not merely Type = Product.
    * Trivial, low-risk, reversible defaults -> Status = Assumed, with the chosen \
default stated in Rationale. Do NOT surface these as Open.
    * Real but not-yet-blocking decisions -> Status = Deferred.
    * Anything the Product Input's Constraints already settle -> Status = Decided \
(do not reopen it).
    * NEVER auto-decide a compliance, legal, or genuinely strategic (high blast \
radius) item — those stay Open.
    Do not put real unresolved decisions in "## Assumptions".
- Stay at the vision altitude — no components, no schedule, no tasks.
- Output ONLY the finished markdown artifact, starting with the "# Vision" \
heading. No preamble, no explanation, no code fences.
"""

_USER_PROMPT = """\
PRODUCT INPUT
=============
{product_input}

VISION TEMPLATE (fill this skeleton; keep every header verbatim)
================================================================
{template_skeleton}
"""


def build_prompt(product_input_doc: str, project: str) -> str:
    """Assemble the user prompt from the Product Input and the Vision skeleton.

    The template's ``{{ project }}`` token is substituted with the project name.
    Substitution is kept to a literal token (no logic), per `06-decisions.md`
    D-009.
    """
    skeleton = template_body(_TEMPLATE_KEY).replace("{{ project }}", project)
    return _USER_PROMPT.format(
        product_input=product_input_doc,
        template_skeleton=skeleton,
    )


def generate_vision(
    config: Config,
    project: str,
    *,
    llm: LLMClient | None = None,
) -> Path:
    """Generate the Vision artifact for a project and write it to disk.

    Reads and validates ``projects/<project>/product-input.md``, fills the Vision
    template via the LLM, and writes ``projects/<project>/vision.md``. Returns the
    written path.

    ``llm`` is injectable so tests can supply a fake; when omitted a real
    :class:`LLMClient` is constructed from ``config``.

    Raises :class:`services.artifacts.ArtifactError` if the Product Input is
    missing, or :class:`services.product_input.ProductInputError` if it fails
    structural validation. Neither writes any output.
    """
    # 1. read + validate upstream
    product_input_doc = product_input.load_and_validate(config, project)

    # 2. + 3. build prompt and call the LLM
    client = llm if llm is not None else LLMClient(config)
    prompt = build_prompt(product_input_doc, project)
    vision_md = client.complete(prompt, system=SYSTEM_PROMPT)

    # 4. write the artifact
    output_filename = get_template(_TEMPLATE_KEY).output_filename
    return artifacts.write_artifact(config, project, output_filename, vision_md)
