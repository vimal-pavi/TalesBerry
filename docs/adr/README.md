# Architecture decision records

Short records of the decisions that shaped the system: what the problem was, what else was on the
table, what was chosen, and what it cost. Each one names the condition under which it should be
revisited, because a decision without a reversal condition is a belief.

| # | Decision | Status |
|---|---|---|
| [001](001-serverless-gpu-platform.md) | Serverless GPU workers rather than always-on instances | Accepted |
| [002](002-comfyui-over-diffusers.md) | ComfyUI as the inference runtime | Accepted |
| [003](003-models-on-network-volume.md) | Model weights on a network volume, not baked into the image | Accepted |
| [004](004-two-tier-preview-and-print-resolution.md) | Two-tier resolution: cheap preview, full-resolution print after payment | Accepted |
| [005](005-static-prerendering.md) | Static prerendering of marketing routes instead of a framework rewrite | Accepted |
| [006](006-versioned-workflows-and-rollback.md) | Pinned, versioned workflow artefacts with an explicit rollback target | Accepted |
