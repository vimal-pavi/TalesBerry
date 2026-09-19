# Incident report: serverless GPU tier instability

**Status:** resolved · **Impact:** preview generation degraded · **Author:** Vimal Jangid

> Written in the format I would use internally. Times, durations and error rates are marked as
> TODO rather than invented — fill them from your own logs before publishing.

## Summary

Generation jobs on the previously stable 30 GB serverless GPU tier began failing and timing out
intermittently. Nothing in the application, the container image or the workflow graph had changed.
The cause was upstream: provider-side driver updates combined with increased multi-tenancy on that
tier. Resolved by pinning production to higher-supply GPU configurations and by moving
experimentation to a second provider.

## Impact

- Preview generation — the pre-payment, conversion-critical path — degraded for <!-- TODO: duration -->.
- <!-- TODO: failure/timeout rate, affected sessions -->
- No data loss. No impact on already-paid print jobs, which run asynchronously and were retried.

Every failed preview in this window is a customer who uploaded their child's photo and got nothing
back, at the exact moment they were deciding whether to spend ₹1,799. The business cost of this
class of failure is much higher than the number of affected requests suggests.

## Detection

<!-- TODO: how you noticed — failed jobs in the dashboard, a customer report, your own test run.
     Say plainly if it was a customer report; "our detection was a customer" is a finding, and
     hiring managers respect it far more than a fabricated alert. -->

## Investigation

**Hypothesis 1 — our change.** Ruled out. No deploy correlated with onset; the running image was
unchanged and the pinned workflow version was identical.

**Hypothesis 2 — workflow or model regression.** Ruled out. The same image and workflow ran
correctly on a different GPU configuration and on a second provider. If the artefact is unchanged
and it works elsewhere, the artefact is not the variable.

**Hypothesis 3 — resource exhaustion in our own code.** Investigated. <!-- TODO: what you checked —
VRAM headroom, worker lifetime, concurrency. -->

**Hypothesis 4 — provider environment.** Confirmed. Failures were specific to one GPU tier,
correlated with provider-side driver updates, and consistent with increased multi-tenancy on that
tier — contention and environment drift on shared hosts, not anything in our stack.

The step that collapsed the search space: **running the identical container elsewhere.** Because
the runtime is a versioned, self-contained image, "is it us or is it them" is a single experiment
rather than a debate.

## Root cause

Environment instability on a shared, lower-supply GPU tier at the provider, triggered by driver
updates and tenancy pressure. Our workload was correct; the substrate under it changed.

## Resolution

1. Production pinned to higher-supply GPU configurations that have consistent availability.
2. Development and experimentation moved to a second provider, so provider-side instability can
   never block both production and the ability to diagnose it.
3. Known-good container image and workflow version treated as an explicit rollback target.

## Why the rollback path was safe

The production workflow is a **pinned, versioned artefact** — a locked workflow file inside a
tagged container image, with model weights on a versioned volume. Rolling back is selecting a known
tag, not reassembling a working state from memory under pressure. That property was deliberate
([ADR-006](../adr/006-versioned-workflows-and-rollback.md)) and it is the reason this incident was
an inconvenience rather than an outage of unknown duration.

## Lessons

1. **A single GPU provider is a single point of failure**, and at this scale the cheapest mitigation
   is not multi-provider production — it is multi-provider *diagnosis*, so you can always answer
   "is it us?" in minutes.
2. **Cheap tiers are cheap for a reason.** Lower-supply tiers carry higher tenancy variance. For a
   pre-payment, conversion-critical path, tier stability is worth more than the hourly saving.
3. **Pinned artefacts turn incidents into decisions.** Every minute not spent reconstructing what
   was running is a minute spent on the actual problem.

## Follow-ups

- [ ] Synthetic canary generation on a schedule, alerting on latency and failure rate, so detection
      does not depend on a customer.
- [ ] Documented one-command failover to the secondary provider.
- [ ] Per-stage timing emitted as structured events rather than reconstructed from logs.
