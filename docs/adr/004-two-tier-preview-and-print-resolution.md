# ADR-004: Two-tier resolution - cheap preview, full-resolution print after payment

**Status:** Accepted

## Context

Previews are free and are generated for every visitor who uploads a photo. Roughly 3% of them
convert. Previews were being generated at print resolution (1250×1250), so the large majority of
GPU spend was being burned on images nobody would ever buy.

Generating at 1000×1000 roughly halves generation time - but it visibly degrades face-swap quality,
and resemblance *is* the product. Cheapening the output everyone judges the product by is not a
cost saving.

## Options considered

1. **Everything at print resolution.** Status quo. Simple, and structurally over-spends on the
   free path.
2. **Everything at lower resolution.** Cheapest, and degrades both the preview a customer decides
   on and the book they receive. Rejected.
3. **Two-tier: reduced-resolution preview, full-resolution print rendered only after payment
   clears.**
4. **Crop-and-upscale hybrid:** generate the scene at low resolution, crop the face, upscale the
   crop, swap on the crop, composite back. Fewer GPU-seconds in theory — but it reintroduces the
   resampling-boundary degradation documented in
   [debugging-notes.md](../debugging-notes.md#3-resizing-mask-assets-degrades-output-even-back-to-the-original-size).
   Rejected: cheaper and worse is not cheaper.

## Decision

Two-tier generation. Preview at reduced resolution, print rendered at full resolution after payment
confirmation.

## Reasons

- The preview is viewed on a phone; the print is viewed on 220 GSM paper. They have genuinely
  different quality requirements.
- It aligns cost with revenue: the expensive render happens only for jobs that have been paid for.
- The architecture already separated the synchronous free path from the asynchronous paid path, so
  the change was a configuration and routing decision rather than a redesign.

## Outcomes

**Positive.** Approximately **40% reduction in GPU spend**, with no change to what a paying customer
receives.

**Negative.** Two render configurations to keep in sync — a quality change must be applied and
validated at both tiers. The preview is no longer pixel-identical to the print, so the preview
resolution has to stay high enough that the printed book is never a *downgrade* from what was sold.
That floor is a quality constraint, not a cost knob.

## Revisit when

Conversion rate rises materially (the free-path term shrinks relative to the paid one), or when
per-customer identity-embedding caching lands and changes the cost shape of a full book render.
