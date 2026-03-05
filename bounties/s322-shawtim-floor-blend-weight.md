# Bounty S322 — @ShawTim: _FLOOR_BLEND_WEIGHT enables gaming via historical data

## Claim

`_FLOOR_BLEND_WEIGHT = 0.3` in `scoring.py` (line 27) enables gaming because
the floor score allegedly incorporates historical data, allowing past scores to
artificially inflate current results.

## Verdict: NOT VERIFIED

The floor blend uses `min(current batch scores)`, not historical data, and is
anti-gaming by design.

## Evidence

### 1. Floor is derived from current batch scores only

In `batch/scoring.py` line 163 (`merge_scores`):

```python
floor = min(score_raw_by_dim.get(key, [weighted_mean]))
```

`score_raw_by_dim` is populated exclusively from the current merge's batch
results, in `batch/core.py` line 536 (`_accumulate_batch_scores`):

```python
score_raw_by_dim.setdefault(key, []).append(score_value)
```

No historical scores, cached data, or cross-run state feeds into this dict.

### 2. The blend formula is anti-gaming

In `batch/scoring.py` lines 115-117 (`score_dimension`):

```python
floor_aware = (
    _WEIGHTED_MEAN_BLEND * inputs.weighted_mean     # 0.7
    + _FLOOR_BLEND_WEIGHT * inputs.floor             # 0.3
)
```

Since `floor = min(raw scores)`, blending 30% of the minimum score *pulls the
result down* toward the worst batch assessment. This prevents a single
high-scoring batch from inflating the merged score. It is a conservative
safeguard, not a gaming vector.

### 3. File paths and line numbers

- `desloppify/app/commands/review/batch/scoring.py` line 27: `_FLOOR_BLEND_WEIGHT = 0.3` — confirmed
- `desloppify/app/commands/review/batch_scoring.py` line 27: `_FLOOR_BLEND_WEIGHT = 0.3` — confirmed (duplicate file)
- `desloppify/app/commands/review/batch/core.py` line 536: `score_raw_by_dim` accumulation — confirmed

## Conclusion

The submission mischaracterizes the floor blend mechanism. The floor is the
minimum score from the *current* batch set, not from any historical source.
The 30% floor blend is explicitly anti-gaming: it anchors the merged score
toward the most pessimistic batch assessment, preventing inflation.
