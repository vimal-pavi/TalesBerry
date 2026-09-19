# ADR-006: Pinned, versioned workflow artefacts with an explicit rollback target

**Status:** Accepted

## Context

Generation quality is the product. It is also the output of a graph with dozens of tunable
parameters, several third-party models and a fast-moving open-source runtime. A quality regression
does not throw an exception — it produces a child who looks slightly less like herself, which
surfaces days later as a refund and a review.

Iterating on that graph is the highest-value engineering activity in the business. Iterating
*safely* is what makes it survivable.

## Options considered

1. **Mutable "latest" workflow.** Fastest to iterate on, impossible to reason about after the fact.
   What was running when this order was generated? Unknown.
2. **Workflow in version control, runtime floating.** Better, but the runtime and custom-node
   versions still drift underneath a fixed graph, so identical inputs can produce different outputs.
3. **Pinned artefacts end to end.** A locked, named workflow file inside a tagged container image,
   with weights on a versioned volume. The last known-good tag is an explicit rollback target.

## Decision

Pinned artefacts end to end. The production workflow is a locked file with a version in its name;
the runtime is a tagged image; weights are versioned on the volume. Experimental workflows never
share a name with a production one.

## Reasons

- **Rollback becomes selection, not reconstruction.** Under pressure, "deploy the last known-good
  tag" is a decision; "work out what we changed" is an outage of unknown length.
- Quality regressions can be bisected, because there is a discrete sequence of versions to bisect.
- It makes "is it us or is it the provider?" a one-experiment question — which is exactly how the
  [GPU tier incident](../incidents/2026-runpod-gpu-tier-instability.md) was resolved quickly.

## Consequences

**Positive.** Regressions are recoverable in minutes. Experiments are reproducible. Changes are
attributable.

**Negative.** Version discipline is manual and depends on the operator, which is a weakness of a
one-person team rather than of the approach. Pinned versions accumulate upgrade debt: staying on a
known-good runtime means deferring upstream improvements until there is time to validate them.

## Revisit when

There is capacity for automated quality regression testing on a fixed panel of consented reference
faces. At that point the release gate becomes a measured resemblance score rather than an
operator's judgement, and upgrades stop being scary.
