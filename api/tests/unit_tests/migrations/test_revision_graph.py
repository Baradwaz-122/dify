from __future__ import annotations

import ast
import re
from pathlib import Path

_VERSIONS_DIR = Path(__file__).resolve().parents[3] / "migrations/versions"
_REVISION_RE = re.compile(r"^revision(?:\s*:\s*str)?\s*=\s*['\"]([^'\"]+)['\"]", re.MULTILINE)
_DOWN_REVISION_RE = re.compile(r"^down_revision\s*=\s*(.+)$", re.MULTILINE)


def _parse_down_revision(raw: str) -> tuple[str, ...]:
    value = ast.literal_eval(raw.strip())
    if value is None:
        return ()
    if isinstance(value, tuple):
        return tuple(str(item) for item in value)
    return (str(value),)


def _load_revision_graph() -> tuple[dict[str, Path], dict[str, tuple[str, ...]]]:
    revisions: dict[str, Path] = {}
    parents: dict[str, tuple[str, ...]] = {}
    for path in _VERSIONS_DIR.glob("*.py"):
        content = path.read_text()
        revision_match = _REVISION_RE.search(content)
        down_match = _DOWN_REVISION_RE.search(content)
        if revision_match is None or down_match is None:
            continue
        revision = revision_match.group(1)
        revisions[revision] = path
        parents[revision] = _parse_down_revision(down_match.group(1))
    return revisions, parents


def test_every_down_revision_exists() -> None:
    revisions, parents = _load_revision_graph()
    missing = sorted(
        {
            parent
            for down_revisions in parents.values()
            for parent in down_revisions
            if parent not in revisions
        }
    )
    assert missing == [], f"migration graph references missing revisions: {missing}"
