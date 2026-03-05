"""Central skip-kind policy for plan and CLI behavior."""

from __future__ import annotations

USER_SKIP_KINDS = ("temporary", "permanent", "false_positive")
SYSTEM_SKIP_KINDS = ("triaged_out",)
VALID_SKIP_KINDS = set(USER_SKIP_KINDS + SYSTEM_SKIP_KINDS)

SKIP_KIND_LABELS = {
    "temporary": "Skipped",
    "permanent": "Wontfixed",
    "false_positive": "Marked false positive",
}

SKIP_KIND_SECTION_LABELS = {
    "temporary": "Skipped Temporarily",
    "permanent": "Wontfix (permanent)",
    "false_positive": "False Positives",
}


def skip_kind_from_flags(*, permanent: bool, false_positive: bool) -> str:
    """Map CLI flags to a canonical skip kind."""
    if false_positive:
        return "false_positive"
    if permanent:
        return "permanent"
    return "temporary"


def skip_kind_requires_attestation(kind: str) -> bool:
    """Return True when the skip kind requires attestation text."""
    return kind in {"permanent", "false_positive"}


def skip_kind_requires_note(kind: str) -> bool:
    """Return True when the skip kind requires a user note."""
    return kind == "permanent"


def skip_kind_state_status(kind: str) -> str | None:
    """Return corresponding state status, if any."""
    if kind == "permanent":
        return "wontfix"
    if kind == "false_positive":
        return "false_positive"
    return None


def skip_kind_needs_state_reopen(kind: str) -> bool:
    """Return True when unskip should reopen state-layer status."""
    return kind in {"permanent", "false_positive"}


__all__ = [
    "SKIP_KIND_LABELS",
    "SKIP_KIND_SECTION_LABELS",
    "SYSTEM_SKIP_KINDS",
    "USER_SKIP_KINDS",
    "VALID_SKIP_KINDS",
    "skip_kind_from_flags",
    "skip_kind_needs_state_reopen",
    "skip_kind_requires_attestation",
    "skip_kind_requires_note",
    "skip_kind_state_status",
]
