# Verdict: S315 — @DavidBuchanan314 — Cross-file write consistency

**Status: PARTIALLY VERIFIED**
**Scores: Sig=4, Orig=4, Core=2, Overall=3**

## Claims assessed

### Claim 1: Non-atomic cross-file writes between state.json and plan.json

**VERIFIED — but mitigated by design.**

The codebase writes state.json and plan.json as separate atomic file operations (each
using temp+rename via `safe_write_text` in `base/discovery/file_paths.py:92`), but there
is no multi-file transaction wrapping both writes together.

Evidence in `cmd_resolve` (`app/commands/resolve/cmd.py`):
- Line 180: `save_state_or_exit(state, state_file)` — state saved first
- Line 182: `_update_living_plan_after_resolve(...)` — plan saved second (line 132)

Evidence in scan workflow (`app/commands/scan/scan_workflow.py`):
- Line 412: `state_mod.save_state(...)` — state saved
- Line 418-424: `_save_config(runtime.config)` — config saved separately
- Line 488-489: `save_plan(plan, plan_path)` — plan saved separately

A crash between these writes would leave state and plan out of sync. However, each
individual file write IS atomic (temp file + `os.replace`), and the system has
self-healing: `reconcile_plan_after_scan` (line 143-225 in `engine/_plan/reconcile.py`)
detects plan references to dead state issues and supersedes them on the next scan.

This is a real gap but low-severity: the window is small (between two atomic writes),
and the next scan heals it automatically.

### Claim 2: Plan save failure silently corrupts state during resolve

**PARTIALLY VERIFIED — mislabeled as "corruption".**

In `_update_living_plan_after_resolve` (`app/commands/resolve/cmd.py:97-138`):
- Line 132: `save_plan(plan)` can fail
- Lines 135-137: failure is caught by `PLAN_LOAD_EXCEPTIONS` and logged as a warning

State was already saved at line 180 (before plan update is attempted). If plan save
fails, state has the resolution recorded but plan still lists the issue in its queue.

This is NOT corruption — state is correct, and the plan is stale. The next scan's
reconciliation will clean up the stale plan references. The warning message at line 137
("could not update living plan") does inform the user, though it goes to stderr and is
easy to miss.

### Claim 3: reconcile_plan_after_scan only heals one direction of divergence

**VERIFIED — but by intentional design, not a bug.**

`reconcile_plan_after_scan` (`engine/_plan/reconcile.py:143-225`) handles only:
- Direction A: Plan references issues that no longer exist/are open in state → supersedes them

It does NOT handle:
- Direction B: State has new issues not referenced in plan → not added to queue

However, direction B is handled by separate functions in the same post-scan workflow:
- `sync_plan_after_review_import` (reconcile.py:237-270) handles new issues after review import
- `sync_unscored_dimensions`, `sync_stale_dimensions`, `sync_triage_needed` all handle
  their respective new-content directions

These are called together in `reconcile_plan_post_scan` (`app/commands/scan/plan_reconcile.py:295-345`)
and in the scan workflow (`scan_workflow.py:440-491`). The separation is deliberate
decomposition, not a missing feature.

## Duplicate check

No prior submissions cover cross-file write atomicity or plan/state consistency gaps.
S309 (@lee101) covered fail-open persistence but focused on backup recovery and
BatchProgressTracker dead code, not multi-file transaction consistency. This is original.

## Summary

The submission identifies a real architectural gap (no multi-file transaction between
state.json and plan.json writes), but overstates its severity:
- Individual file writes are atomic (temp+rename)
- The system self-heals via reconciliation on next scan
- "Corruption" is inaccurate — state remains correct, only plan becomes stale
- The one-direction reconciliation claim is true but is intentional decomposition

The cross-file atomicity gap is a genuine observation worth noting, but the practical
impact is minimal given the self-healing mechanisms in place.
