"""Pattern → issue-ID resolution for plan commands."""

from __future__ import annotations

from desloppify.engine.plan import PlanModel
from desloppify.state import StateModel, match_issues


def _append_unique(fid: str, seen: set[str], result: list[str]) -> None:
    if fid in seen:
        return
    seen.add(fid)
    result.append(fid)


def _collect_plan_ids(plan: PlanModel | None) -> set[str]:
    plan_ids: set[str] = set()
    if plan is None:
        return plan_ids
    plan_ids.update(plan.get("queue_order", []))
    plan_ids.update(plan.get("skipped", {}).keys())
    for cluster in plan.get("clusters", {}).values():
        plan_ids.update(cluster.get("issue_ids", []))
    return plan_ids


def resolve_ids_from_patterns(
    state: StateModel,
    patterns: list[str],
    *,
    plan: PlanModel | None = None,
    status_filter: str = "open",
) -> list[str]:
    """Resolve one or more patterns to a deduplicated list of issue IDs.

    When *plan* is provided, literal IDs that exist only in the plan
    (e.g. ``subjective::*`` synthetic items) are included even if they
    have no corresponding entry in ``state["issues"]``.
    """
    seen: set[str] = set()
    result: list[str] = []
    plan_ids = _collect_plan_ids(plan)

    for pattern in patterns:
        matches = match_issues(state, pattern, status_filter=status_filter)
        if matches:
            for issue in matches:
                _append_unique(issue["id"], seen, result)
            continue
        if pattern in plan_ids:
            # Literal plan ID (e.g. subjective::foo) not in state issues
            _append_unique(pattern, seen, result)
            continue
        if plan is not None and pattern in plan.get("clusters", {}):
            # Cluster name → expand to member IDs
            for fid in plan["clusters"][pattern].get("issue_ids", []):
                _append_unique(fid, seen, result)
    return result


__all__ = ["resolve_ids_from_patterns"]
