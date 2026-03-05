"""Plan data model, operations, and persistence.

This is the internal implementation of the plan system. External code
should use ``engine.plan`` (the public facade) or ``engine.planning``
(plan rendering and output) instead of importing from this package directly.

Submodules:
- schema / schema_migrations: PlanState TypedDict and migration logic
- operations_*: queue/skip/cluster/meta/lifecycle mutations
- persistence: JSON read/write with atomic saves
- reconcile: post-scan plan↔state synchronization
- auto_cluster: automatic issue clustering
- epic_triage*: LLM-powered triage pipeline
- stale_dimensions: dimension staleness detection
- subjective_policy: subjective review scheduling
- commit_tracking: git commit↔plan-item linking
"""
