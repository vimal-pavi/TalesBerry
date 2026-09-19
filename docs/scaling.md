# Scaling design: what breaks first

A system-design exercise grounded in a system I actually operate, rather than an imaginary one.
The question: **what has to change to go from the current order volume to 100× it?**

The honest starting point is that the current bottleneck is not the GPUs. It is fulfilment — the
operation can handle roughly 15 orders a day, and print and shipping are human-paced. Any scaling
plan that begins with the inference layer is solving the wrong problem first. That said, here is
what the technical layers require, in the order they break.

## 1. Fulfilment and supply chain (breaks first)

Print vendor capacity, QC on physical output, returns, and per-order human touch. Fixing this means
multiple print partners with regional routing, an order state machine with explicit statuses rather
than a spreadsheet, and automated print-file handoff. This is the constraint that actually caps
revenue, and it is a people-and-partners problem before it is a software one.

## 2. Preview generation capacity

Previews scale with **traffic**, not orders, and traffic scales with ad spend. At 100× orders,
preview volume is 100× too — and at a ~3% conversion rate, that is where nearly all the GPU spend
lands.

What changes:

- **Job queue with idempotency keys.** Today's poll-for-completion flow is adequate at current
  concurrency and is not adequate under burst. A duplicate submission must not produce a second
  paid render.
- **Separate pools for preview and print.** Different SLOs, different resolutions, different GPU
  tiers. Preview is latency-sensitive and interruptible; print is throughput-sensitive and must not
  be starved by a traffic spike.
- **Admission control.** Under saturation, degrade honestly: queue with an accurate wait, do not
  silently time out. A timed-out preview is a lost customer *and* wasted GPU seconds.
- **Multi-provider capacity.** One serverless GPU provider is a single point of failure; that has
  already caused an incident at current scale ([report](incidents/2026-runpod-gpu-tier-instability.md)).

## 3. Cost per generated image

At 100× volume, a 20% GPU cost improvement stops being an optimisation and becomes a funding
decision. Levers, roughly in order of remaining value:

- Batching multiple pages of the same book in one worker, amortising model load across pages.
- Caching identity embeddings per customer instead of recomputing per page — the same face is
  processed 20+ times per book today.
- Pre-generating the non-personalised parts of each story template once, rather than per order.
- GPU tier selection driven by measured cost-per-image, not by VRAM headroom intuition.

The first two are the big ones, and both follow from the same observation: **a book is a batch, not
20 unrelated requests.** The current architecture treats it as 20 unrelated requests.

## 4. Storage and delivery

Generated pages accumulate forever, and most belong to previews that never converted. Required:
lifecycle policies that expire unconverted preview assets, cold storage for delivered orders, and
signed URLs with expiry rather than long-lived public paths — see
[security-and-privacy.md](security-and-privacy.md).

## 5. Quality at scale

At 100× volume, a 1% resemblance failure rate is no longer a handful of apologetic refunds. This
needs an automated resemblance regression suite — a fixed panel of consented reference faces, a
similarity score computed on every workflow change, and a release gate on the score. Without it,
every pipeline improvement is a gamble against the thing customers pay for.

## Observability: the honest version

Current instrumentation is adequate for one operator who knows the system, and would not survive
the volume above. During the incident documented in this repo, per-stage timings had to be
reconstructed from logs by inspection. The required end state:

```
API            request latency · error rate · queue depth
GPU            cold-start rate · execution time · VRAM · utilisation · worker lifetime
Pipeline       per-stage timing: fetch · sample · swap · restore · upload
Business       preview→order conversion · GPU cost per shipped book
```

The last line is the one most inference dashboards leave out, and it is the one that decides
whether any of the rest matters.

## Known measurement gap

Analytics session identifiers and order identifiers cannot currently be joined, so funnel
behaviour and order data are analysed separately. It is a real limitation, it is known, and it is
recorded here rather than papered over — at 100× volume it becomes the difference between knowing
which creative drives profit and guessing.
