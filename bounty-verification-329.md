# Bounty Verification Report — S329

**Submission**: @leanderriefel — Split-brain plan persistence (`plan` ignores its own state scoping contract)
**Verifier**: lota-1
**Date**: 2026-03-05

---

## Status: PARTIALLY VERIFIED

The core observation is correct — there is an inconsistency in how plan handlers resolve the plan file path. However, the submission contains inaccurate line references for one file, and the practical impact is limited to the uncommon `--state` flag usage.

## Evidence

### Verified claims

1. **`--state` on plan CLI**: `parser_groups_plan_impl.py:361` — Confirmed. The plan command accepts `--state`.

2. **Runtime carries resolved state path**: `runtime.py:24-37` — Confirmed. `CommandRuntime` has `state_path` field, populated from args.

3. **Plan persistence supports both models**:
   - Global default at `persistence.py:24` (`PLAN_FILE = STATE_DIR / "plan.json"`) and `persistence.py:27-29` (default in `load_plan`) — Confirmed.
   - State-derived helper at `persistence.py:103-105` (`plan_path_for_state`) — Confirmed.

4. **State-scoped handlers** (correctly derive plan path from state):
   - `override_handlers.py:233-235` (`cmd_plan_skip`) — Confirmed. Uses `_plan_file_for_state(state_file)`.
   - `override_handlers.py:302-304` (`cmd_plan_unskip`) — Confirmed. Same pattern.
   - `override_handlers.py:347,360` (`cmd_plan_reopen`) — Also state-scoped (not mentioned in submission).

5. **Global-only handlers** (ignore `--state`, always use default PLAN_FILE):
   - `cmd.py:88` (`_cmd_plan_show`) — Confirmed: `plan = load_plan()`.
   - `reorder_handlers.py:49` (`cmd_plan_reorder`) — Confirmed: `plan = load_plan()`.
   - `queue_render.py:179` (`cmd_plan_queue`) — Confirmed: `plan = load_plan()`.
   - `cmd.py:152` (`_cmd_plan_reset`) — Also global (not mentioned).
   - `override_handlers.py:117` (`cmd_plan_describe`) — Also global (not mentioned).
   - `override_handlers.py:142` (`cmd_plan_note`) — Also global (not mentioned).
   - `override_handlers.py:591` (`cmd_plan_focus`) — Also global (not mentioned).

### Inaccurate claims

- **`commit_log_handlers.py:119,171`**: These lines are `state_mod.load_state()` calls, NOT `load_plan()`. The actual global `load_plan()` in that file is at **line 193** (`cmd_commit_log_dispatch`). The submission cited wrong line numbers for this file.

## Accuracy

File paths are all correct. Line numbers are mostly accurate (5/6 files), with `commit_log_handlers.py` having incorrect line references. The submission also missed several additional global-only handlers (`describe`, `note`, `focus`, `reset`) which would have strengthened the case.

## Assessment

- **Significance: 5/10** — Real inconsistency, but only manifests when `--state` is used with a non-default path, which is an uncommon workflow. In the default case (no `--state`), both code paths resolve to the same file.

- **Originality: 5/10** — Requires tracing data flow across multiple files and understanding the dual-path design. Not immediately obvious, but follows from a straightforward "grep for load_plan calls" analysis.

- **Core Impact: 2/10** — Does not affect gaming-resistant scoring. Plan data (queue ordering, clusters, skips) is a convenience layer on top of state. The scoring engine reads from state, not plan. A split-brain plan would cause confusing UX (e.g., reorder not sticking when viewed via queue), but would not compromise score integrity.

- **Overall Score: 4/10** — Valid finding with real inconsistency, but limited practical impact. The `--state` flag is a power-user feature for multi-state workflows that most users won't encounter. The submission slightly oversells the severity ("split-brain" implies data corruption risk, but in practice it's a UX inconsistency for an edge-case workflow).

## One-line Verdict

Real but low-impact inconsistency: plan handlers mix state-scoped and global plan paths, but only matters for the rarely-used `--state` flag and doesn't affect scoring integrity.
