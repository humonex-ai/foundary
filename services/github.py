"""Thin GitHub REST client for Execution V1 issue sync.

A minimal wrapper over the GitHub Issues REST API. Side-effecting I/O is isolated
here so the sync logic can be tested against an in-memory fake (no live calls).
``session`` is injectable for the same reason (mirrors ``services.llm``).

Only what issue sync needs: list, create, update body, replace labels. No PRs, no
Projects, no GraphQL, no native dependencies.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

API_BASE = "https://api.github.com"


class GitHubError(RuntimeError):
    """Raised when a GitHub API call fails or returns an unusable response."""


@dataclass
class Issue:
    number: int
    title: str
    body: str
    state: str  # "open" | "closed"
    labels: list[str] = field(default_factory=list)


class GitHubClient:
    """Minimal GitHub Issues client. Inject ``session`` (an httpx.Client-like
    object with ``.request(method, url, headers=, json=)``) in tests."""

    def __init__(self, token: str, *, session: Any | None = None, base_url: str = API_BASE):
        if not token:
            raise GitHubError(
                "GITHUB_TOKEN is not set. Export it or add it to .env "
                "(needs 'issues:write' / repo scope)."
            )
        self._token = token
        self._base = base_url.rstrip("/")
        if session is not None:
            self._session = session
        else:
            import httpx

            self._session = httpx.Client(timeout=30.0)

    # --- public API --------------------------------------------------------

    def list_issues(self, repo: str, *, labels: str | None = None) -> list[Issue]:
        """List issues (all states). Pull requests are filtered out."""
        issues: list[Issue] = []
        page = 1
        while True:
            params = {"state": "all", "per_page": "100", "page": str(page)}
            if labels:
                params["labels"] = labels
            data = self._request("GET", f"/repos/{repo}/issues", params=params)
            if not data:
                break
            for raw in data:
                if "pull_request" in raw:  # the issues endpoint also returns PRs
                    continue
                issues.append(self._to_issue(raw))
            if len(data) < 100:
                break
            page += 1
        return issues

    def create_issue(self, repo: str, *, title: str, body: str, labels: list[str]) -> Issue:
        raw = self._request(
            "POST", f"/repos/{repo}/issues", json={"title": title, "body": body, "labels": labels}
        )
        return self._to_issue(raw)

    def update_issue(self, repo: str, number: int, *, body: str) -> Issue:
        raw = self._request("PATCH", f"/repos/{repo}/issues/{number}", json={"body": body})
        return self._to_issue(raw)

    def set_labels(self, repo: str, number: int, labels: list[str]) -> None:
        """Replace the full label set on an issue (PUT semantics)."""
        self._request("PUT", f"/repos/{repo}/issues/{number}/labels", json={"labels": labels})

    # --- internals ---------------------------------------------------------

    def _to_issue(self, raw: dict) -> Issue:
        return Issue(
            number=raw["number"],
            title=raw.get("title", ""),
            body=raw.get("body") or "",
            state=raw.get("state", "open"),
            labels=[lbl["name"] if isinstance(lbl, dict) else lbl for lbl in raw.get("labels", [])],
        )

    def _request(
        self, method: str, path: str, *, params: dict | None = None, json: dict | None = None
    ) -> Any:
        url = f"{self._base}{path}"
        headers = {
            "Authorization": f"Bearer {self._token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        try:
            resp = self._session.request(method, url, headers=headers, params=params, json=json)
        except Exception as exc:
            raise GitHubError(f"GitHub request failed: {method} {path}: {exc}") from exc

        status = getattr(resp, "status_code", None)
        if status is None or not (200 <= status < 300):
            detail = getattr(resp, "text", "")
            raise GitHubError(f"GitHub API error {status} on {method} {path}: {detail}")
        if method == "PUT" and path.endswith("/labels"):
            return None
        try:
            return resp.json()
        except Exception as exc:
            raise GitHubError(f"GitHub returned non-JSON on {method} {path}: {exc}") from exc
