#!/usr/bin/env python3
"""Summarise GPU image-generation benchmark runs.

Reads a results CSV (schema documented in README.md) and prints p50/p95 stage timings
per variant, separating cold and warm requests, plus derived cost per image.

    python latency_report.py results.csv
    python latency_report.py results.csv --chart latency.png
"""

from __future__ import annotations

import argparse
import csv
import sys
from collections import defaultdict

STAGES = [
    "worker_start_s",
    "model_load_s",
    "input_fetch_s",
    "generate_s",
    "face_swap_s",
    "restore_s",
    "upload_s",
]


def percentile(values: list[float], pct: float) -> float:
    """Nearest-rank percentile. No numpy dependency on purpose."""
    if not values:
        return 0.0
    ordered = sorted(values)
    rank = max(1, min(len(ordered), round(pct / 100 * len(ordered))))
    return ordered[rank - 1]


def load(path: str) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        sys.exit(f"{path} has no rows")
    return rows


def to_float(row: dict, key: str) -> float:
    try:
        return float(row.get(key) or 0.0)
    except ValueError:
        return 0.0


def summarise(rows: list[dict]) -> dict:
    """Group rows by (variant, cold) and compute stage medians and totals."""
    groups: dict[tuple[str, bool], list[dict]] = defaultdict(list)
    for row in rows:
        groups[(row.get("variant", "unknown"), row.get("cold", "0") == "1")].append(row)

    summary = {}
    for key, group in groups.items():
        totals = [to_float(r, "total_s") for r in group]
        summary[key] = {
            "n": len(group),
            "stages": {s: percentile([to_float(r, s) for r in group], 50) for s in STAGES},
            "p50": percentile(totals, 50),
            "p95": percentile(totals, 95),
            "rate": percentile([to_float(r, "gpu_hourly_rate") for r in group], 50),
        }
    return summary


def print_report(summary: dict) -> None:
    for (variant, cold) in sorted(summary):
        stats = summary[(variant, cold)]
        label = "cold" if cold else "warm"
        print(f"\n{variant}  [{label}]  n={stats['n']}")
        print("-" * 52)
        for stage, value in stats["stages"].items():
            if value:
                share = value / stats["p50"] * 100 if stats["p50"] else 0
                print(f"  {stage:<18} {value:8.2f}s   {share:5.1f}%")
        print(f"  {'p50 total':<18} {stats['p50']:8.2f}s")
        print(f"  {'p95 total':<18} {stats['p95']:8.2f}s")
        if stats["rate"] and stats["p50"]:
            per_hour = 3600 / stats["p50"]
            print(f"  {'images/hour':<18} {per_hour:8.1f}")
            print(f"  {'cost/image':<18} {stats['rate'] / per_hour:8.4f}  (GPU rate units)")


def chart(summary: dict, out_path: str) -> None:
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        sys.exit("matplotlib is required for --chart:  pip install matplotlib")

    labels = [f"{v}\n{'cold' if c else 'warm'}" for (v, c) in sorted(summary)]
    bottoms = [0.0] * len(labels)
    _, axis = plt.subplots(figsize=(1.9 * len(labels) + 3, 5))

    for stage in STAGES:
        values = [summary[k]["stages"][stage] for k in sorted(summary)]
        if not any(values):
            continue
        axis.bar(labels, values, bottom=bottoms, label=stage.replace("_s", ""))
        bottoms = [b + v for b, v in zip(bottoms, values)]

    axis.set_ylabel("seconds (p50)")
    axis.set_title("Per-stage generation latency")
    axis.legend(fontsize=8)
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    print(f"\nchart written to {out_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_path")
    parser.add_argument("--chart", metavar="PNG", help="also write a stacked bar chart")
    args = parser.parse_args()

    summary = summarise(load(args.csv_path))
    print_report(summary)
    if args.chart:
        chart(summary, args.chart)


if __name__ == "__main__":
    main()
