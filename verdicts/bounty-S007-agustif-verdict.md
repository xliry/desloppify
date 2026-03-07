# Bounty Verification: S007 — @agustif submission

## Status: YES_WITH_CAVEATS

## Claims vs Reality

### Claim 1: Packet assembly duplicated across three paths bypassing canonical builder

> Packet assembly is duplicated in at least three paths: prepare.py:41, batch/orchestrator.py:134, and external.py:145. There is a central builder/coordinator path (packet/build.py:53, coordinator.py:208), but these flows bypass it.

**TRUE.**

All three paths independently call `review_mod.prepare_holistic_review()` with inline option construction:

- `desloppify/app/commands/review/prepare.py:48-59` — constructs `HolisticReviewPrepareOptions` inline
- `desloppify/app/commands/review/batch/orchestrator.py:142-153` — same inline construction
- `desloppify/app/commands/review/external.py:150-161` — same inline construction

The canonical builder exists at `packet/build.py:53` (`build_holistic_packet`) and is wrapped by `coordinator.py:208` (`build_review_packet_payload`). None of the three paths use either.

### Claim 2: max_files_per_batch missing from external.py

> max_files_per_batch is applied in prepare.py:55 and batch/orchestrator.py:149, but not in external.py:154.

**TRUE.**

- `prepare.py:55`: `max_files_per_batch=coerce_review_batch_file_limit(config)` — present
- `orchestrator.py:149`: `max_files_per_batch=coerce_review_batch_file_limit(config)` — present
- `external.py:150-161`: `HolisticReviewPrepareOptions` does NOT include `max_files_per_batch` — missing

The canonical builder at `packet/build.py:77` includes it. External.py bypasses the builder and omits the parameter, so external-session packets have no batch file limit.

### Claim 3: Config redaction missing from external.py

> Config redaction is applied in prepare.py:70 and batch/orchestrator.py:155, but not in external.py:125.

**TRUE.**

- `prepare.py:70`: `data["config"] = redacted_review_config(config)` — present
- `orchestrator.py:155`: `packet["config"] = redacted_review_config(config)` — present
- `external.py:_prepare_packet_snapshot` (lines 125-182): No call to `redacted_review_config`, no `packet["config"]` assignment — missing

The canonical coordinator at `coordinator.py:227` includes `packet["config"] = redacted_review_config(config)`. External.py bypasses it.

## Duplicate Coverage Assessment

No prior submissions cover review packet construction duplication or schema/policy drift across review entrypoints. This is an original finding.

## Accuracy Assessment

- File paths: Accurate — submitter omitted `desloppify/` prefix (Python package root), but all files exist at the cited locations
- Line numbers: Within 1-3 lines of actual positions (submitter used `prepare.py:41` for setup_lang call; actual packet construction starts at line 48)
- Behavioral claims: 100% accurate — both drift instances (max_files_per_batch, config redaction) are confirmed absent from external.py
- Architectural claim: Accurate — canonical builder exists and is bypassed

## Scores

- **Significance (Sig)**: 5 — Real behavioral drift between review execution modes, not hypothetical; packets produced by different entrypoints differ in batch limits and config exposure
- **Originality (Orig)**: 6 — No prior submissions cover this area; identifies a concrete DRY violation with observable consequences
- **Core Impact**: 2 — Affects review packet construction consistency, not scoring accuracy or gaming resistance directly
- **Overall**: 5 — Well-evidenced with accurate file references, concrete drift examples, and a clear architectural diagnosis

## One-line verdict
Accurate identification of duplicated review packet construction across three entrypoints bypassing a canonical builder, with confirmed schema/policy drift (missing max_files_per_batch and config redaction in external.py).
