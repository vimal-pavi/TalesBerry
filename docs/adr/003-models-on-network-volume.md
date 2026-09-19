# ADR-003: Model weights on a network volume, not baked into the image

**Status:** Accepted

## Context

The model set — SDXL, a Lightning LoRA, InstantID, ControlNet, face analysis, swap and restoration
models — is many gigabytes. Those weights have to be in VRAM before the first image is generated on
a cold worker.

The instinctive answer is to bake everything into the container image so a worker is fully
self-contained. That is the wrong call here.

## Options considered

1. **Bake weights into the image.** Self-contained and reproducible. Produces an enormous image:
   slow builds, slow pulls on cold scheduling, and a full rebuild-and-redistribute cycle to change
   one model.
2. **Download weights at container start.** Small image, but every cold start pays a large network
   transfer — on the conversion-critical path.
3. **Network volume attached to workers.** Weights live once, are mounted by every worker, and are
   versioned independently of the code.

## Decision

Weights on a network volume. The container image carries ComfyUI, the custom nodes, the
dependencies and the handler — everything that is *code* — and none of the weights.

## Reasons

- Cold-start cost is dominated by loading weights into VRAM; a mounted volume avoids paying a
  network download on top of that.
- Image builds and pulls stay fast, which keeps the deploy loop tight.
- **Models and code version independently.** Testing a different face-restoration model does not
  require rebuilding and redistributing a multi-gigabyte image.

## Consequences

**Positive.** Small images, fast deploys, cheap model experimentation.

**Negative.** A worker is no longer fully self-contained — the volume is a dependency, and moving
providers means replicating it. Volume and image versions must be kept compatible; a workflow
referencing a model that is not on the mounted volume fails at run time, not build time.

## Revisit when

Cold-start volume-mount latency becomes measurable against VRAM load time, or when multi-provider
production makes a self-contained artefact more valuable than a fast build loop.
