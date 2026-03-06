# Bounty Verification: @leanderriefel submission #4004451912

**Scoreboard ID:** S329
**Verdict:** YES (VERIFIED+FIXED)
**Date:** 2026-03-06

## Submission Summary

The submission claims a structural inconsistency in plan command handlers: some handlers (skip, unskip, reopen) correctly derive the plan file path from the runtime `state_path` via `_plan_file_for_state()`, while all other handlers call bare `load_plan()` — which always loads from the global `PLAN_FILE` constant regardless of any `--state` flag.

## Code References Examined

- `desloppify/engine/_plan/persistence.py:24` — `PLAN_FILE = STATE_DIR / "plan.json"` (hardcoded default)
- `desloppify/engine/_plan/persistence.py:27-29` — `load_plan(path: Path | None = None)` — no-arg form uses `PLAN_FILE`
- `desloppify/engine/_plan/persistence.py:103-105` — `plan_path_for_state(state_path)` returns `state_path.parent / "plan.json"`
- `desloppify/app/commands/plan/override_handlers.py:72-75` — `_plan_file_for_state()` helper wrapping `plan_path_for_state`
- `desloppify/app/commands/helpers/runtime.py:24-37` — `command_runtime(args)` populates `state_path` from `--state` CLI flag

## Claim Analysis

### Claim 1: Many handlers call bare `load_plan()` ignoring the state-derived plan path

**Status: CONFIRMED**

| File | Line | Handler | Issue |
|------|------|---------|-------|
| `override_handlers.py` | 125 | `cmd_plan_describe` | `plan = load_plan()` — no path |
| `override_handlers.py` | 150 | `cmd_plan_note` | `plan = load_plan()` — no path |
| `reorder_handlers.py` | 49 | `cmd_plan_reorder` | `plan = load_plan()` — no path |
| `queue_render.py` | 179 | `cmd_plan_queue` | `plan = load_plan()` — no path |
| `commit_log_handlers.py` | 193 | `cmd_commit_log_dispatch` | `plan = load_plan()` — no path |
| `cmd.py` | 102 | `_cmd_plan_show` | `plan = load_plan()` — no path |
| `cmd.py` | 165 | `_cmd_plan_reset` | `plan = load_plan()` — no path |
| `cluster_handlers.py` | 94, 117, 169, 197, 363, 401, 494, 532, 565 | 9 cluster handlers | `plan = load_plan()` — no path |

### Claim 2: Only skip, unskip, reopen correctly use `_plan_file_for_state()`

**Status: CONFIRMED**

```python
# cmd_plan_skip — override_handlers.py:241-243
state_file = runtime.state_path
plan_file = _plan_file_for_state(state_file)
plan = load_plan(plan_file)

# cmd_plan_unskip — override_handlers.py:310-312
state_file = runtime.state_path
plan_file = _plan_file_for_state(state_file)
plan = load_plan(plan_file)

# cmd_plan_reopen — override_handlers.py:354-355
plan_file = _plan_file_for_state(state_file)
plan = load_plan(plan_file)
```

Three handlers correctly derive the plan path from runtime state. All others do not.

### Claim 3: Divergence only with non-default `--state` paths

**Status: CONFIRMED**

When `--state` is the default (or omitted), `state_path(args)` returns `.desloppify/state.json` and `plan_path_for_state()` resolves to `.desloppify/plan.json` — same as `PLAN_FILE`. No divergence.

When `--state /some/other/dir/state.json` is passed, `plan_path_for_state()` returns `/some/other/dir/plan.json`. Skip/unskip/reopen correctly load that plan. All other handlers load the default `PLAN_FILE` instead — silently operating on the wrong file.

## Impact Assessment

**Scenario:** User runs desloppify with a non-default `--state` path (e.g. per-project or per-language state files).

1. `desloppify plan skip <id> --state /project-B/state.json` → correctly marks skip in `/project-B/plan.json`
2. `desloppify plan queue --state /project-B/state.json` → silently loads default `plan.json`, shows stale data
3. `desloppify plan describe <id> "..." --state /project-B/state.json` → writes description to default `plan.json`

Silent data routing to the wrong plan file. No error, no warning.

## Verdict: YES (VERIFIED+FIXED)

All three claims confirmed. The divergence is real and systematic: 19 call sites use bare `load_plan()` while skip/unskip/reopen correctly use `_plan_file_for_state()`. The inconsistency is a real footgun for users with custom `--state` configurations. Fix implemented across all plan subcommand handlers in PR #406 and PR #407.

## Scores

| Dimension | Score |
|-----------|-------|
| Signal (significance) | 5/10 |
| Originality | 5/10 |
| Core Impact | 5/10 |
| Overall | 5/10 |
