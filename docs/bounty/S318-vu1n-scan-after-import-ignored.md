# S318 Verdict: @vu1n — `--scan-after-import` silently ignored in direct `--import` mode

## Status: VERIFIED

## Claim

`--scan-after-import` is silently ignored when using direct `--import` mode
(`desloppify review --import file.json --scan-after-import`). The flag is
parsed and stored but never forwarded to the import handler.

## Evidence Verification

### Evidence 1: Flag defined under batch execution group
**VERIFIED.** `--scan-after-import` is defined in
`parser_groups_admin_review.py:213` inside `_add_batch_execution_options()`.
While grouped with batch options, argparse adds it to the review parser
globally, so it is accepted (and parsed) for all `desloppify review`
invocations including direct `--import`.

### Evidence 2: Flag extracted into ReviewOptions but not forwarded
**VERIFIED.** `ReviewOptions.scan_after_import` is always populated from
args (`cmd.py:53`), but the direct `--import` dispatch path at
`cmd.py:186-198` calls `do_import()` without passing `scan_after_import`:

```python
if opts.import_file:
    do_import(
        opts.import_file,
        state,
        lang,
        state_file,
        config=runtime.config,
        allow_partial=opts.allow_partial,
        manual_override=opts.manual_override,
        attested_external=opts.attested_external,
        manual_attest=opts.attest,
    )
    return
```

No `scan_after_import` kwarg is passed.

### Evidence 3: `do_import` lacks `scan_after_import` parameter
**VERIFIED.** The `do_import` signature at `importing/cmd.py:322-335` has no
`scan_after_import` parameter. Even if the caller tried to pass it, it would
raise a TypeError. The function simply has no code path to trigger a
post-import scan.

### Evidence 4: Other import modes DO honor the flag
**VERIFIED.** The flag is correctly forwarded in:
- `import_run_dir` path: `cmd.py:148` passes `scan_after_import=opts.scan_after_import`
- `external_submit` path: `cmd.py:170` passes `scan_after_import=opts.scan_after_import`
- Batch execution: `batches.py:864` and `batch/execution.py:379` check `getattr(args, "scan_after_import", False)`

This asymmetry confirms the direct `--import` path is the only one missing
the flag — a classic oversight when the parameter was added to other paths
but not backported to the original import entry point.

## Assessment

| Criterion | Score | Rationale |
|-----------|-------|-----------|
| **Significance** | 4 | Real silent flag drop — user expects a scan and gets none, no error or warning |
| **Originality** | 5 | Requires tracing flag lifecycle through parser → dataclass → dispatch → handler |
| **Core Impact** | 1 | CLI UX issue only; no scoring integrity impact; user can run `desloppify scan` manually |
| **Overall** | 3 | Valid, well-evidenced bug report; low downstream consequence |

## Summary

All four evidence claims are accurate. The `--scan-after-import` flag is
silently dropped in direct `--import` mode because (a) `do_import` has no
such parameter, and (b) the dispatch code at `cmd.py:186-198` doesn't pass
it. Other import modes (batch, external-submit, import-run) correctly forward
the flag, making this an asymmetric oversight rather than a design decision.
The fix would be straightforward: add `scan_after_import` to `do_import`'s
signature and wire it through.
