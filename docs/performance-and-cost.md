# GPU performance and cost

In a D2C business with a fixed print cost and a fixed price, GPU seconds are not an engineering
metric. They are a line in the gross margin. This document is about where the seconds go and how
the spend was cut without cutting the thing customers are paying for.

## The economic frame

The numbers that make this a cost-engineering problem rather than a latency one:

- Roughly **3%** of people who generate a free preview go on to buy.
- A book is **20+ generated pages**; a preview is a small number of pages.
- Preview generation happens **before** any payment, for every visitor who uploads a photo.

So the dominant GPU cost in the system is work done for people who will never pay. Optimising the
paid path is close to irrelevant; optimising the free path is the whole game.

## Where the time goes

Per-page generation breaks into stages that behave very differently:

| Stage | Cold worker | Warm worker | Notes |
|---|---|---|---|
| Container + Python + ComfyUI start | dominant | 0 | Paid once per worker, not per image |
| Model load into VRAM | dominant | 0 | SDXL + InstantID + swap + restoration is a lot of weights |
| Input fetch | small | small | Parallelised; was sequential |
| Diffusion sampling | moderate | moderate | 6 steps, not 25–40 — see [image-pipeline.md](image-pipeline.md#4-generation--sdxl-with-a-lightning-4-step-lora-6-steps-cfg-18-euler--sgm_uniform) |
| Face swap + restoration | moderate | moderate | Fixed cost per face |
| Upload | small | small | |

<!-- FILL: replace the qualitative column with measured seconds from benchmarks/. -->

The structural insight: **cold-start cost is per-worker, generation cost is per-image.** Everything
worth optimising is therefore either "make cold starts rarer" or "make the per-image graph
cheaper" — and those are completely different kinds of work.

### Cold start vs warm

```
COLD REQUEST                          WARM REQUEST
  container scheduling                  worker already running
  → python + ComfyUI init               → models already in VRAM
  → model load into VRAM                → inference
  → GPU warm-up
  → inference
```

Mitigations in production: keeping workers warm during traffic hours rather than paying the load
cost on every request, pinning GPU tiers that actually have supply (see
[the incident report](incidents/2026-runpod-gpu-tier-instability.md)), and keeping model loading
off the request path.

## The changes that mattered

| Change | Mechanism | Effect |
|---|---|---|
| Lightning LoRA at 6 steps, CFG 1.8 | ~5× fewer sampling steps than standard SDXL | Largest single per-image reduction |
| Parallel input fetching | Inputs downloaded concurrently rather than sequentially | Removes fixed serial overhead per job |
| Pre-built container image | ComfyUI, custom nodes and dependencies baked at build time | Removes runtime setup from every cold start |
| Models on a network volume | Weights attached rather than shipped in the image ([ADR-003](adr/003-models-on-network-volume.md)) | Fast image pulls; swap a model without rebuilding |
| Warm-worker configuration | Amortise init across many requests | Cold-start cost stops being a per-request cost |
| Two-tier resolution | Preview cheap, print full ([ADR-004](adr/004-two-tier-preview-and-print-resolution.md)) | **~40% GPU cost reduction** |
| Pinned, versioned workflow | Known-good image, explicit rollback path | Prevents silent regressions eating the gains |

<!-- FILL: add measured before/after for each row. A table of mechanisms is good; a table of
     mechanisms with numbers is what gets you the offer. -->

## The two-tier decision in detail

Previews were being generated at print resolution (1250×1250). Dropping everything to 1000×1000
roughly halves generation time — but visibly degrades face-swap quality, and resemblance is the
product.

The resolution of the trade-off was to stop treating it as one number:

- **Preview:** reduced resolution. Good enough to sell on a phone screen, materially cheaper.
- **Print:** full resolution, generated **only after payment clears**.

Approximately **40% of GPU spend eliminated**, with zero change to what a paying customer receives.
It only works because the free and paid paths were already separated in the architecture.

The alternative considered and rejected: generate the scene at low resolution, crop the face
region, upscale the crop, swap on the crop, composite back. Fewer GPU-seconds in theory, but it
reintroduces exactly the resize-boundary problem documented in
[debugging-notes.md](debugging-notes.md#3-resizing-mask-assets-degrades-output-even-back-to-the-original-size).
Cheaper and worse is not cheaper.

## Cost model

The number that matters is **GPU cost per shipped book**, which is not GPU cost per image:

```
cost_per_book = (pages_per_book × print_render_cost)
              + (previews_per_conversion × preview_pages × preview_render_cost)
```

The second term is usually larger than the first. Any conversion-rate improvement on the preview
page is simultaneously a GPU cost reduction — which is why
[web performance work](web-performance.md) sits in an infrastructure portfolio and not a marketing
one.

<!-- FILL: GPU tier comparison — VRAM, cost/hour, images/hour, cost/image, and the resulting
     cost per book at your current conversion rate. See benchmarks/. -->

## How this is measured

See [benchmarks/](../benchmarks/) for the harness and the CSV schema. The rule that keeps these
numbers honest: **cold and warm runs are reported separately and never averaged together.** A mean
across both is a number that describes no real request.
