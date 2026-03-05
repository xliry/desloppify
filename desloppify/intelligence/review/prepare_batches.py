"""Holistic investigation batch builders for review preparation.

Each batch builder returns exactly ONE batch with exactly ONE dimension.
This ensures one prompt per dimension after explosion (which becomes a no-op).
"""

from __future__ import annotations

from pathlib import Path

from desloppify.intelligence.review._context.models import HolisticContext

_EXTENSIONLESS_FILENAMES = {
    "makefile",
    "dockerfile",
    "readme",
    "license",
    "build",
    "workspace",
}


def _normalize_file_path(value: object) -> str | None:
    """Normalize/validate candidate file paths for batch payloads."""
    if not isinstance(value, str):
        return None
    text = value.strip().strip(",'\"")
    if not text or text in {".", ".."}:
        return None
    if text.endswith("/"):
        return None

    basename = Path(text).name
    if not basename:
        return None
    if "." not in basename and basename.lower() not in _EXTENSIONLESS_FILENAMES:
        return None
    return text


def _collect_unique_files(
    sources: list[list[dict]],
    key: str = "file",
    *,
    max_files: int | None = None,
) -> list[str]:
    """Collect unique file paths from multiple source lists."""
    seen: set[str] = set()
    out: list[str] = []
    for src in sources:
        for item in src:
            f = _normalize_file_path(item.get(key, ""))
            if f and f not in seen:
                seen.add(f)
                out.append(f)
                if max_files is not None and len(out) >= max_files:
                    return out
    return out



def _collect_files_from_batches(
    batches: list[dict], *, max_files: int | None = None
) -> list[str]:
    """Collect unique file paths across batch payloads (preserving order)."""
    seen: set[str] = set()
    out: list[str] = []
    for batch in batches:
        for filepath in batch.get("files_to_read", []):
            normalized = _normalize_file_path(filepath)
            if not normalized:
                continue
            if normalized in seen:
                continue
            seen.add(normalized)
            out.append(normalized)
            if max_files is not None and len(out) >= max_files:
                return out
    return out


def _representative_files_for_directory(
    ctx: HolisticContext,
    directory: str,
    *,
    max_files: int = 3,
) -> list[str]:
    """Map a directory-level signal to representative file paths."""
    if not isinstance(directory, str) or not directory.strip():
        return []

    dir_key = directory.strip()
    if dir_key in {".", "./"}:
        normalized_dir = "."
    else:
        normalized_dir = f"{dir_key.rstrip('/')}/"

    profiles = ctx.structure.get("directory_profiles", {})
    profile = profiles.get(normalized_dir)
    if not isinstance(profile, dict):
        return []

    out: list[str] = []
    for filename in profile.get("files", []):
        if not isinstance(filename, str) or not filename:
            continue
        filepath = (
            filename
            if normalized_dir == "."
            else f"{normalized_dir.rstrip('/')}/{filename}"
        )
        normalized = _normalize_file_path(filepath)
        if not normalized or normalized in out:
            continue
        out.append(normalized)
        if len(out) >= max_files:
            break
    return out


# ---------------------------------------------------------------------------
# Seed file collectors — shared across dimension batches
# ---------------------------------------------------------------------------

def _arch_coupling_files(ctx: HolisticContext, *, max_files: int | None = None) -> list[str]:
    """Files relevant to architecture/coupling dimensions."""
    return _collect_unique_files(
        [
            ctx.architecture.get("god_modules", []),
            ctx.coupling.get("module_level_io", []),
            ctx.coupling.get("boundary_violations", []),
            ctx.dependencies.get("deferred_import_density", []),
        ],
        max_files=max_files,
    )


def _conventions_files(ctx: HolisticContext, *, max_files: int | None = None) -> list[str]:
    """Files relevant to conventions/errors dimensions."""
    sibling = ctx.conventions.get("sibling_behavior", {})
    outlier_files = [
        {"file": o["file"]} for di in sibling.values() for o in di.get("outliers", [])
    ]
    error_dirs = ctx.errors.get("strategy_by_directory", {})
    mixed_dir_files: list[dict[str, str]] = []
    for directory, strategies in error_dirs.items():
        if not isinstance(strategies, dict) or len(strategies) < 3:
            continue
        for filepath in _representative_files_for_directory(ctx, directory):
            mixed_dir_files.append({"file": filepath})

    exception_files = [
        {"file": item.get("file", "")}
        for item in ctx.errors.get("exception_hotspots", [])
        if isinstance(item, dict)
    ]
    dupe_files = [
        {"file": item.get("files", [""])[0]}
        for item in ctx.conventions.get("duplicate_clusters", [])
        if isinstance(item, dict) and item.get("files")
    ]
    naming_drift_files: list[dict[str, str]] = []
    for entry in ctx.conventions.get("naming_drift", []):
        if isinstance(entry, dict):
            directory = entry.get("directory", "")
            for filepath in _representative_files_for_directory(ctx, directory):
                naming_drift_files.append({"file": filepath})

    return _collect_unique_files(
        [outlier_files, mixed_dir_files, exception_files, dupe_files, naming_drift_files],
        max_files=max_files,
    )


