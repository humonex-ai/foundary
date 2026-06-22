# Foundry skills

## `foundry-spec`
Turns a matured idea into validated Foundry artifacts, then routes them into
Foundry (via the MCP if connected, else emits files for local `foundry submit`).
Self-contained — bundles the full artifact templates **and** the per-artifact
authoring rules, so it works without the MCP.

### Bundled references are generated — don't hand-edit
`foundry-spec/references/*.md` are snapshots built from the repo's authoritative
sources (`templates/`, `agents/*.py` system prompts, `docs/01-principles.md`).
Regenerate after changing any of those:
```bash
python skills/build_references.py
```
With the Foundry MCP connected, `get_templates` is the live source for templates;
the bundle is the offline fallback for web / ChatGPT and the only source of the
authoring rules.

### Install per surface

**Claude Code / Desktop (personal):**
```bash
cp -r skills/foundry-spec ~/.claude/skills/foundry-spec
```
Then in a session the skill auto-loads when you ask to "make this a Foundry
project". Pair it with the Foundry MCP for the full submit → approve → sync loop:
```bash
claude mcp add --scope user foundry -- uvx --from git+https://github.com/humonex-ai/foundary.git@v0.1.1 foundry-mcp
```

**Claude Code (this project only):**
```bash
mkdir -p .claude/skills && cp -r skills/foundry-spec .claude/skills/
```

**Claude web (claude.ai) — upload as a Skill:**
```bash
cd skills && zip -r foundry-spec.zip foundry-spec
```
Upload `foundry-spec.zip` in Settings → Capabilities → Skills (needs a plan with
Skills + code execution). Runs ideation + authoring; materialize via Branch B
(emits files to submit locally), since the local Foundry MCP isn't reachable from
the web.

**How to call it on Claude web:** there is no `/slash` command — skills are
auto-invoked by description match. Just describe the task in a chat: "Make this a
Foundry project", "Write the Foundry project spec for <idea>". The skill authors
the four artifacts as labeled code blocks; save them to a folder and run
`foundry submit <name> --dir <folder>` locally to validate + record, then approve
and `sync_github` via the MCP in Claude Code.

**ChatGPT — no native Skills.** Closest equivalent: a Custom GPT (or a Project's
custom instructions). Paste `foundry-spec/SKILL.md` as the instructions and
upload **both** reference files as knowledge —
`foundry-spec/references/templates.md` **and**
`foundry-spec/references/authoring-rules.md`. SKILL.md mandates reading the
authoring rules on every surface, so omitting `authoring-rules.md` strips the
per-artifact guidance and you only get bare skeletons. Materialize via Branch B.
