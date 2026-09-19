# ADR-001: Serverless GPU workers rather than always-on instances

**Status:** Accepted

## Context

Preview generation is bursty and traffic-driven. Load follows ad delivery and Indian evening
hours — long quiet stretches punctuated by spikes. The workload needs 24 GB+ of VRAM and a large
model set resident in memory.

## Options considered

1. **Always-on cloud GPU instance (AWS/GCP).** Predictable, fully controlled, and the most
   expensive per useful second by a wide margin. An idle A10G bills the same as a busy one.
2. **Serverless GPU (RunPod).** Scale to zero, per-second billing, containerised runtime. Costs a
   cold start when no worker is warm, and puts the provider's environment stability on the critical
   path.
3. **Marketplace GPUs (vast.ai).** Cheapest per hour, highest variance in availability and host
   quality.
4. **Hosted image-generation API.** No infrastructure at all — but see
   [ADR-002](002-comfyui-over-diffusers.md): none of them do identity-preserving generation to the
   standard this product requires.

## Decision

Serverless GPU workers for production, with marketplace GPUs for development and experimentation.

## Reasons

- Utilisation is the dominant cost term at this volume. Paying for idle GPUs would consume the
  margin the business runs on.
- Container-based deployment means the development and production runtimes are the same artefact.
- Scale-to-zero makes experimentation cheap, which matters when quality work requires many runs.

## Consequences

**Positive.** GPU spend tracks demand. Capacity scales without a provisioning decision. Rebuilding
the environment is a container pull.

**Negative.** Cold starts are a real latency cost on a conversion-critical path, mitigated by
warm-worker configuration. Provider environment stability becomes a production dependency — which
has since caused a real incident
([report](../incidents/2026-runpod-gpu-tier-instability.md)).

## Revisit when

Sustained utilisation is high enough that reserved capacity is cheaper than per-second billing, or
when cold-start latency becomes the binding constraint on conversion.
