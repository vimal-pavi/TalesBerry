# ADR-005: Static prerendering of marketing routes instead of a framework rewrite

**Status:** Accepted

## Context

The site is a client-side React/Vite SPA. Search engines were indexing an empty shell, and answer
engines — increasingly the discovery path for "personalised books for kids in India" — do not
execute JavaScript at all. Meanwhile nearly all paid traffic is mobile, where hydration cost is
real.

Only the marketing surface needs to be indexable. Personalisation, preview, cart, checkout, auth
and admin are interactive by nature and gain nothing from prerendering.

## Options considered

1. **Rewrite in Next.js.** The "correct" long-term answer and a multi-week rewrite of a revenue-
   generating site by a one-person team, with the conversion funnel at risk throughout. Rejected on
   risk, not on merit.
2. **Prerendering service (e.g. Prerender.io).** Fast to deploy, serves rendered HTML to bots. A
   recurring cost, a third-party dependency on the indexing path, and it does nothing for real user
   performance — human visitors still get the empty shell first.
3. **Build-time prerendering with `vite-react-ssg`.** Emit real static HTML for selected routes at
   build time, leave everything else client-side.

## Decision

Build-time prerendering of **11 India marketing routes**; interactive routes stay client-side.

## Reasons

- Solves the actual problem — real HTML for crawlers *and* for humans — without a rewrite.
- Scoped to the routes that need it, so the risk is bounded to the marketing surface.
- No recurring third-party cost on the discovery path.
- Falls out of the existing Vite build; no new hosting model.

## Consequences

**Positive.** Static HTML with real content on the routes that drive discovery, and a faster first
paint for mobile ad traffic.

**Negative.** SSR-safety becomes a permanent constraint on shared code: anything touching `window`
needs a guard, and a browser-only assumption added later will break the build (see
[web-performance.md](../web-performance.md#spa--static-prerendering)). The library is on a beta
version, and one of its options only works when passed in the correct position — a sharp edge that
had to be learned. Dynamic routes are not prerendered yet.

## Revisit when

Dynamic content routes need indexing at scale, or the app outgrows the constraint — at which point
the Next.js migration is the right call, made from a position of working SEO rather than under
pressure.
