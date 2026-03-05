# Bounty Verification: S336 — @yv-was-taken

## Submission: "Subjective dimension_scores keyed by mutable display names instead of stable identifiers"

**Status: VERIFIED**

---

## Evidence

### Claim 1: `append_subjective_dimensions()` uses display name as dict key
**TRUE.** At `engine/_scoring/subjective/core.py:207`, display name is computed via `_dimension_display_name(dim_name, lang_name=lang_name)`. At line 240, `results[display] = {...}` uses this display name as the dictionary key. The stable internal key (`dim_name`) is buried as nested metadata at line 253: `"dimension_key": dim_name`. Line numbers are exact.

### Claim 2: `_canonical_subjective_dimension_key()` reverse-maps display names
**TRUE.** At `engine/_work_queue/synthetic.py:35-43`, this function scans the entire `DISPLAY_NAMES` dict on every call to map a display label back to an internal key. Line numbers are exact.

### Claim 3: `_subjective_dimension_aliases()` generates 5+ aliases
**TRUE.** At `synthetic.py:46-56`, the function returns a set of 5 aliases (cleaned.lower(), cleaned with underscores, slugified cleaned, canonical.lower(), slugified canonical). Line numbers are exact.

### Claim 4: `_lookup_dimension_score()` does case-insensitive fuzzy matching
**TRUE.** At `app/commands/show/scope.py:147-162`, the function performs case-insensitive fallback matching with `replace(" ", "_")` because the key format in `dimension_scores` is unreliable. Line numbers are exact.

### Claim 5: Divergent `_normalize_dimension_name` implementations
**TRUE.** `health.py:15-16` normalizes to **spaces** (`" ".join(...)`), while `subjective_dimensions.py:89-90` and `metadata.py:27-28` normalize to **underscores** (`"_".join(...)`). This is a real divergence that could cause subtle key-matching failures if the wrong normalization is used to look up a key produced by the other.

### Claim 6: Display name can vary by language
**TRUE.** `_dimension_display_name()` at `core.py:61-69` delegates to `metadata.dimension_display_name(dim_name, lang_name=lang_name)`, which loads language-specific overrides. If a language override changes a display name, old dimension_scores entries under the old display name become orphaned.

### Claim 7: Carried-forward logic won't match old keys to new ones
**PARTIALLY TRUE.** At `state_integration.py:213-219`, the carried-forward logic explicitly **skips** subjective dimensions (`if "subjective_assessment" in prev_data.get("detectors", {}): continue`). So the issue isn't that carried-forward mismatches keys — it's that subjective dimensions are not carried forward at all. The broader orphaning concern is valid but the specific mechanism cited is slightly misleading.

---

## Accuracy
- **File paths:** All 7 file paths are correct and exist in the codebase.
- **Line numbers:** All line numbers are accurate (exact or within 1 line).
- **Code behavior:** All described behaviors are accurately characterized.

## Assessment

| Metric | Score | Rationale |
|--------|-------|-----------|
| **Significance** | 6 | Real architectural issue creating unnecessary complexity (reverse-mapping, aliases, fuzzy matching). The system works correctly but the keying strategy is genuinely inconsistent. |
| **Originality** | 7 | Deep cross-file tracing through 7 files, identifying a systematic keying inconsistency. Not a surface-level observation — requires understanding the full data flow. |
| **Core Impact** | 3 | Does not affect gaming resistance or scoring accuracy. The dimension scores are computed correctly regardless of the keying strategy. The language-override orphaning concern is theoretical — no evidence of it occurring in practice. |
| **Overall** | 5 | Well-researched, accurate, and clearly articulated. All file paths and line numbers are correct (rare among submissions). However, the practical impact is low — the system functions correctly, and the complexity is manageable. The fix described (key by dim_name) would be a genuine improvement but isn't fixing a bug. |

## One-line verdict
Accurate and well-traced architectural observation about display-name keying in dimension_scores creating unnecessary reverse-mapping complexity, but with low practical impact on scoring correctness or gaming resistance.
