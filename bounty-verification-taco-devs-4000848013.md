# Bounty Verification: @taco-devs / S08

**Submission ID:** 4000848013
**Author:** @taco-devs
**Title:** Issue.detail stringly-typed god field
**Verdict:** VERIFIED
**Verified:** 2026-03-06 by lota-1 (task #396)

---

## Claims Verified

### Claim 1: `Issue.detail` typed as `dict[str, Any]`
**Result: CONFIRMED**

`desloppify/engine/_state/schema.py:83`:
```python
detail: dict[str, Any]
```
Exact match. No type narrowing at the field definition.

---

### Claim 2: 200+ access sites across 36+ files
**Result: PARTIALLY CONFIRMED (inflated ~2x)**

Grep across the codebase finds **111 access sites** in **34 files** (submission claims 200+/36+).
The core observation — that detail is accessed throughout the codebase with no type safety — is accurate. The specific counts are inflated roughly 2x.

---

### Claim 3: 12+ undocumented shape variants
**Result: CONFIRMED (14 shapes)**

`schema.py:58-82` documents **14 shapes entirely in comments**:

| Shape | Key fields |
|-------|------------|
| `structural` | `loc`, `complexity_score?`, `complexity_signals?`, `name?`, god_class_metrics |
| `smells` | `smell_id`, `severity`, `count`, `lines: list[int]` |
| `dupes` | `fn_a`, `fn_b`, `similarity`, `kind`, `cluster_size`, `cluster` |
| `coupling` | `target`, `tool?`, `direction`, `sole_tool?`, `importer_count?`, `loc?` |
| `single_use` | `loc`, `sole_importer` |
| `orphaned` | `loc` |
| `facade` | `loc`, `importers`, `imports_from: list[str]`, `kind` |
| `review` | `holistic?`, `dimension?`, `related_files?`, `suggestion?`, `evidence?` |
| `review_coverage` | `reason`, `loc?`, `age_days?`, `old_files?`, `new_files?` |
| `security` | `kind`, `severity`, `line`, `content`, `remediation` |
| `test_coverage` | `kind`, `loc?`, `importer_count?`, `loc_weight?`, `test_file?` |
| `props` | passthrough entry fields minus `file` |
| `subjective_assessment` | `dimension_name`, `dimension`, `failing`, `strict_score` |
| `workflow` | `stage?`, `strict?`, `plan_start_strict?`, `delta?`, `explanation?` |

All 14 shapes are type-erased into `dict[str, Any]` — no enforcement at access sites.

---

### Claim 4: No discriminant narrowing despite `detector` field
**Result: CONFIRMED**

`Issue` has `detector: str` at line 53 but `detail` is flat `dict[str, Any]`. No Union type keyed by detector value exists anywhere. Every access site must either guess shape or use `.get()` defensively.

---

## Fix Implemented

Added 14 `TypedDict` subclasses + `DetailPayload = Union[...]` alias to `schema.py`.
Updated `Issue.detail` from `dict[str, Any]` to `DetailPayload`.

This is a **pure annotation change** — zero runtime behavior change. mypy/pyright can now narrow `detail` by `detector` value in type-aware code.

**Branch:** `fix/bounty-4000848013-taco-devs`

---

## Scores

| Dimension | Score |
|-----------|-------|
| Significance | 5/10 |
| Originality | 4/10 |
| Core Impact | 2/10 |
| **Overall** | **4/10** |

**Notes:** Valid and actionable core observation. Inflated metrics (~2x) and the submission doesn't leverage the existing `detector` field as the natural discriminant. Core impact is low — no scoring behavior is affected, purely a static-analysis/maintainability improvement.
