# Production debugging notes

Four real failures from running this pipeline. They are collected here because the interesting part
of each one is the same: the symptom pointed somewhere other than the cause, and the fix was cheap
once the cause was isolated.

---

## 1. The dependency that silently moved inference to CPU

**Symptom.** After a routine rebuild, generation was dramatically slower. No errors. No failed
jobs. GPU utilisation low. Everything "worked."

**Why it was confusing.** A crash is easy. A pipeline that produces correct output slowly, with no
error anywhere, looks like a capacity problem — and capacity problems send you off to look at
worker counts, queue depth and GPU tiers, all of which were fine.

**Cause.** `insightface` pulls `onnxruntime` (the CPU build) as a dependency. Installing it *after*
`onnxruntime-gpu` replaces the GPU runtime in place. ONNX Runtime then falls back to the CPU
execution provider, silently and by design. Face detection and analysis were running on CPU inside
a GPU container.

**Fix.** Reinstall `onnxruntime-gpu` as the **final** pip command in the image build — dependency
order is load-bearing, not cosmetic.

**Prevention.** A startup assertion that fails the container loudly if the CUDA execution provider
is not active:

```python
import onnxruntime as ort
assert "CUDAExecutionProvider" in ort.get_available_providers(), \
    "onnxruntime is CPU-only — check pip install order in the Dockerfile"
```

**Generalisable lesson.** Silent fallbacks are worse than crashes. Any dependency that can quietly
degrade from GPU to CPU needs an explicit assertion at startup, because the failure mode is a
performance bug that looks like a capacity bug.

---

## 2. Choosing build over buy, on evidence

**Question.** Hosted multimodal image APIs are cheaper and dramatically simpler to operate than a
self-managed diffusion stack. Could one replace this pipeline?

**Test.** Identity-preserving face swap evaluated directly against the current pipeline on real
reference photos.

**Result.** Hosted general-purpose image generation could not reliably preserve identity. The
outputs were competent images of a *similar-looking* child. That is an architectural limitation,
not a prompting problem: these models are not conditioned on a face embedding the way
InstantID-style pipelines are, so there is no mechanism by which the specific face is carried
through.

**Decision.** Keep the self-managed pipeline. Re-evaluate when a hosted API exposes explicit
identity conditioning rather than text and reference-image similarity.

**Generalisable lesson.** "Can the managed service do this?" is answered with a test on real inputs
and the actual acceptance criterion — here, *does the child's grandmother recognise them* — not with
a capability table. And the answer has a shelf life; the decision is recorded with the condition
that would reverse it.

---

## 3. Resizing mask assets degrades output — even back to the original size

**Symptom.** Output quality dropped after an asset-pipeline change, with no change to the workflow
graph, the models or the parameters.

**Cause.** Mask and template assets had been passed through a resize step. Crucially, resizing them
*back to their original target dimensions* did **not** restore quality. Resampling shifts edges by
sub-pixel amounts; those shifts then propagate through depth estimation and identity conditioning,
where they compound into visible differences in the final composite.

**Fix.** Original source assets are used unmodified. Any resizing happens in the generation graph
where its effect is controlled, never in asset preparation.

**Generalisable lesson.** In a multi-stage vision pipeline, an operation that is lossless-looking in
isolation is not necessarily neutral in composition. "It's the same dimensions" is not the same
claim as "it's the same pixels."

---

## 4. Model bias appearing as a product defect

**Symptom.** Generated children showed features the source photograph did not have — bindis
hallucinated onto children not wearing one, skin tone systematically darkened relative to the
upload.

**Cause.** The token `indian` in the prompt path. SDXL's text encoder carries strong stereotype
associations for that token, and they override the subtler identity signal.

**Fix.** Remove the token from the prompt entirely and let identity conditioning carry ethnicity
from the actual photograph, with stacked negative weights as a backstop.

**Generalisable lesson.** For a personalisation product, every generic descriptive token in the
prompt competes with the customer's own photograph — and the model's priors will win more often
than you expect. The safest prompt describes the *scene*; the *person* comes from the image. For an
Indian customer base this is not a fairness abstraction, it is a defect rate.

---

## The pattern

In all four cases the debugging method was the same: **find the stage where the behaviour changes,
then bisect the change.** Not "is the GPU slow" but "which stage got slower, and what was the last
thing that touched it." Most of the time saved came from refusing to guess before the stage was
isolated.