def _abstractions_files(ctx: HolisticContext, *, max_files: int | None = None) -> list[str]:
    """Files relevant to abstractions/dependencies dimensions."""
    util_files = ctx.abstractions.get("util_files", [])
    wrapper_files = [
        {"file": item.get("file", "")}
        for item in ctx.abstractions.get("pass_through_wrappers", [])
        if isinstance(item, dict)
    ]
    indirection_files = [
        {"file": item.get("file", "")}
        for item in ctx.abstractions.get("indirection_hotspots", [])
        if isinstance(item, dict)
    ]
    param_bag_files = [
        {"file": item.get("file", "")}
        for item in ctx.abstractions.get("wide_param_bags", [])
        if isinstance(item, dict)
    ]
    interface_files: list[dict[str, str]] = []
    for item in ctx.abstractions.get("one_impl_interfaces", []):
        if not isinstance(item, dict):
            continue
        for group in ("declared_in", "implemented_in"):
            for filepath in item.get(group, []):
                interface_files.append({"file": filepath})

    delegation_files = [
        {"file": item.get("file", "")}
        for item in ctx.abstractions.get("delegation_heavy_classes", [])
        if isinstance(item, dict)
    ]
    facade_files = [
        {"file": item.get("file", "")}
        for item in ctx.abstractions.get("facade_modules", [])
        if isinstance(item, dict)
    ]
    type_violation_files = [
        {"file": item.get("file", "")}
        for item in ctx.abstractions.get("typed_dict_violations", [])
        if isinstance(item, dict)
    ]
    complexity_files = [
        {"file": item.get("file", "")}
        for item in ctx.abstractions.get("complexity_hotspots", [])
        if isinstance(item, dict)
    ]
    cycle_files: list[dict] = []
    for summary in ctx.dependencies.get("cycle_summaries", []):
        for token in summary.split():
            if "/" in token and "." in token:
                cycle_files.append({"file": token.strip(",'\"")})

    return _collect_unique_files(
        [
            util_files, wrapper_files, indirection_files, param_bag_files,
            interface_files, delegation_files, facade_files,
            type_violation_files, complexity_files, cycle_files,
        ],
        max_files=max_files,
    )


def _testing_api_files(ctx: HolisticContext, *, max_files: int | None = None) -> list[str]:
    """Files relevant to testing/API dimensions."""
    critical = ctx.testing.get("critical_untested", [])
    sync_async = [{"file": f} for f in ctx.api_surface.get("sync_async_mix", [])]
    return _collect_unique_files([critical, sync_async], max_files=max_files)


def _authorization_files(ctx: HolisticContext, *, max_files: int | None = None) -> list[str]:
    """Files relevant to authorization dimension."""
    auth_ctx = ctx.authorization
    auth_files: list[dict] = []
    for rpath, info in auth_ctx.get("route_auth_coverage", {}).items():
        if info.get("without_auth", 0) > 0:
            auth_files.append({"file": rpath})
    for rpath in auth_ctx.get("service_role_usage", []):
        auth_files.append({"file": rpath})
    rls_coverage = auth_ctx.get("rls_coverage", {})
    rls_files = rls_coverage.get("files", {})
    if isinstance(rls_files, dict):
        for _table, file_paths in rls_files.items():
            if isinstance(file_paths, list):
                for fpath in file_paths:
                    auth_files.append({"file": fpath})
    return _collect_unique_files([auth_files], max_files=max_files)


def _ai_debt_files(ctx: HolisticContext, *, max_files: int | None = None) -> list[str]:
    """Files relevant to AI debt/migration dimensions."""
    ai_debt = ctx.ai_debt_signals
    migration = ctx.migration_signals
    debt_files: list[dict] = []
    for rpath in ai_debt.get("file_signals", {}):
        debt_files.append({"file": rpath})
    dep_files = migration.get("deprecated_markers", {}).get("files")
    if isinstance(dep_files, dict):
        for entry in dep_files:
            debt_files.append({"file": entry})
    for entry in migration.get("migration_todos", []):
        debt_files.append({"file": entry.get("file", "")})
    return _collect_unique_files([debt_files], max_files=max_files)


