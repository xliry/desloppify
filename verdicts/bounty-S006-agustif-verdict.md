# Bounty Verification: S006 — @agustif submission

## Status: YES_WITH_CAVEATS

## Claims vs Reality

### Claim 1: Newer-version plans are warned then mutated (persistence.py:58, :67)

> On load, newer-version plans are only warned about, then still mutated.

**TRUE.**

`engine/_plan/persistence.py:58-65`: If `version > PLAN_VERSION`, a warning is printed to stderr but execution continues. Line 67: `ensure_plan_defaults(data)` runs unconditionally, applying mutations to the loaded data regardless of version.

This means a plan saved by a newer version of the tool will have its schema coerced by an older version's migration logic — a real forward-compatibility hazard.

### Claim 2: ensure_plan_defaults always runs migration/coercion on read (schema.py:198)

> `ensure_plan_defaults` always runs migration/coercion on read.

**TRUE.**

`engine/_plan/schema.py:190-198`: `ensure_plan_defaults` first applies `setdefault` for all v7 keys, then unconditionally calls `_upgrade_plan_to_v7(plan)`. This runs on every load, not just for legacy plans.

### Claim 3: Migration coerces wrong shapes to empty containers and force-sets version to v7 (schema_migrations.py:25, :30, :42, :304)

> Migration coerces wrong shapes to empty containers and force-sets version to v7 even for newer input.

**TRUE.**

- `schema_migrations.py:19-26`: `_ensure_container` replaces any value that doesn't match the expected type with an empty `list()` or `dict()`. This silently discards data if a newer version changed a field's type.
- `schema_migrations.py:29-42`: `ensure_container_types` applies this coercion to `queue_order`, `skipped`, `overrides`, `clusters`, `superseded`, `promoted_ids`, `plan_start_scores`, `execution_log`, `epic_triage_meta`, `commit_log`, and `uncommitted_issues`.
- `schema_migrations.py:304-306`: `if plan.get("version") != V7_SCHEMA_VERSION: plan["version"] = V7_SCHEMA_VERSION` — this **downgrades** a hypothetical v8+ plan to v7, making the version lie about the data's origin.

This is the strongest finding in the submission. A forward-version plan gets silently downgraded.

### Claim 4: If invariants fail, drops to fresh empty plan (persistence.py:69-73)

> If invariants still fail, it drops to a fresh empty plan.

**TRUE.**

`engine/_plan/persistence.py:68-73`: After `ensure_plan_defaults` mutates the data, `validate_plan` runs. If it raises `ValueError`, the code returns `empty_plan()` — all user intent (queue order, clusters, skips) is lost.

This is the same fail-open pattern covered by S309 (Claim 1).

### Claim 5: Normal flows save the mutated/empty result (persistence.py:80-97; preflight.py:47-50)

> Normal flows then save that result, making loss durable.

**PARTIALLY TRUE.**

- `persistence.py:78-100` is the `save_plan` function — it does not auto-save on load.
- `app/commands/scan/preflight.py:47-50`: `load_plan()` followed by conditional `save_plan(plan)` — but this only saves if `plan_start_scores` is non-empty.

The submission implies every load triggers a durable save, which is not accurate. However, any downstream code path that loads, mutates, and saves (which does happen in scan preflight and other flows) will persist the coerced/empty result. The concern is directionally correct but overstated — not every load leads to a save.

### Claim 6: Related pattern in state persistence (state/schema.py:401, :431; state/persistence.py:128, :138)

> Related pattern exists in state persistence too.

**TRUE.**

- `engine/_state/schema.py:400-431`: `_normalize_loaded_state` removes non-dict issues (line 404→430-431) and coerces fields with defaults.
- `engine/_state/persistence.py:126-138`: On normalization failure (`ValueError`, `TypeError`, `AttributeError`), falls back to `empty_state()`.

Same fail-open pattern. Already covered by S309 Claim 1.

## Overlap with S309 (lee101)

S309 covers the **fail-open persistence** pattern — both state and plan falling back to empty on corruption/validation failure. S006 claims 4 and 6 directly overlap with S309 Claim 1.

**S006 adds original value beyond S309:**
1. The **version downgrade** problem (v8+ → v7 force-set) — not covered by S309
2. The **container coercion** during migration (wrong shapes → empty containers) — not covered by S309
3. The **warn-but-still-mutate** behavior for newer-version plans — not covered by S309
4. Framing the entire read-path migration strategy as a systemic design decision, not just the fail-open endpoint

S309 focused on the final fallback; S006 focuses on the destructive transformations that happen before the fallback.

## Accuracy Assessment

- File paths: 100% accurate — all referenced files exist at the cited locations
- Line numbers: Accurate within 1-2 lines for all references
- Code behavior: Correctly described for claims 1-4 and 6; claim 5 overstates the auto-save scope
- Architectural diagnosis: Sound — the read-path coercion strategy is a real design concern

## Scores

- **Significance (Sig)**: 5 — The version downgrade and container coercion are real reliability hazards in a planning tool; the fail-open reset (shared with S309) is a known design trade-off
- **Originality (Orig)**: 4 — Claims 1-3 (version downgrade, container coercion, warn-but-mutate) are original beyond S309; claims 4 and 6 overlap directly with S309
- **Core Impact**: 1 — Affects plan/state persistence reliability, not scoring accuracy or gaming resistance
- **Overall**: 4 — Well-evidenced with accurate file references, original migration-strategy analysis beyond S309, one overstated claim (auto-save scope)

## One-line verdict
Accurate identification of destructive read-path migration (version downgrade, container coercion, warn-but-mutate) in plan persistence, with original analysis beyond S309's fail-open coverage; claim about auto-save durability is overstated.
