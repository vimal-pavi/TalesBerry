# Web performance

Nearly all traffic arrives from paid social, on Android phones, inside an in-app browser, on Indian
mobile networks. Under those conditions the front end is not a presentation layer — it is the
narrowest part of the funnel, and every second of load time is money already spent on the click.

## Result

| Metric | Before | After |
|---|---|---|
| Homepage LCP | 9.5s | **2.6s** |
| Lighthouse performance | 72 | **94** |
| Page payload | 26 MB | **< 2 MB** |

## What was wrong

A 26 MB homepage. Full-resolution book-cover artwork — 400 KB to 1.7 MB per image — served
straight from object storage through a CDN that did nothing but cache the original bytes, plus
autoplay video. Every phone downloaded print-grade images to render thumbnails.

## The fix

**One asset, many renditions.** An AWS Serverless Image Handler (Lambda@Edge in front of
CloudFront) resizes and re-encodes on request, with a `getOptimizedImage()` helper in the app that
turns a storage path into an optimised URL. Every `<img>` gets a `srcSet` across breakpoints, a
`sizes` hint, `loading="lazy"` below the fold and `fetchPriority="high"` on the LCP element.

The deliberate choice here is that the app never references a raw asset URL. Optimisation is a
property of *how you ask for an image*, not something someone has to remember to do when adding
one.

**Removing video from the landing path.** Three homepage videos, removed. The LCP contribution was
larger than their conversion contribution.

## Migration discipline

The same work on the personalisation page was partially completed and is documented honestly as
such: the hero image moved to the optimised CDN, but a long tail of thumbnails and a 1.1 MB
guidelines PNG still load from the old distribution, leaving that page at a 13–16s LCP. It is the
highest-value remaining fix in the funnel — the land-to-start rate on that page is the tightest
constraint in the whole conversion path.

Two rules made the migration safe:

1. **Never touch generated content.** AI preview images, user uploads and dynamically constructed
   URLs are explicitly excluded from any bulk image change. Passing a generated preview through a
   resize pipeline degrades the exact output the customer is judging.
2. **Verify by search, not by assertion.** Completion is defined as "a global search for the old
   distribution hostname returns nothing," not as a tool reporting success.

That second rule exists because the site is built in an AI-assisted builder that will report an
edit as applied when it has not been. The working practice that came out of it: treat the git
remote as the source of truth, verify every change against the committed file, and keep refactors
on a branch with a frozen snapshot branch to roll back to.

## SPA → static prerendering

The site began as a client-side React/Vite SPA. Google was indexing an empty shell, and answer
engines — which increasingly drive discovery for a category like this — do not execute JavaScript
at all.

Rather than a full framework migration, the marketing surface was prerendered with
`vite-react-ssg`: **11 India marketing routes** are emitted as real static HTML, while every
interactive route (personalise, preview, cart, checkout, auth, admin) stays client-side where it
belongs.

The work was mostly about making a browser-assuming codebase survive a server render:

- Geo-redirect hooks guarded with `typeof window === 'undefined'` checks.
- A loading-splash gate removed from the app shell — it produced empty prerendered HTML, which is
  the precise failure the migration existed to fix.
- Route components reading region from context rather than `window.location.pathname`.
- The Supabase client made SSR-safe behind an `isBrowser` guard.
- Auth providers verified router-free so they could stay above the router.
- A router-aware root layout and an explicit route manifest extracted from the previous inline tree.

Two traps worth recording, because they cost real time:

- `includedRoutes` must be passed as the **third argument** to `ViteReactSSG` in the entry file. In
  this beta, the `ssgOptions` config route silently does not work.
- The site builder re-injects its own script tag into `index.html`; the durable fix is
  `rollupOptions.external` rather than deleting the tag and watching it come back.

**Verification:** view-source on the prerendered routes must show real content and
`data-server-rendered=true` — not a Lighthouse score, not a framework's claim. Either the HTML has
the words in it or the migration did not work.

## Why this belongs in an AI engineering portfolio

Because it is the same discipline as the GPU work, applied one layer up: find the stage that
dominates, measure it, change the mechanism rather than the symptom, and verify against the real
artefact. And because a faster preview page directly reduces GPU cost per shipped book — see
[performance-and-cost.md](performance-and-cost.md#cost-model).