def _package_org_files(ctx: HolisticContext, *, max_files: int | None = None) -> list[str]:
    """Files relevant to package organization dimensions."""
    structure = ctx.structure
    struct_files: list[dict] = []
    for entry in structure.get("flat_dir_issues", []):
        if isinstance(entry, dict):
            directory = entry.get("directory", "")
            for filepath in _representative_files_for_directory(ctx, directory):
                struct_files.append({"file": filepath})
    for rf in structure.get("root_files", []):
        if rf.get("role") == "peripheral":
            struct_files.append({"file": rf["file"]})
    dir_profiles = structure.get("directory_profiles", {})
    largest_dirs = sorted(
        dir_profiles.items(), key=lambda x: -x[1].get("file_count", 0)
    )[:3]
    for dir_key, profile in largest_dirs:
        for fname in profile.get("files", [])[:3]:
            dir_path = dir_key.rstrip("/")
            rpath = f"{dir_path}/{fname}" if dir_path != "." else fname
            struct_files.append({"file": rpath})
    coupling_matrix = structure.get("coupling_matrix", {})
    seen_edges: set[str] = set()
    for edge in coupling_matrix:
        if " → " in edge:
            a, b = edge.split(" → ", 1)
            reverse = f"{b} → {a}"
            if reverse in coupling_matrix and edge not in seen_edges:
                seen_edges.add(edge)
                seen_edges.add(reverse)
                for d in (a, b):
                    for fname in dir_profiles.get(d, {}).get("files", [])[:2]:
                        dir_path = d.rstrip("/")
                        rpath = f"{dir_path}/{fname}" if dir_path != "." else fname
                        struct_files.append({"file": rpath})
    return _collect_unique_files([struct_files], max_files=max_files)


def _state_design_files(ctx: HolisticContext, *, max_files: int | None = None) -> list[str]:
    """Files relevant to state/design integrity dimensions."""
    evidence = ctx.scan_evidence
    mutable_files = [
        item for item in evidence.get("mutable_globals", [])
        if isinstance(item, dict)
    ]
    complexity_files = [
        item for item in evidence.get("complexity_hotspots", [])[:10]
        if isinstance(item, dict)
    ]
    error_files = [
        item for item in evidence.get("error_hotspots", [])[:10]
        if isinstance(item, dict)
    ]
    density_files = [
        {"file": item["file"]}
        for item in evidence.get("signal_density", [])[:10]
        if isinstance(item, dict) and item.get("file")
    ]
    return _collect_unique_files(
        [mutable_files, complexity_files, error_files, density_files],
        max_files=max_files,
    )


# ---------------------------------------------------------------------------
# Dimension → seed file mapping.  Each dimension appears EXACTLY ONCE.
# ---------------------------------------------------------------------------

_DIMENSION_FILE_MAPPING: dict[str, str] = {
    # dimension_name → file collector function name suffix
    "cross_module_architecture": "arch_coupling",
    "high_level_elegance": "package_org",
    "convention_outlier": "conventions",
    "error_consistency": "conventions",
    "naming_quality": "conventions",
    "abstraction_fitness": "abstractions",
    "dependency_health": "abstractions",
    "low_level_elegance": "abstractions",
    "mid_level_elegance": "package_org",
    "test_strategy": "testing_api",
    "api_surface_coherence": "testing_api",
    "authorization_consistency": "authorization",
    "ai_generated_debt": "ai_debt",
    "incomplete_migration": "ai_debt",
    "package_organization": "package_org",
    "initialization_coupling": "state_design",
    "design_coherence": "state_design",
    "contract_coherence": "abstractions",
    "logic_clarity": "abstractions",
    "type_safety": "abstractions",
}

_FILE_COLLECTORS = {
    "arch_coupling": _arch_coupling_files,
    "conventions": _conventions_files,
    "abstractions": _abstractions_files,
    "testing_api": _testing_api_files,
    "authorization": _authorization_files,
    "ai_debt": _ai_debt_files,
    "package_org": _package_org_files,
    "state_design": _state_design_files,
}


def _ensure_holistic_context(holistic_ctx: HolisticContext | dict) -> HolisticContext:
    if isinstance(holistic_ctx, HolisticContext):
        return holistic_ctx
    return HolisticContext.from_raw(holistic_ctx)


