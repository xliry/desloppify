# S331 Verification: Shadow Scoring Pipeline — ScoreBundle aggregates silently discarded

**Author:** @openclawmara
**Verified by:** lota-1
**Verdict:** VERIFIED
**Scores:** Sig=5, Orig=5, Core=3, Overall=4

## Summary

@openclawmara identifies that `compute_score_bundle()` computes four aggregate health scores
(`overall_score`, `objective_score`, `strict_score`, `verified_strict_score`) that are never
read in production code — they are silently discarded and recomputed by `_aggregate_scores()`.
Additionally, the two pipelines have a semantic disagreement on `verified_strict_score`: the
dead pipeline includes subjective dimensions while the live pipeline excludes them.

## Claim-by-Claim Verification

### Claim 1: ScoreBundle aggregate scores are computed but silently discarded

**VERIFIED.**

- `_update_objective_health()` (state_integration.py:268) calls `compute_score_bundle()` which
  returns a `ScoreBundle` with four aggregate fields.
- `_materialize_dimension_scores()` (state_integration.py:189) receives the bundle but only reads
  `bundle.dimension_scores`, `bundle.strict_dimension_scores`, and
  `bundle.verified_strict_dimension_scores` (lines 194-196).
- It never reads `bundle.overall_score`, `bundle.objective_score`, `bundle.strict_score`, or
  `bundle.verified_strict_score`.
- At line 233, `state.update(_aggregate_scores(state["dimension_scores"]))` recomputes and writes
  all four aggregates independently.
- Grep confirms the bundle's aggregate fields are only accessed in tests, never in production code.

### Claim 2: Semantic disagreement on verified_strict_score

**VERIFIED.**

- Pipeline 1 (core.py:157): `verified_strict_score=compute_health_score(verified_strict_scores)`
  — uses ALL verified_strict dimension scores including subjective dimensions (appended at
  core.py:96-103 for all modes).
- Pipeline 2 (state_integration.py:133-148): filters to `mechanical` only (line 135-138), then
  computes `verified_strict_score` from mechanical dimensions exclusively (lines 144-147).
- With `SUBJECTIVE_WEIGHT_FRACTION = 0.60`, the live pipeline drops 60% of the scoring budget
  from the verified_strict calculation when subjective dimensions are present.

### File paths and line numbers

- `results/core.py:104-137` for `compute_score_bundle` — **off by ~20 lines** (actual: 125-158).
- `state_integration.py:133-148` for `_aggregate_scores` — **exact match**.
- `state_integration.py:233` for `state.update()` call — **exact match**.
- `state_integration.py:144` for mechanical verified_strict — **exact match**.

## Assessment

This is a well-researched, accurate submission. The core finding is real: there are two
independent scoring pipelines, Pipeline 1's aggregate results are dead computation, and the
two disagree on whether `verified_strict_score` should include subjective dimensions.

**Significance (5/10):** Real dead code and semantic fork in the scoring engine. The
disagreement is currently inert (Pipeline 1 results are discarded), but represents a
genuine maintenance trap and potential correctness risk if Pipeline 1 were ever activated.

**Originality (5/10):** Novel finding — no previous submission identified this dual-pipeline
issue. The analysis traces both code paths clearly and identifies the specific semantic
disagreement.

**Core Impact (3/10):** The live scoring path (_aggregate_scores) is the one that actually
determines scores written to state. The dead code in ScoreBundle is wasted computation but
doesn't affect actual scoring results. The semantic disagreement is theoretical until
someone tries to use Pipeline 1's values.

**Overall (4/10):** Accurate, well-evidenced submission with a real finding. Loses points
because the impact is limited to dead code/wasted computation rather than producing
incorrect live scores.
