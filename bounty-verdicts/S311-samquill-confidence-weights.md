# S311 Verdict: @samquill — Duplicate Diverged CONFIDENCE_WEIGHTS

## Claim

Batch scoring modules define a local `_CONFIDENCE_WEIGHTS` dictionary with
different values from the canonical `CONFIDENCE_WEIGHTS` in
`scoring_constants.py`, creating inconsistent confidence weighting across
scoring contexts.

## Verification

### VERIFIED: Two diverged CONFIDENCE_WEIGHTS definitions exist

**Canonical** (`desloppify/base/scoring_constants.py:7`):
```python
CONFIDENCE_WEIGHTS = {Confidence.HIGH: 1.0, Confidence.MEDIUM: 0.7, Confidence.LOW: 0.3}
```

**Batch scoring** (`desloppify/app/commands/review/batch/scoring.py:8-12`
and `desloppify/app/commands/review/batch_scoring.py:8-12`):
```python
_CONFIDENCE_WEIGHTS = {
    "high": 1.2,
    "medium": 1.0,
    "low": 0.75,
}
```

The values diverge significantly:
| Level  | Canonical | Batch  |
|--------|-----------|--------|
| high   | 1.0       | 1.2    |
| medium | 0.7       | 1.0    |
| low    | 0.3       | 0.75   |

Additionally, canonical uses `Confidence` enum keys while batch uses raw
strings — meaning the batch code cannot trivially be swapped to use the
canonical constant.

### Context: Different scoring purposes

- **Canonical weights** are used in detection scoring (`engine/_scoring/detection.py`),
  issue rendering (`base/output/issues.py`, `core/issues_render.py`), and
  the remediation engine. They weight individual issue confidence for score
  aggregation.
- **Batch weights** are used in `DimensionMergeScorer.issue_severity()` /
  `finding_severity()` for holistic review dimension merge scoring — a
  separate scoring context for batch review aggregation.

The different values *may* be intentional for these different contexts, but
there is no documentation explaining the divergence.

### Additional observation: batch/scoring.py vs batch_scoring.py duplication

These two files are near-identical copies (177 lines each) with only
terminology differences ("issue" vs "finding" in variable/method names).
Both are actively imported:
- `batch_scoring.py` by `batch_core.py` and `tests/commands/test_review_batch_core_direct.py`
- `batch/scoring.py` by `tests/commands/review/test_review_batch_core_direct.py`

## Scores

- **Significance: 4/10** — Real inconsistency between weight definitions, but
  they serve different scoring contexts; unclear if intentional design or drift.
- **Originality: 4/10** — Novel observation not covered by prior submissions.
  Specific file references appear accurate.
- **Core Impact: 2/10** — Batch weights affect holistic review dimension merges
  only, not the main detection scoring pipeline.
- **Overall: 3/10**

## Status: PARTIALLY VERIFIED

The duplicate diverged weights are real and accurately identified. However,
the two weight sets serve fundamentally different scoring purposes (detection
vs batch dimension merges), so the divergence may be by design rather than a
bug. The lack of documentation explaining this is a valid concern but reduces
significance.
