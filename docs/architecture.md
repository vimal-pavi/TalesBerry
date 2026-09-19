# System architecture

How a photograph becomes a printed book, and what the system is actually optimising for.

## The shape of the problem

TalesBerry is a two-sided latency problem in a single product.

**The preview must feel instant and it is free.** A parent uploads one photo on a mobile phone,
usually inside the Instagram in-app browser, and decides within a minute whether this is worth
₹1,799. Median time from seeing the preview to paying is about 25 minutes; more than half of buyers
pay within 30 minutes and only ~5% take longer than a day. If they close the tab, they are gone.
So preview latency is a conversion variable, not an engineering nicety.

**The print must be perfect and it is paid for.** 20+ pages, print resolution, a face the child's
grandmother will recognise. The book ships in a few days.

These two jobs have opposite cost profiles, and the architecture exists mostly to keep them apart.
See [ADR-004](adr/004-two-tier-preview-and-print-resolution.md).

## Components

| Layer | Choice | Why |
|---|---|---|
| Web app | React + Vite, static prerendering, served from Cloudflare | Mobile-first, ad traffic, SEO — see [web-performance.md](web-performance.md) |
| Data & auth | Supabase (Postgres) | One service for auth, rows and storage; no backend team to staff |
| Asset delivery | S3 + CloudFront with Lambda@Edge image handler | On-the-fly resize/format so one stored asset serves every breakpoint |
| GPU inference | ComfyUI in a Docker image on RunPod Serverless | Workflow-as-data, scale-to-zero — see [ADR-001](adr/001-serverless-gpu-platform.md), [ADR-002](adr/002-comfyui-over-diffusers.md) |
| Model weights | Network volume attached to the workers, not baked into the image | See [ADR-003](adr/003-models-on-network-volume.md) |
| Fulfilment | Print-ready PDF handed to a print vendor | Physical ops is not a differentiator worth owning at this volume |

## Request flow

**Preview (synchronous from the user's point of view)**

1. Photo upload → object storage, with a short-lived reference stored against the session.
2. The app submits a generation job to the serverless GPU endpoint and polls for completion.
3. A worker — warm if one is available, cold otherwise — runs the pipeline in
   [docs/image-pipeline.md](image-pipeline.md) against the chosen story template.
4. The finished page is written to S3 and served through CloudFront to the preview screen.
5. The preview page is shareable, which matters: a meaningful share of preview views are WhatsApp
   forwards to a spouse or grandparent, so preview URLs must survive being sent to someone else.

**Print (asynchronous, post-payment)**

1. Payment confirmation enqueues the full book at print resolution.
2. Every page is generated, assembled into a print-ready PDF and handed to the print vendor.
3. Failures here are recoverable by re-running a page — nobody is waiting on a screen.

## Sync / async boundary

The only truly synchronous path is preview generation, and it is synchronous only because the
alternative — "we'll WhatsApp you the preview" — kills the in-session urgency the funnel depends
on. Everything downstream of payment is queued.

This is the single most important structural decision in the system: **the free path is the fast
path, and the paid path is the expensive path.** Most naive implementations of this product do the
opposite — full-quality generation for everyone, monetised at 3%.

## Failure modes and how they are handled

| Failure | Blast radius | Handling |
|---|---|---|
| GPU worker cold start | One preview, +tens of seconds | Warm-worker configuration; the UI sets expectations rather than lying about progress |
| GPU tier unavailable / unstable | All previews | Pinned GPU tiers, secondary provider for dev; see [the incident report](incidents/2026-runpod-gpu-tier-instability.md) |
| Silent CPU fallback in a CUDA dependency | All previews, ~10× slower, no error | Startup assertion on the execution provider; see [debugging-notes.md](debugging-notes.md#1-the-dependency-that-silently-moved-inference-to-cpu) |
| Poor resemblance on an individual face | One customer, but it is *the* product failure | Deterministic, pinned workflow version; quality regressions treated as production incidents |
| Print vendor delay | Order-level | Human ops; explicitly not automated at this volume |

## What I would change with a second engineer

- Replace polling with a proper job queue and idempotency keys, so a retried submission cannot
  produce a duplicate paid render.
- Per-stage timing emitted as structured events rather than reconstructed from logs during an
  incident ([scaling.md](scaling.md#observability-the-honest-version)).
- An automated resemblance regression suite: a fixed set of consented reference faces scored on
  every workflow change, so quality regressions are caught before customers find them.
