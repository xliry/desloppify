# Bounty S330 Verdict: @opspawn — JUDGMENT_DETECTORS stale-import in concerns.py

## Claim
`JUDGMENT_DETECTORS` imported via `from desloppify.base.registry import JUDGMENT_DETECTORS`
in `concerns.py` is a stale snapshot. When plugins call `register_detector()` with
`needs_judgment=True`, the new detector is NOT reflected in `concerns.py`'s local binding,
silently excluding plugin detectors from concern generation.

## Verification

### The mechanism (CONFIRMED)

1. **`concerns.py:20`** — `from desloppify.base.registry import JUDGMENT_DETECTORS`
   creates a local name binding to the `frozenset` object that exists at import time.

2. **`registry.py:418-427`** — `register_detector()` rebuilds `JUDGMENT_DETECTORS` as a
   new `frozenset` and reassigns the module-level name via `global JUDGMENT_DETECTORS`.
   This updates `registry.JUDGMENT_DETECTORS` but NOT `concerns.JUDGMENT_DETECTORS` — the
   old frozenset is immutable and the local binding in concerns.py still points to it.

3. **`concerns.py:434-437` and `:483-486`** — Both `_file_concerns()` and
   `_cross_file_patterns()` filter issues against the stale `JUDGMENT_DETECTORS`,
   so any plugin-registered `needs_judgment=True` detector would be silently excluded
   from concern generation.

### The Python semantics are correct
`from module import name` copies the reference at import time. Reassigning the name
in the source module (even with `global`) does NOT propagate to importers. This is a
well-known Python binding gotcha. The fix would be to either:
- Access `registry.JUDGMENT_DETECTORS` via attribute lookup each time (reads current binding)
- Use `_RUNTIME.judgment_detectors` (the mutable dataclass is always current)
- Add a `get_judgment_detectors()` accessor function

### Practical impact (LOW — currently zero)

**No existing code triggers this bug today:**

1. **`generic.py:146-153`** — `register_detector()` is called for generic tool specs,
   but `needs_judgment` defaults to `False`. Plugin-registered tool detectors are NOT
   judgment detectors.

2. **All 20 built-in judgment detectors** (smells, structural, coupling, orphaned, etc.)
   are already in the base registry dict BEFORE `concerns.py` is imported. They are
   captured in the initial frozenset.

3. **No existing plugin or test** calls `register_detector(DetectorMeta(..., needs_judgment=True))`.
   The `test_generic_plugin.py` tests register detectors but never with `needs_judgment=True`.

The bug is latent: it would only manifest if a future plugin registered a detector with
`needs_judgment=True`, which no current code path does.

## Verdict: VALID but LOW significance

- **Correctness**: The stale-binding analysis is technically correct.
- **Bug class**: Real Python binding gotcha — the code intends dynamic updates
  (evidenced by the `global` + reassignment pattern) but the consumer defeats it.
- **Current impact**: Zero. No existing code path triggers the stale binding.
- **Future risk**: Low-medium. A plugin author setting `needs_judgment=True` would
  silently lose concern generation for their detector, which would be hard to debug.
- **Originality**: Moderate. Identifies a real semantic mismatch between the registry's
  update mechanism and the consumer's import pattern.

**Score: 3/10** — Correct analysis of a real but currently-dormant bug with no
demonstrated impact on existing functionality.