def build_investigation_batches(
    holistic_ctx: HolisticContext | dict,
    lang: object,
    *,
    repo_root: Path | None = None,
    max_files_per_batch: int | None = None,
) -> list[dict]:
    """Build one batch per dimension from holistic context.

    Each batch has exactly one dimension and its relevant seed files.
    """
    ctx = _ensure_holistic_context(holistic_ctx)
    del lang  # Reserved for future language-specific batch shaping.

    # Cache file collector results so we don't recompute for shared collectors
    file_cache: dict[str, list[str]] = {}
    batches: list[dict] = []

    for dimension, collector_key in _DIMENSION_FILE_MAPPING.items():
        if collector_key not in file_cache:
            collector = _FILE_COLLECTORS[collector_key]
            file_cache[collector_key] = collector(
                ctx, max_files=max_files_per_batch
            )

        files = file_cache[collector_key]
        if not files:
            continue

        batches.append({
            "name": dimension,
            "dimensions": [dimension],
            "files_to_read": files,
            "why": f"seed files for {dimension} review",
        })

    return batches


def filter_batches_to_dimensions(
    batches: list[dict],
    dimensions: list[str],
    *,
    fallback_max_files: int | None = 80,
) -> list[dict]:
    """Keep only batches whose dimension is in the active set.

    For dimensions not covered by any batch, create a single-dimension
    fallback batch using representative files from other batches.
    """
    selected = [d for d in dimensions if isinstance(d, str) and d]
    if not selected:
        return []
    selected_set = set(selected)
    filtered: list[dict] = []
    covered: set[str] = set()
    for batch in batches:
        batch_dims = [dim for dim in batch.get("dimensions", []) if dim in selected_set]
        if not batch_dims:
            continue
        filtered.append({**batch, "dimensions": batch_dims})
        covered.update(batch_dims)

    missing = [dim for dim in selected if dim not in covered]
    if not missing:
        return filtered

    max_files = fallback_max_files if isinstance(fallback_max_files, int) else None
    if isinstance(max_files, int) and max_files <= 0:
        max_files = None
    fallback_files = _collect_files_from_batches(filtered or batches, max_files=max_files)
    if not fallback_files:
        return filtered

    # One fallback batch per missing dimension (not one batch with all missing)
    for dim in missing:
        filtered.append({
            "name": dim,
            "dimensions": [dim],
            "files_to_read": fallback_files,
            "why": f"no direct batch mapping for {dim}; using representative files",
        })
    return filtered


def batch_concerns(
    concerns: list,
    *,
    max_files: int | None = None,
    active_dimensions: list[str] | None = None,
) -> dict | None:
    """Build investigation batch from mechanical concern signals.

    Returns a single batch with dimension ``design_coherence``.
    Concern signals are attached as extra context for the reviewer.
    """
    if not concerns:
        return None

    types = sorted({c.type for c in concerns if c.type})
    why_parts = ["mechanical detectors identified structural patterns needing judgment"]
    if types:
        why_parts.append(f"concern types: {', '.join(types)}")

    files: list[str] = []
    seen: set[str] = set()
    concern_signals: list[dict[str, object]] = []
    for concern in concerns:
        candidate = _normalize_file_path(getattr(concern, "file", ""))
        if not candidate or candidate in seen:
            continue
        seen.add(candidate)
        files.append(candidate)

        evidence_raw = getattr(concern, "evidence", ())
        evidence = [
            str(entry).strip()
            for entry in evidence_raw
            if isinstance(entry, str) and entry.strip()
        ][:4]
        summary = str(getattr(concern, "summary", "")).strip()
        question = str(getattr(concern, "question", "")).strip()
        concern_type = str(getattr(concern, "type", "")).strip()
        concern_signals.append(
            {
                "type": concern_type or "design_concern",
                "file": candidate,
                "summary": summary or "Mechanical concern requires subjective judgment",
                "question": question or "Is this pattern intentional or debt?",
                "evidence": evidence,
            }
        )

    total_candidate_files = len(files)
    if (
        max_files is not None
        and isinstance(max_files, int)
        and max_files > 0
        and total_candidate_files > max_files
    ):
        files = files[:max_files]
        why_parts.append(
            f"truncated to {max_files} files from {total_candidate_files} candidates"
        )

    return {
        "name": "design_coherence",
        "dimensions": ["design_coherence"],
        "files_to_read": files,
        "why": "; ".join(why_parts),
        "total_candidate_files": total_candidate_files,
        "concern_signals": concern_signals[:12],
        "concern_signal_count": len(concern_signals),
    }


__all__ = ["batch_concerns", "build_investigation_batches", "filter_batches_to_dimensions"]
