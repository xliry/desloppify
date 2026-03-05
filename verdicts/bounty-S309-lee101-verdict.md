# Bounty Verification: S309 — @lee101 submission

## Status: PARTIALLY VERIFIED

## Claims vs Reality

### Claim 1: Fail-open persistence resets to empty_state()/empty_plan()

**CONFIRMED** — The code does fall back to empty state/plan on corruption or validation failure.

Evidence:
- `desloppify/engine/_state/persistence.py:126-138`: After successful JSON parse, if `_normalize_loaded_state()` throws `ValueError`/`TypeError`/`AttributeError`, the code returns `empty_state()`. Line numbers match exactly.
- `desloppify/engine/_plan/persistence.py:68-73`: If `validate_plan()` throws `ValueError`, the code returns `empty_plan()`. Line numbers match exactly.
- `desloppify/engine/_state/persistence.py:59-115`: For JSON parse failures, the code first attempts backup recovery (`.json.bak`), and only falls to `empty_state()` if both primary and backup fail. It also renames the corrupted file to `.json.corrupted` for forensics.
- `desloppify/engine/_plan/persistence.py:35-51`: Similar backup recovery for plan parse failures.

**Nuance the submission omits:** The fail-open is a last resort — backup recovery is attempted first for parse errors. The submission focuses on the normalization/validation path (lines 126-138, 68-73) where valid JSON with invalid schema resets without backup attempt. This is a fair concern for that specific path, but the submission's framing of "silent hard resets" overstates the issue since warnings are printed to stderr and logged.

**Significance:** This is a real design trade-off. The code chooses availability (tool keeps working) over durability (preserving possibly-corrupted data). For a CLI tool, this is defensible — crashing on corrupted state would be worse. The normalization-failure path (no backup attempt) is the weakest point.

### Claim 2: Split-brain BatchProgressTracker

**CONFIRMED as dead code, NOT as split-brain.**

Evidence:
- `desloppify/app/commands/review/batch/execution.py:46-116`: `_build_progress_reporter()` is the active progress reporting function, used at line 591.
- `desloppify/app/commands/review/batches_runtime.py:43-117`: `BatchProgressTracker` class implements the same queued/start/done lifecycle events.
- `BatchProgressTracker` is **never imported** by any module. It appears only in its own file's `__all__` list (line 424). It is dead code.
- The submission's claimed line numbers are approximately correct: execution.py:46 (reporter function), execution.py:233 (final status loop), execution.py:591 (usage), batches_runtime.py:73 (report method), batches_runtime.py:151 (mark_final_statuses method).

**The "split-brain" diagnosis is wrong.** There is no active split-brain because `BatchProgressTracker` is unused dead code. The active flow only uses `_build_progress_reporter`. The real issue is simply dead code that should be removed — a much less severe problem than "split-brain state machines."

## Accuracy Assessment
- File paths: 100% correct — all referenced files exist
- Line numbers: Accurate within 1-2 lines for all references
- Code evidence: The diff-style evidence matches actual code patterns
- Diagnosis: Claim 1 is valid but overstated (ignores backup recovery). Claim 2 misdiagnoses dead code as active split-brain.

## Scores
- **Significance (Sig)**: 4 — Fail-open is a real design concern; dead code is minor
- **Originality (Orig)**: 4 — Accurate file references and real code analysis, but the "split-brain" diagnosis is wrong
- **Core Impact**: 1 — Neither issue affects the scoring engine or gaming resistance
- **Overall**: 3 — Correct file paths and line numbers with real (if overstated) observations; self-described "work in progress"

## One-line verdict
Accurate file references showing real fail-open persistence and dead code, but overstates severity: backup recovery exists for parse failures, and BatchProgressTracker is unused dead code, not an active split-brain.
