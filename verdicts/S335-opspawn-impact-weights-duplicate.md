# Verdict: S335 — @opspawn — compute_score_impact ignores confidence weights

**Status:** DUPLICATE of S21 (@xinlingfeiwu)

## Submission Summary

@opspawn claims `compute_score_impact` at `impact.py:41` subtracts `issues_to_fix * 1.0`
from `weighted_failures`, ignoring per-issue confidence weights (`HIGH: 1.0`, `MEDIUM: 0.7`,
`LOW: 0.3`), causing score improvement forecasts to be systematically over-estimated for
non-HIGH-confidence detectors.

## Duplicate Analysis

S21 by @xinlingfeiwu reported the same finding: `compute_score_impact` ignores confidence
weights when estimating score improvement. S21 was already verified as PARTIALLY VERIFIED
with scores Sig=5, Orig=5, Core=2, Overall=4.

S335 describes the exact same bug at the exact same location (`impact.py:41`):

```python
new_weighted = max(0.0, old_weighted - issues_to_fix * 1.0)  # assumes weight 1.0
```

While `weighted_failures` is accumulated using actual `CONFIDENCE_WEIGHTS` values from
`scoring_constants.py:7` via `detection.py:57`.

## Evidence

- **impact.py:41** — `issues_to_fix * 1.0` confirmed: hardcoded 1.0 weight per fix
- **scoring_constants.py:7** — `CONFIDENCE_WEIGHTS = {HIGH: 1.0, MEDIUM: 0.7, LOW: 0.3}` confirmed
- **detection.py:57** — `CONFIDENCE_WEIGHTS.get(issue.get("confidence", "medium"), 0.7)` confirmed

## Accuracy

- File paths: Correct (`desloppify/engine/_scoring/results/impact.py:41`)
- Line numbers: Accurate
- Code behavior: Correctly described

## Scores

| Metric | Score | Reasoning |
|--------|-------|-----------|
| Significance | 5 | Real estimation bug, but only affects UI forecasts |
| Originality | 0 | Exact duplicate of S21 — no new findings |
| Core Impact | 2 | Affects display only, not actual scoring |
| Overall | 2 | Technically correct but zero originality |

## One-line Verdict

Duplicate of S21: same `compute_score_impact * 1.0` hardcoded weight finding by @xinlingfeiwu, already verified.
