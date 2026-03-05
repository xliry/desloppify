# Bounty Verification: S37 — Unsynchronized shared mutable state in parallel batch runner

**Submission by:** @Boripheus
**Claim:** The `failures` set in the parallel batch runner is shared mutable state accessed from multiple threads without synchronization
**Status:** NOT VERIFIED

## Claim Analysis

The submission alleges that the `failures` set in `execute_batches` is unsynchronized shared mutable state — mutated from worker threads without the `lock` that protects `progress_failures`, creating a data-race bug.

## Evidence: Tracing all access sites of `failures`

### Where `failures` is created

- `runner_parallel.py:54` — `failures: set[int] = set()` — created on the main thread inside `execute_batches`

### Every mutation site of `failures` in parallel mode

| Site | File | Line | Thread | Lock? |
|------|------|------|--------|-------|
| `_queue_parallel_tasks` | `_runner_parallel_execution.py:169` | `failures.add(idx)` | **Main thread** (queuing loop) | No |
| `_complete_parallel_future` | `_runner_parallel_execution.py:252` | `failures.add(idx)` | **Main thread** (drain loop via `as_completed`) | No |
| `_record_execution_error` | `_runner_parallel_progress.py:125` | `failures.add(idx)` | **Main thread** (called only from `_complete_parallel_future`) | No |

### Where `failures` is read

- `runner_parallel.py:88` — `return sorted(failures)` — main thread, after `ThreadPoolExecutor.__exit__` (all workers joined)

### Key observation: `failures` is never touched by worker threads

The worker thread function `_run_parallel_task` (`_runner_parallel_execution.py:102-133`) does **not** receive `failures` as a parameter. It only receives `progress_failures`, `started_at`, and `lock`.

The `_drain_parallel_completions` function iterates completed futures on the main thread via `as_completed()`. Each call to `_complete_parallel_future` runs on the main thread. This is where `failures.add(idx)` happens — always on the main thread.

### Why the asymmetry between `failures` and `progress_failures` is correct

| Set | Written from | Needs lock? |
|-----|-------------|-------------|
| `progress_failures` | Worker threads (via `_record_progress_error`) AND main thread (via `_complete_parallel_future` read at line 250) | **Yes** — protected by `lock` |
| `failures` | Main thread only | **No** — single-thread access, no race possible |

The locking asymmetry is intentional and correct by design:
- `progress_failures` is mutated from worker threads (`_run_parallel_task` -> `_record_progress_error`) so it needs `lock`
- `failures` is only mutated from the main thread (queuing loop and drain loop) so no lock is needed

## Overlap with S18

This submission covers the same code and makes a similar claim to S18 (@jasonsutter87, "Selective lock discipline"), which was already PARTIALLY VERIFIED. The S18 verification noted: "failures is main-thread-only." S37 repeats the same misdiagnosis.

## Why this fails verification

1. **Central claim is factually wrong**: `failures` is NOT accessed from multiple threads. It is only mutated from the main thread
2. **The locking asymmetry is correct design**: `progress_failures` needs a lock because worker threads write to it; `failures` does not need a lock because only the main thread writes to it
3. **No data race exists**: There is no concurrent access to `failures` — all mutations happen sequentially on the main thread (queue loop, then drain loop)
4. **Overlaps with previously verified S18**: Same code area and same misdiagnosis already covered

## Scores

| Dimension | Score | Rationale |
|-----------|-------|-----------|
| Significance (Sig) | 2 | Thread safety is important, but the claim is wrong — no actual race condition exists |
| Originality (Orig) | 2 | Overlaps substantially with S18; same asymmetric-locking observation, same misdiagnosis |
| Core Impact (Core) | 1 | No impact on scoring system; batch runner is I/O orchestration |
| Overall | 2 | Identifies the locking asymmetry (real observation) but misdiagnoses it as a bug when it's correct design |
