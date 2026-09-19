# ADR-002: ComfyUI as the inference runtime

**Status:** Accepted

## Context

The pipeline chains identity conditioning, structural conditioning, a distilled sampler, a face
swap and a restoration pass ([image-pipeline.md](../image-pipeline.md)). Quality work means
changing that graph constantly: swap a node, change a weight, compare outputs on the same faces.

## Options considered

1. **Custom PyTorch pipeline.** Maximum control and the lowest possible overhead. Every new
   technique — a new identity adapter, a new swap model — becomes an integration project.
2. **Diffusers library.** Clean Python API, well maintained, good for standard pipelines. Non-linear
   graphs with several third-party models are workable but awkward, and the ecosystem of
   face-specific nodes lives elsewhere.
3. **ComfyUI.** Graph-based, workflow-as-JSON, and the de facto home of the identity and face
   ecosystem — InstantID, ReActor, CodeFormer, ControlNet integrations land here first.
4. **Hosted image API.** No runtime to operate.

## Decision

ComfyUI, containerised, invoked programmatically from a serverless handler.

## Reasons

- **The workflow is data, not code.** A pipeline change is a JSON diff that can be versioned,
  diffed and rolled back — which is what makes [ADR-006](006-versioned-workflows-and-rollback.md)
  possible at all.
- The face-specific ecosystem is here. Integration cost for a new technique is near zero relative
  to writing it against raw PyTorch.
- The same workflow file runs on a laptop, a marketplace GPU and a production worker.

## Consequences

**Positive.** Iteration speed on quality — the thing that actually drives revenue — is very high.
Experiments are reproducible by file.

**Negative.** A heavy runtime to containerise, with custom nodes as a real dependency-management
burden (see [debugging-notes.md](../debugging-notes.md#1-the-dependency-that-silently-moved-inference-to-cpu)).
Some per-request overhead relative to a hand-written pipeline. A dependency on a fast-moving
open-source project.

## Revisit when

The graph stops changing. Once quality work slows down, the argument flips: a frozen graph is worth
porting to a minimal custom pipeline for throughput and operational simplicity.
