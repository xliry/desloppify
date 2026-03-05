# Bounty Verification: S304 — Unsynchronized failures set (duplicate)

**Submission by:** @Boripheus
**Claim:** The `failures` set in the parallel batch runner is shared mutable state accessed from multiple threads without synchronization
**Status:** DUPLICATE of S37

## Duplicate Analysis

This submission is identical to S37 (@Boripheus, "Unsynchronized failures set"), which was already verified as NOT VERIFIED. Both submissions:

- Are by the same author (@Boripheus)
- Target the same code: the `failures` set in `execute_batches` (parallel batch runner)
- Make the same claim: `failures` is unsynchronized shared mutable state
- Share the same misdiagnosis: the locking asymmetry between `failures` and `progress_failures` is a bug

## S37 Verification Result (referenced)

S37 was verified NOT VERIFIED with the following findings:

1. `failures` is only mutated from the main thread (queuing loop and drain loop via `as_completed`)
2. Worker threads never receive `failures` — they only receive `progress_failures`, `started_at`, and `lock`
3. The locking asymmetry is correct by design: `progress_failures` needs a lock (worker threads write to it), `failures` does not (main-thread-only)
4. No data race exists

## Scores

| Dimension | Score | Rationale |
|-----------|-------|-----------|
| Significance (Sig) | 2 | Same as S37 — claim is wrong, no actual race condition |
| Originality (Orig) | 0 | Exact duplicate of own prior submission S37 |
| Core Impact (Core) | 1 | No impact on scoring system |
| Overall | 1 | Duplicate submission with no new information |
