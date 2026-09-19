# Security and privacy

This system's primary input is **a photograph of someone's child**, uploaded by their parent. That
single fact sets the standard for everything below. A generic "we use environment variables"
security page would be beside the point.

This document describes principles and posture. It deliberately does not describe the live
configuration in enough detail to be useful to an attacker.

## Principles

**1. Minimise what is collected.** The pipeline needs a face. It does not need a full profile of
the child. Fields exist because the book requires them — first name, age, a hairstyle choice — and
nothing is collected "in case it is useful later."

**2. The photograph is input, not an asset.** The uploaded photo is raw material for generation,
not something the business accumulates. Retention is bounded by what fulfilment and re-print
support actually require, and lifecycle rules expire the rest — with unconverted preview uploads
being the largest category and the first to go.

**3. Generated pages are private by default.** Preview URLs are unguessable and expiring rather
than enumerable. This matters more than usual because previews are *designed* to be shared on
WhatsApp — the sharing model has to be "this link, to whoever I send it to," never "anyone can walk
the bucket."

**4. Separate application data from generated assets.** Customer records live in the application
database; generated imagery lives in object storage behind a CDN. Neither system holds the whole
picture, and access to one does not yield the other.

**5. Least privilege on the generation path.** GPU workers receive the inputs for the job they are
running and credentials scoped to writing their output. A compromised ephemeral worker should not
be able to read other customers' uploads.

**6. Nothing sensitive in logs.** Logs carry identifiers and timings, not photographs, not children's
names, not signed URLs. This is the rule most easily broken while debugging — the temptation to log
the full request payload during an incident is exactly when it matters.

**7. Secrets never touch the repository.** All credentials come from environment configuration and
provider secret stores; nothing is committed, including in notebooks, workflow JSON or
screenshots. See [.gitignore](../.gitignore).

## Third-party surface

Every external service that touches customer data is a decision with a privacy cost, not just a
latency and price cost:

| Service class | What it sees | Mitigation |
|---|---|---|
| Serverless GPU provider | Uploaded photo during generation | Ephemeral workers; scoped credentials; no persistence on the worker |
| Object storage / CDN | Generated pages and uploads | Private buckets, signed and expiring URLs, lifecycle expiry |
| Database / auth | Customer records | Row-level access control; no photographs stored in the database |
| Print vendor | Final print files | Contractual; minimum necessary data per order |

## Publishing this repository safely

This repository is documentation. Everything in the list below is deliberately absent from it, and
should stay absent:

- API keys, tokens, connection strings, webhook secrets
- Bucket names, CDN distribution hostnames or IDs, endpoint URLs, registry paths, worker or
  account identifiers
- Customer photographs, generated pages, names, order data, or any identifiable output
- The complete production workflow graph
- Internal business metrics that are not the author's to publish

## What I would do next with more capacity

- Formal data-retention policy with automated enforcement and an audit trail, rather than
  lifecycle rules applied per bucket.
- A documented deletion path a parent can invoke: "delete my child's photograph and everything
  generated from it," honoured across storage, database and backups.
- Periodic credential rotation with scoped, short-lived tokens on the generation path.
- An explicit model-safety review on generated output — the bias issue documented in
  [debugging-notes.md](debugging-notes.md#4-model-bias-appearing-as-a-product-defect) is a privacy-
  adjacent harm, not merely a quality bug, and it deserves a standing check rather than an ad-hoc
  fix.
