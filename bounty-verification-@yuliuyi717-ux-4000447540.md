## Problem (in our own words)

The StateModel (schema.py) serves as a single mutable document that co-locates three distinct concerns: raw issue records from detectors, derived scoring fields (strict_score, overall_score, stats), and operator decision logs (resolution attestations, subjective assessments). Both merge_scan() and resolve_issues() mutate issues and recompute scores in the same flow, creating a coupling between evidence collection, decision recording, and score derivation.

## Evidence

- `desloppify/engine/_state/schema.py:259-292` — StateModel TypedDict combines `issues` (raw), `strict_score`/`verified_strict_score`/`overall_score` (derived), `stats` (derived), `subjective_assessments` (operator/LLM), `attestation_log` (operator), `concern_dismissals` (operator)
- `desloppify/engine/_state/schema.py:322-339` — `empty_state()` initializes all three concern types in a single dict
- `desloppify/engine/_state/merge.py:123-218` — `merge_scan()` calls `upsert_issues()` (mutates issues), `auto_resolve_disappeared()` (mutates statuses), then `_recompute_stats()` (derives scores) — all on the same state dict
- `desloppify/engine/_state/resolution.py:99-173` — `resolve_issues()` writes operator decisions (`status`, `note`, `resolution_attestation`) directly into issue records (line 160), then calls `_recompute_stats()` (line 171)

## Fix

No fix needed — the coupling is intentional and pragmatic for a CLI tool with file-based persistence. Scores are deterministically recomputed from issues on every mutation, maintaining consistency. The suggested event-sourcing architecture would be disproportionate over-engineering.

## Verdict

| Question | Answer | Reasoning |
|----------|--------|-----------|
| **Is this poor engineering?** | YES | Co-locating raw evidence, derived caches, and operator decisions in one mutable model creates real coupling that makes provenance tracking harder and prevents independent evolution of concerns. |
| **Is this at least somewhat significant?** | NO | The pattern is pragmatic for a CLI tool. Scores are always recomputed (not stale-cached), there's no concurrency, and audit trails exist via attestation_log and scan_history. The practical impact is minimal. |

**Final verdict:** YES_WITH_CAVEATS

## Scores

| Criterion | Score |
|-----------|-------|
| Significance | 4/10 |
| Originality | 3/10 |
| Core Impact | 3/10 |
| Overall | 3/10 |

## Summary

The submission correctly identifies that StateModel co-locates raw detector output, derived scores, and operator decisions in a single mutable document, and that merge_scan() and resolve_issues() both mutate issues and recompute scores in the same flow. All three code references are accurate. However, the practical significance is overstated: scores are deterministically recomputed (not stale-cached), the tool runs sequentially (no concurrency risk), and audit trails exist via separate fields. The "non-commutative behavior" claim is overstated — final state is deterministic given the same inputs; only the recorded history trajectory varies with operation ordering. The suggested fix (event sourcing with immutable event log) is extreme over-engineering for a local CLI tool.

## Why Desloppify Missed This

- **What should catch:** A subjective review dimension focused on data-model separation — flagging TypedDicts that mix raw data, derived caches, and user-input fields in one model.
- **Why not caught:** Mechanical detectors check structural patterns (complexity, coupling, god classes) but not data-model design concerns. Subjective review dimensions focus on code-level quality rather than state architecture.
- **What could catch:** A "state model cohesion" subjective dimension that checks whether persisted state mixes raw/derived/operator data concerns. Alternatively, a mechanical check for TypedDicts exceeding N fields with mixed read/write semantics.

## Verdict Files

- [Verdict JSON](https://github.com/xliry/desloppify/blob/fix/bounty-4000447540-yuliuyi717-ux/bounty-verdicts/%40yuliuyi717-ux-4000447540.json)
- [Verdict Report](https://github.com/xliry/desloppify/blob/fix/bounty-4000447540-yuliuyi717-ux/bounty-verification-%40yuliuyi717-ux-4000447540.md)

Generated with [Lota](https://github.com/xliry/lota)
