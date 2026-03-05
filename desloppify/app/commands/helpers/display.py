"""Shared display utilities for command output."""

from __future__ import annotations


def short_issue_id(fid: str) -> str:
    """Extract the 8-char hash suffix from a issue ID for compact display.

    Issue IDs look like ``review::.::holistic::dim::identifier::abcdef12``.
    Commands accept the hash suffix as a shorthand for the full ID.
    """
    if "::" in fid:
        suffix = fid.rsplit("::", 1)[-1]
        if len(suffix) >= 8:
            return suffix[:8]
    return fid


__all__ = ["short_issue_id"]
