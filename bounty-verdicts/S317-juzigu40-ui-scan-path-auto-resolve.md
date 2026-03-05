# S317 Verdict: @juzigu40-ui — scan_path auto-resolve "laundering"

## Status: PARTIALLY VERIFIED

## Summary

The submission identifies that scanning with a narrow `--path` auto-resolves out-of-scope
findings with `scan_verified` attestations, removing them from failure accounting. The code
paths are real and accurately referenced, but the reopen mechanism in `upsert_issues`
undoes the effect on the next full-scope scan, limiting the practical exploit window.

## Claims Verified

### Claim 1: Path-external findings are force-marked `auto_resolved` on narrow scan
**VERIFIED** — `desloppify/engine/_state/merge_issues.py:104-116`: When `scan_path` is set
and not `"."`, any open issue whose `file` doesn't start with the scan_path prefix is
marked `auto_resolved` via `_mark_auto_resolved`. Line numbers match exactly.

### Claim 2: `_mark_auto_resolved` writes `scan_verified: True` attestation
**VERIFIED** — `desloppify/engine/_state/merge_issues.py:49-62`: Sets
`resolution_attestation` with `kind: "scan_verified"` and `scan_verified: True`.
Line numbers match exactly.

### Claim 3: `strict` and `verified_strict` failure sets exclude `auto_resolved`
**VERIFIED** — `desloppify/engine/_scoring/policy/core.py:191-195`:
`FAILURE_STATUSES_BY_MODE` defines:
- `lenient`: `{"open"}`
- `strict`: `{"open", "wontfix"}`
- `verified_strict`: `{"open", "wontfix", "fixed", "false_positive"}`

None include `auto_resolved`, so auto-resolved issues don't count as failures in any mode.
Line numbers match exactly.

### Claim 4: Score recomputation is path-scoped
**VERIFIED** — `desloppify/engine/_scoring/state_integration.py:277-298`: `recompute_stats`
calls `path_scoped_issues(state["issues"], scan_path)` to filter issues before counting
and scoring. Line numbers are slightly off (submission cited L285-298; function starts at
L277) but the core reference is accurate.

### Claim 5: Queue selection defaults to `state["scan_path"]`
**VERIFIED** — `desloppify/engine/_work_queue/core.py:160-163`: `_resolve_inputs` reads
`state.get("scan_path")` as the default when `opts.scan_path is _SCAN_PATH_FROM_STATE`.
`desloppify/engine/_work_queue/ranking.py:136`: `build_issue_items` calls
`path_scoped_issues(state.get("issues", {}), scan_path)`. Line numbers match.

### Claim 6: Summary shows `auto_resolved` but hides `resolved_out_of_scope`
**VERIFIED** — `desloppify/app/commands/scan/reporting/summary.py:87-88`: `show_diff_summary`
displays `diff["auto_resolved"]` as "resolved" but never displays `diff["resolved_out_of_scope"]`.
`desloppify/engine/_state/merge_history.py:157`: `resolved_out_of_scope` is tracked in the
diff struct but no app-layer code reads or displays it. Line numbers match.

## Critical Mitigation: Reopen Mechanism

The submission's practical exploit scenario (narrow scan -> inflated scores) is significantly
mitigated by `upsert_issues` (`merge_issues.py:201-223`): when a subsequent scan re-detects
an `auto_resolved` issue, it reopens it with an incremented `reopen_count`. A full-scope scan
after a narrow one would re-detect and reopen all the "laundered" issues.

The "laundering" only persists as long as the user keeps scanning with a narrow path. The
docstring at line 79 explicitly acknowledges this: "Re-scanning with a wider scan_path will
reopen them via upsert."

## Accuracy

All 6 file paths are correct. Line numbers are accurate (within 1-2 lines on one claim).
The submission references commit `6eb2065` — all code paths verified against current HEAD.

## Significance Assessment

The submission correctly identifies a real design tension:
- Out-of-scope auto-resolution IS intentional (docstring says so) but the `scan_verified`
  attestation is misleading — it's really "out of scope", not "verified fixed"
- The summary UI genuinely hides the `resolved_out_of_scope` count from the user
- Between a narrow scan and the next full scan, scores ARE artificially inflated

However:
- The reopen mechanism makes this self-correcting on the next full scan
- The design is documented in-code as intentional (to "stop polluting queue counts")
- A user who only runs narrow scans is a contrived scenario since scan_path is typically
  used during development iteration, not as a permanent setting

## Originality Check

No prior bounty covers scan_path auto-resolve behavior. This is a novel finding. The same
author's S02 (config bootstrap) and S313 (supplemental) are unrelated topics.

## Scores

- **Significance**: 5/10 — Real design tension with misleading attestation and hidden UI count
- **Originality**: 6/10 — Novel finding with thorough code tracing across 6 components
- **Core Impact**: 3/10 — Self-correcting on next full scan; doesn't enable permanent score inflation
- **Overall**: 4/10 — Well-researched but practical impact limited by reopen mechanism

## One-line verdict

Real but self-correcting: narrow-path scans do temporarily launder issues into `auto_resolved` with misleading `scan_verified` attestations, but the reopen mechanism on the next full scan undoes the inflation.
