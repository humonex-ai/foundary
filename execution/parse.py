"""Parse the Work Orders artifact and its Decision List (Execution V1).

Reads the markdown produced by the Work Order agent (`03-work-orders.md`):
- Work Orders: ``### WO-NNN — title`` blocks with bullet fields.
- Decision List: a markdown table with ID / Decision / Owner / Type / Status /
  Blocks / Rationale columns.

Tolerant but strict: raises :class:`ParseError` with a clear message if the
artifact is malformed, rather than emitting a partial result.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

_WO_ID_RE = re.compile(r"WO-\d+")
_WO_HEADING_RE = re.compile(r"^###\s+(WO-\d+)\s*[—\-:]\s*(.+?)\s*$", re.MULTILINE)
# A field bullet like: - **Goal:** value
_FIELD_RE = re.compile(r"^-\s*\*\*([^:*]+):\*\*\s*(.*)$")


class ParseError(RuntimeError):
    """Raised when the Work Orders artifact or Decision List is malformed."""


@dataclass(frozen=True)
class WorkOrder:
    id: str
    title: str
    goal: str = ""
    in_scope: str = ""
    out_of_scope: str = ""
    done_when: str = ""
    depends_on: tuple[str, ...] = ()
    complexity: str = ""
    risk: str = ""


@dataclass(frozen=True)
class Decision:
    id: str
    decision: str
    owner: str
    type: str
    status: str
    blocks: tuple[str, ...]  # WO ids referenced in the Blocks cell
    rationale: str


def _section(markdown: str, header: str) -> str | None:
    """Return the body of a top-level ``## <header>`` section, or None."""
    pattern = re.compile(
        rf"^##\s+{re.escape(header)}\s*$(.*?)(?=^##\s+|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    m = pattern.search(markdown)
    return m.group(1) if m else None


# --- Work Orders -----------------------------------------------------------

def _parse_fields(block: str) -> dict[str, str]:
    """Parse ``- **Field:** value`` bullets in a WO block.

    A field's value runs until the next field bullet or end of block, so
    multi-line values (e.g. a Done-when checklist) are captured whole.
    """
    fields: dict[str, str] = {}
    current: str | None = None
    buf: list[str] = []

    def flush():
        if current is not None:
            fields[current.strip().lower()] = "\n".join(buf).strip()

    for line in block.splitlines():
        m = _FIELD_RE.match(line.strip())
        if m:
            flush()
            current = m.group(1)
            buf = [m.group(2)]
        elif current is not None:
            buf.append(line)
    flush()
    return fields


def parse_work_orders(markdown: str) -> list[WorkOrder]:
    """Parse all Work Orders from a `03-work-orders.md` artifact."""
    matches = list(_WO_HEADING_RE.finditer(markdown))
    if not matches:
        raise ParseError("No Work Orders found (expected '### WO-NNN — title' headings).")

    work_orders: list[WorkOrder] = []
    seen: set[str] = set()
    for i, m in enumerate(matches):
        wo_id, title = m.group(1), m.group(2).strip()
        if wo_id in seen:
            raise ParseError(f"Duplicate Work Order id {wo_id!r}.")
        seen.add(wo_id)

        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(markdown)
        # Stop the last block at the next top-level section if present.
        block = markdown[start:end]
        block = re.split(r"^##\s+", block, maxsplit=1, flags=re.MULTILINE)[0]

        fields = _parse_fields(block)
        depends_raw = fields.get("depends on", "")
        depends = tuple(d for d in _WO_ID_RE.findall(depends_raw) if d != wo_id)

        # Complexity and Risk are often on one bullet ("Complexity: M. Risk: Low.")
        # so extract each directly from the block rather than from a field bullet.
        work_orders.append(
            WorkOrder(
                id=wo_id,
                title=title,
                goal=fields.get("goal", ""),
                in_scope=fields.get("in scope", ""),
                out_of_scope=fields.get("out of scope", ""),
                done_when=fields.get("done when", ""),
                depends_on=depends,
                complexity=_token(block, "Complexity"),
                risk=_token(block, "Risk"),
            )
        )
    return work_orders


def _token(block: str, field_name: str) -> str:
    """Extract the leading word after ``**<field>:**`` anywhere in the block."""
    m = re.search(rf"{field_name}:\*{{0,2}}\s*([A-Za-z]+)", block)
    return m.group(1) if m else ""


# --- Decision List ---------------------------------------------------------

_EXPECTED_COLS = ["id", "decision", "owner", "type", "status", "blocks", "rationale"]


def parse_decisions(markdown: str) -> list[Decision]:
    """Parse the Decision List table. Returns [] if the section has no rows."""
    body = _section(markdown, "Decision List")
    if body is None:
        return []

    rows = [ln.strip() for ln in body.splitlines() if ln.strip().startswith("|")]
    if not rows:
        return []

    # Locate the header row, then skip its separator row.
    header_cells = [c.strip().lower() for c in _split_row(rows[0])]
    if header_cells[: len(_EXPECTED_COLS)] != _EXPECTED_COLS:
        raise ParseError(
            f"Decision List header mismatch. Expected {_EXPECTED_COLS}, got {header_cells}."
        )

    decisions: list[Decision] = []
    for row in rows[1:]:
        if set(row) <= set("|-: "):  # separator row like |---|---|
            continue
        cells = _split_row(row)
        if len(cells) < len(_EXPECTED_COLS):
            raise ParseError(f"Malformed Decision List row: {row!r}")
        did = cells[0].strip()
        if not re.fullmatch(r"D-\d+", did):
            # skip a leftover template placeholder row (e.g. italic example)
            continue
        decisions.append(
            Decision(
                id=did,
                decision=cells[1].strip(),
                owner=cells[2].strip(),
                type=cells[3].strip(),
                status=cells[4].strip(),
                blocks=tuple(_WO_ID_RE.findall(cells[5])),
                rationale=cells[6].strip(),
            )
        )
    return decisions


def _split_row(row: str) -> list[str]:
    """Split a markdown table row into cells (drop leading/trailing pipes)."""
    parts = row.split("|")
    # Drop the empty first/last produced by surrounding pipes.
    if parts and parts[0].strip() == "":
        parts = parts[1:]
    if parts and parts[-1].strip() == "":
        parts = parts[:-1]
    return parts
