# Benchmarks

A small harness for measuring where the seconds go in GPU image generation, and for turning those
measurements into the numbers used in [performance-and-cost.md](../docs/performance-and-cost.md).

## Rules that keep the numbers honest

1. **Cold and warm runs are reported separately.** An average across both describes no real
   request. Cold-start cost is per *worker*; generation cost is per *image*.
2. **Per-stage, not just total.** A total latency number tells you the system is slow. Stage
   timings tell you which change is worth making.
3. **Same inputs across runs.** A fixed set of reference photos, or the comparison measures the
   photos rather than the pipeline.
4. **Report p50 and p95, not the mean.** Customers experience the tail.
5. **Cost, not just time.** `cost_per_image = gpu_hourly_rate / images_per_hour`. Time is a proxy;
   money is the metric.

## Schema

`results.csv`, one row per generated image:

| column | meaning |
|---|---|
| `run_id` | identifier for a batch of runs |
| `variant` | what is being compared, e.g. `baseline`, `lightning-6step`, `preview-tier` |
| `gpu` | GPU model, e.g. `RTX 4090` |
| `cold` | `1` if this request paid worker-start cost, else `0` |
| `worker_start_s` | container + runtime init (cold only) |
| `model_load_s` | weights into VRAM (cold only) |
| `input_fetch_s` | fetching source photo and assets |
| `generate_s` | diffusion sampling + VAE decode |
| `face_swap_s` | swap refinement |
| `restore_s` | face restoration |
| `upload_s` | writing the finished page out |
| `total_s` | wall clock for the request |
| `resolution` | e.g. `1250x1250` |
| `gpu_hourly_rate` | provider rate, in your billing currency |

`sample_results.csv` in this directory shows the shape with illustrative values — **replace it with
real measurements before publishing.**

## Usage

```bash
python latency_report.py results.csv              # table: p50/p95 per stage, per variant
python latency_report.py results.csv --chart out.png   # stacked bar chart (needs matplotlib)
```
